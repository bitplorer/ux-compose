"""Dev stack — three OS processes, one public origin.

    A  glue (this module)   no --reload     public host:port
    X  pages + CSS + HMR    --reload *.py   never watches *.css / assets
    Y  Channel              no --reload     /ux-channel only

A is a reverse proxy, not FastAPI.mount. Mounting X and Y under one
uvicorn is still one process — Channel would die with the pages worker.

The user app stays ``app:asgi``. Both X and Y import it. A sends
page/HMR/CSS traffic to X and Channel traffic to Y so session RAM on Y
survives an X reload.

CSS writes never hit a reloader. The browser (HMR client) HEADs
``/css/output.css`` and swaps the sheet.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Callable
from urllib.parse import urlsplit

CHANNEL_PREFIXES = ("/ux-channel",)
X_ENV = "UXCOMPOSE_X_ORIGIN"
Y_ENV = "UXCOMPOSE_Y_ORIGIN"

RELOAD_INCLUDES = ["*.py"]
RELOAD_EXCLUDES = ["*.css", "assets/*", "**/assets/*"]


def backend_for(path: str) -> str:
    """Which process owns this URL path. ``Y`` or ``X``."""
    raw = path or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    for prefix in CHANNEL_PREFIXES:
        if raw == prefix or raw.startswith(prefix + "/"):
            return "Y"
    return "X"


def _origin(env_name: str, default: str) -> str:
    return os.environ.get(env_name, default).rstrip("/")


def make_glue(*, x_origin: str | None = None, y_origin: str | None = None):
    """Build the A proxy. Origins are read from env on every request."""
    import httpx
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.routing import Route, WebSocketRoute
    from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

    def x_base() -> str:
        return x_origin or _origin(X_ENV, "http://127.0.0.1:8081")

    def y_base() -> str:
        return y_origin or _origin(Y_ENV, "http://127.0.0.1:8082")

    hop = {
        "host",
        "content-length",
        "content-encoding",
        "transfer-encoding",
        "connection",
        "keep-alive",
    }

    async def http_proxy(request):
        path = request.url.path
        base = y_base() if backend_for(path) == "Y" else x_base()
        url = base + path
        if request.url.query:
            url += "?" + request.url.query
        headers = {k: v for k, v in request.headers.items() if k.lower() not in hop}
        body = await request.body()
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            r = await client.request(request.method, url, headers=headers, content=body)
        out = {k: v for k, v in r.headers.items() if k.lower() not in hop}
        return Response(content=r.content, status_code=r.status_code, headers=out)

    async def ws_proxy(ws: WebSocket):
        await ws.accept()
        path = ws.url.path
        base = y_base() if backend_for(path) == "Y" else x_base()
        parts = urlsplit(base)
        scheme = "wss" if parts.scheme == "https" else "ws"
        dest = f"{scheme}://{parts.netloc}{path}"
        if ws.url.query:
            dest += "?" + ws.url.query
        try:
            import websockets
        except ImportError:
            await ws.close(code=1011)
            return
        extra = []
        cookie = ws.headers.get("cookie")
        origin = ws.headers.get("origin")
        if cookie:
            extra.append(("Cookie", cookie))
        if origin:
            extra.append(("Origin", origin))
        try:
            async with websockets.connect(dest, additional_headers=extra) as up:

                async def c2s():
                    try:
                        while True:
                            msg = await ws.receive()
                            if msg["type"] == "websocket.disconnect":
                                break
                            if msg.get("text") is not None:
                                await up.send(msg["text"])
                            elif msg.get("bytes") is not None:
                                await up.send(msg["bytes"])
                    except WebSocketDisconnect:
                        pass

                async def s2c():
                    try:
                        async for raw in up:
                            if ws.client_state != WebSocketState.CONNECTED:
                                break
                            if isinstance(raw, bytes):
                                await ws.send_bytes(raw)
                            else:
                                await ws.send_text(str(raw))
                    except Exception:
                        pass

                import asyncio

                await asyncio.gather(c2s(), s2c())
        except Exception:
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.close(code=1011)

    return Starlette(
        routes=[
            WebSocketRoute("/", ws_proxy),
            WebSocketRoute("/{path:path}", ws_proxy),
            Route("/", http_proxy, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]),
            Route("/{path:path}", http_proxy, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]),
        ]
    )


def glue_factory():
    """uvicorn --factory target for A."""
    return make_glue()


def _popen(cmd: list[str], *, cwd: str, extra_env: dict[str, str] | None = None) -> subprocess.Popen:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    print("devstack:", " ".join(cmd), flush=True)
    return subprocess.Popen(cmd, cwd=cwd, env=env)


def _stop(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()


def run_dev_stack(
    *,
    app_ref: str,
    host: str,
    port: int,
    reload_dirs: list[str],
    cwd: str | None = None,
    start_tailwind: Callable[[], subprocess.Popen | None] | None = None,
) -> int:
    """Block: Tailwind + Y + X + A. A is the public origin."""
    import uvicorn

    root = cwd or os.getcwd()
    x_port = port + 1
    y_port = port + 2
    x_origin = f"http://127.0.0.1:{x_port}"
    y_origin = f"http://127.0.0.1:{y_port}"

    os.environ[X_ENV] = x_origin
    os.environ[Y_ENV] = y_origin
    os.environ["UXCOMPOSE_APP"] = app_ref

    py = sys.executable
    css = start_tailwind() if start_tailwind is not None else None

    y_cmd = [
        py, "-m", "uvicorn", app_ref,
        "--host", "127.0.0.1", "--port", str(y_port),
    ]
    x_cmd = [
        py, "-m", "uvicorn", "ux_compose.hmr:asgi_factory",
        "--factory",
        "--host", "127.0.0.1", "--port", str(x_port),
        "--reload",
        "--reload-include", "*.py",
        "--reload-exclude", "*.css",
        "--reload-exclude", "assets/*",
    ]
    for d in reload_dirs:
        x_cmd.extend(["--reload-dir", d])

    y_proc = x_proc = None
    try:
        y_proc = _popen(y_cmd, cwd=root)
        x_proc = _popen(x_cmd, cwd=root, extra_env={"UXCOMPOSE_APP": app_ref})
        deadline = time.time() + 8
        while time.time() < deadline:
            if y_proc.poll() is not None:
                print(f"devstack: Y exited {y_proc.returncode}", file=sys.stderr)
                return 1
            if x_proc.poll() is not None:
                print(f"devstack: X exited {x_proc.returncode}", file=sys.stderr)
                return 1
            time.sleep(0.15)
        print(
            f"devstack: A public http://{host}:{port}  "
            f"X pages {x_origin} (reload *.py)  Y channel {y_origin} (stable)"
        )
        uvicorn.run(
            "ux_compose.devstack:glue_factory",
            host=host,
            port=port,
            factory=True,
            reload=False,
        )
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        _stop(x_proc)
        _stop(y_proc)
        _stop(css)
