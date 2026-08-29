"""Dev HMR (delivery layer — not Document.use).

Two clocks, both on:

  process reload   uvicorn --reload on ``*.py``
                   new worker, cold import, new page class

  browser HMR      this module
                   WebSocket at ``/__uxcompose/hmr``
                   reconnect after worker death → health → location.reload()
                   HTML inject of the client (dev middleware)

A page unit is a Python class in the worker. This is live reload, not
module-graph swap. This module does not watch files.
"""
from __future__ import annotations

import importlib
import os
from typing import Any, Callable

HMR_PATH = "/__uxcompose/hmr"
HMR_ATTR = b"data-uxcompose-hmr"
BODY_CLOSE = b"</body>"
APP_ENV = "UXCOMPOSE_APP"

# First open is silent. Unclean close (worker died) reconnects, waits until
# this URL is 200, then reloads. close(1000) on beforeunload is a user
# navigation — do not bounce.
CLIENT_JS = r"""
(function () {
  if (window.__UXCOMPOSE_HMR__) return;
  window.__UXCOMPOSE_HMR__ = true;
  function wsUrl() {
    var u = new URL("__uxcompose/hmr", location.href);
    u.protocol = location.protocol === "https:" ? "wss:" : "ws:";
    return u.toString();
  }
  function waitAlive(done) {
    var n = 0;
    var tick = function () {
      fetch(location.href, { cache: "no-store", credentials: "same-origin" })
        .then(function (r) {
          if (r.ok) done();
          else retry();
        })
        .catch(retry);
    };
    var retry = function () {
      n += 1;
      if (n > 80) return;
      setTimeout(tick, 100);
    };
    tick();
  }
  var current;
  function connect(isReconnect) {
    var ws;
    try { ws = new WebSocket(wsUrl()); }
    catch (e) {
      setTimeout(function () { connect(true); }, 400);
      return;
    }
    current = ws;
    ws.onopen = function () {
      if (isReconnect) {
        waitAlive(function () { location.reload(); });
      }
    };
    ws.onclose = function (ev) {
      if (ev.code === 1000) return;
      setTimeout(function () { connect(true); }, 400);
    };
    ws.onerror = function () {
      try { ws.close(); } catch (e) {}
    };
  }
  window.addEventListener("beforeunload", function () {
    try { if (current) current.close(1000); } catch (e) {}
  });
  connect(false);
})();
"""


def client_script_tag() -> str:
    return f'<script {HMR_ATTR.decode("ascii")}>\n{CLIENT_JS}\n</script>'


def is_html_content_type(value: bytes) -> bool:
    return b"text/html" in value.lower()


def inject_html(body: bytes, script_html: bytes) -> bytes:
    """Insert the client once, before the last </body>. Pure. Idempotent."""
    if HMR_ATTR in body:
        return body
    idx = body.lower().rfind(BODY_CLOSE)
    if idx < 0:
        return body
    return body[:idx] + script_html + body[idx:]


def load_asgi_ref(app_ref: str) -> Any:
    if ":" not in app_ref:
        raise ValueError(f"ASGI path must be module:attr, got {app_ref!r}")
    mod_name, attr = app_ref.split(":", 1)
    obj: Any = importlib.import_module(mod_name)
    for part in attr.split("."):
        obj = getattr(obj, part)
    return obj


def asgi_factory() -> Any:
    """uvicorn factory: attach on every worker so --reload remounts the WS."""
    spec = os.environ.get(APP_ENV, "app:asgi")
    return attach_hmr(load_asgi_ref(spec))


def _has_route(asgi_app: Any, path: str) -> bool:
    router = getattr(asgi_app, "router", asgi_app)
    for route in getattr(router, "routes", []) or []:
        if getattr(route, "path", None) == path:
            return True
    return False


def _patch_ws_annotation(endpoint: Callable) -> None:
    annotations = dict(getattr(endpoint, "__annotations__", {}) or {})
    try:
        from fastapi import WebSocket as Ws
    except ImportError:
        try:
            from starlette.websockets import WebSocket as Ws
        except ImportError:
            return
    annotations["websocket"] = Ws
    endpoint.__annotations__ = annotations


def bind_hmr_socket(asgi_app: Any, *, path: str = HMR_PATH) -> bool:
    if _has_route(asgi_app, path):
        return True

    async def hmr_endpoint(websocket: Any) -> None:
        await websocket.accept()
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            return

    _patch_ws_annotation(hmr_endpoint)

    if hasattr(asgi_app, "add_api_websocket_route"):
        asgi_app.add_api_websocket_route(path, hmr_endpoint, name="uxcompose_hmr")
        return True
    if hasattr(asgi_app, "add_websocket_route"):
        asgi_app.add_websocket_route(path, hmr_endpoint, name="uxcompose_hmr")
        return True
    if hasattr(asgi_app, "websocket"):
        asgi_app.websocket(path)(hmr_endpoint)
        return True
    return False


class HmrInjectMiddleware:
    """Dev HTML inject. Seat is serve, not Document.use."""

    def __init__(self, app: Any, script_html: str) -> None:
        self.app = app
        self.script = script_html.encode("utf-8")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = {"html": False}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = []
                html = False
                for key, value in message.get("headers", []):
                    if key.lower() == b"content-length":
                        continue
                    if key.lower() == b"content-type" and is_html_content_type(value):
                        html = True
                    headers.append((key, value))
                state["html"] = html
                message = {**message, "headers": headers}
            elif message["type"] == "http.response.body" and state["html"]:
                body = message.get("body", b"")
                message = {**message, "body": inject_html(body, self.script)}
            await send(message)

        await self.app(scope, receive, send_wrapper)


def attach_hmr(asgi_app: Any, *, path: str = HMR_PATH) -> Any:
    """Mount browser HMR. No file watcher. uvicorn --reload owns ``*.py``."""
    bind_hmr_socket(asgi_app, path=path)
    return HmrInjectMiddleware(asgi_app, client_script_tag())


__all__ = [
    "APP_ENV",
    "HMR_PATH",
    "CLIENT_JS",
    "client_script_tag",
    "inject_html",
    "load_asgi_ref",
    "asgi_factory",
    "attach_hmr",
]
