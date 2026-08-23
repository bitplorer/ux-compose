"""Dev HMR process for ux-compose (delivery layer — not Document.use).

* Watches package / routes paths
* WebSocket at ``/__uxcompose/hmr`` broadcasts reload
* Client stub JS for HTML pages in dev

Attach via ``attach_hmr(asgi_app, watch_paths=...)`` before serve,
or let ``uxcompose serve --hmr`` do it when the ASGI object is loadable.
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence

HMR_PATH = "/__uxcompose/hmr"

CLIENT_JS = """\
(function () {
  if (window.__UXCOMPOSE_HMR__) return;
  window.__UXCOMPOSE_HMR__ = true;
  var path = %s;
  var proto = location.protocol === "https:" ? "wss" : "ws";
  var url = proto + "://" + location.host + path;
  var delay = 500;
  function connect() {
    var ws;
    try { ws = new WebSocket(url); } catch (e) { setTimeout(connect, delay); return; }
    ws.onmessage = function (ev) {
      try {
        var msg = JSON.parse(ev.data || "{}");
        if (msg && (msg.type === "reload" || msg.op === "reload")) {
          location.reload();
        }
      } catch (e) { location.reload(); }
    };
    ws.onclose = function () { setTimeout(connect, Math.min(delay * 1.5, 4000)); };
    ws.onerror = function () { try { ws.close(); } catch (e) {} };
  }
  connect();
})();
""" % json.dumps(HMR_PATH)


def client_script_tag() -> str:
    """Inline script tag for optional manual injection in dev shells."""
    return f"<script data-uxcompose-hmr>\n{CLIENT_JS}\n</script>"


def _iter_files(roots: Sequence[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        r = root.resolve()
        if not r.exists():
            continue
        if r.is_file():
            out.append(r)
            continue
        for p in r.rglob("*"):
            if not p.is_file():
                continue
            if any(part.startswith(".") or part in {"__pycache__", "node_modules", ".venv", "venv"} for part in p.parts):
                continue
            if p.suffix in {".py", ".html", ".css", ".js", ".md", ".json", ".toml"}:
                out.append(p)
    return out


def _snapshot(paths: Sequence[Path]) -> dict[str, float]:
    snap: dict[str, float] = {}
    for p in _iter_files(paths):
        try:
            snap[str(p)] = p.stat().st_mtime
        except OSError:
            pass
    return snap


class HmrHub:
    """In-process broadcast hub for HMR websocket clients."""

    def __init__(self) -> None:
        self._clients: set[Any] = set()
        self._lock = threading.Lock()

    def add(self, ws: Any) -> None:
        with self._lock:
            self._clients.add(ws)

    def discard(self, ws: Any) -> None:
        with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, payload: dict) -> None:
        data = json.dumps(payload)
        dead: list[Any] = []
        with self._lock:
            clients = list(self._clients)
        for ws in clients:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.discard(ws)

    def broadcast_threadsafe(self, loop: asyncio.AbstractEventLoop, payload: dict) -> None:
        try:
            asyncio.run_coroutine_threadsafe(self.broadcast(payload), loop)
        except Exception:
            pass


def start_watcher(
    watch_paths: Sequence[Path],
    on_change: Callable[[], None],
    *,
    interval: float = 0.4,
    stop_event: Optional[threading.Event] = None,
) -> threading.Thread:
    stop = stop_event or threading.Event()
    roots = [Path(p) for p in watch_paths]

    def _run() -> None:
        prev = _snapshot(roots)
        while not stop.is_set():
            time.sleep(interval)
            cur = _snapshot(roots)
            if cur != prev:
                prev = cur
                try:
                    on_change()
                except Exception:
                    pass

    t = threading.Thread(target=_run, name="uxcompose-hmr-watch", daemon=True)
    t.start()
    return t


def attach_hmr(
    asgi_app: Any,
    *,
    watch_paths: Optional[Iterable[str | Path]] = None,
    path: str = HMR_PATH,
) -> Any:
    """Attach WebSocket HMR route + background watcher to a Starlette/FastAPI app.

    Returns the same ``asgi_app``. No-op if the app cannot register routes.
    """
    roots = [Path(p) for p in (watch_paths or [".", "routes"])]
    hub = HmrHub()
    loop_holder: dict[str, Any] = {"loop": None}

    def _notify() -> None:
        loop = loop_holder.get("loop")
        if loop is None:
            return
        hub.broadcast_threadsafe(loop, {"type": "reload", "op": "reload"})

    # Capture running loop on first request if possible via middleware
    try:
        from starlette.websockets import WebSocket

        async def hmr_endpoint(websocket: WebSocket) -> None:
            await websocket.accept()
            try:
                loop_holder["loop"] = asyncio.get_running_loop()
            except RuntimeError:
                pass
            hub.add(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except Exception:
                pass
            finally:
                hub.discard(websocket)

        # FastAPI / Starlette
        if hasattr(asgi_app, "add_websocket_route"):
            asgi_app.add_websocket_route(path, hmr_endpoint, name="uxcompose_hmr")
        elif hasattr(asgi_app, "websocket"):
            # FastAPI decorator style already used; prefer add_api_websocket_route
            if hasattr(asgi_app, "add_api_websocket_route"):
                asgi_app.add_api_websocket_route(path, hmr_endpoint, name="uxcompose_hmr")
            else:
                return asgi_app
        else:
            return asgi_app

        start_watcher(roots, _notify)
        # Stash for debugging / tests
        try:
            setattr(asgi_app, "state", getattr(asgi_app, "state", type("S", (), {})()))
            asgi_app.state.uxcompose_hmr = hub  # type: ignore[attr-defined]
        except Exception:
            pass
    except ImportError:
        return asgi_app

    return asgi_app


__all__ = [
    "HMR_PATH",
    "CLIENT_JS",
    "client_script_tag",
    "HmrHub",
    "start_watcher",
    "attach_hmr",
]
