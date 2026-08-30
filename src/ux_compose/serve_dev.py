"""What ``uxcompose serve dev`` starts.

Four roles, one public URL (the browser never talks to the workers):

    public process     this module          no reload   host:port
    pages worker       routes + CSS + HMR   reload *.py  never *.css
    channel worker     /ux-channel*         no reload
    css watcher        Tailwind --watch=always writes output.css

The app file stays ``app:asgi``. Both workers import it. This process
only forwards: Channel paths to the channel worker, everything else to
the pages worker. That is why a pages reload does not wipe Channel RAM.

Not a FastAPI sub-app mount. One uvicorn still dies as one process.

httpx is the HTTP client for that forward (browser → public → worker).
Starlette is the public ASGI app. websockets forwards HMR and Channel
sockets. None of these run in ``serve prod`` or deploy.
"""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import threading
import time
from typing import Callable, Literal
from urllib.parse import urlsplit

Worker = Literal["pages", "channel"]

CHANNEL_PATH_PREFIX = "/ux-channel"
PAGES_URL_ENV = "UXCOMPOSE_PAGES_URL"
CHANNEL_URL_ENV = "UXCOMPOSE_CHANNEL_URL"

RELOAD_INCLUDES = ["*.py"]
RELOAD_EXCLUDES = ["*.css", "assets/*", "**/assets/*"]


def owner_for(path: str) -> Worker:
    """Which worker answers this URL path."""
    raw = path or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    if raw == CHANNEL_PATH_PREFIX or raw.startswith(CHANNEL_PATH_PREFIX + "/"):
        return "channel"
    return "pages"


def _url_from_env(name: str) -> str:
    raw = os.environ.get(name)
    if not raw:
        raise RuntimeError(f"{name} is unset — start workers through serve_dev.run")
    return raw.rstrip("/")


def make_public_asgi(*, pages_url: str | None = None, channel_url: str | None = None):
    """ASGI the browser hits. Reads worker URLs from the environment."""
    import httpx
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.routing import Route, WebSocketRoute
    from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

    def pages() -> str:
        return pages_url or _url_from_env(PAGES_URL_ENV)

    def channel() -> str:
        return channel_url or _url_from_env(CHANNEL_URL_ENV)

    hop = {
        "host",
        "content-length",
        "content-encoding",
        "transfer-encoding",
        "connection",
        "keep-alive",
    }

    def worker_base(path: str) -> str:
        return channel() if owner_for(path) == "channel" else pages()

    async def forward_http(request):
        path = request.url.path
        url = worker_base(path) + path
        if request.url.query:
            url += "?" + request.url.query
        headers = {k: v for k, v in request.headers.items() if k.lower() not in hop}
        body = await request.body()
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            r = await client.request(request.method, url, headers=headers, content=body)
        out = {k: v for k, v in r.headers.items() if k.lower() not in hop}
        return Response(content=r.content, status_code=r.status_code, headers=out)

    async def forward_ws(ws: WebSocket):
        await ws.accept()
        path = ws.url.path
        parts = urlsplit(worker_base(path))
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

                async def client_to_worker():
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

                async def worker_to_client():
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

                await asyncio.gather(client_to_worker(), worker_to_client())
        except Exception:
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.close(code=1011)

    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    return Starlette(
        routes=[
            WebSocketRoute("/", forward_ws),
            WebSocketRoute("/{path:path}", forward_ws),
            Route("/", forward_http, methods=methods),
            Route("/{path:path}", forward_http, methods=methods),
        ]
    )


def public_asgi():
    """uvicorn --factory target for the public process."""
    return make_public_asgi()


def _spawn(
    cmd: list[str],
    *,
    cwd: str,
    extra_env: dict[str, str] | None = None,
    pass_fds: tuple[int, ...] = (),
) -> subprocess.Popen:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    print("serve-dev:", " ".join(cmd), flush=True)
    return subprocess.Popen(cmd, cwd=cwd, env=env, pass_fds=pass_fds, close_fds=True)


def _stop(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def listen_loopback() -> socket.socket:
    """Bind and listen on 127.0.0.1:0. Keep the socket — do not close it.

    uvicorn ``--fd`` inherits this listener. The port is owned from this
    bind until the worker process exits. No probe-and-close gap.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(2048)
    sock.set_inheritable(True)
    return sock


def _watch_workers(pages: subprocess.Popen, channel: subprocess.Popen) -> None:
    """If a worker dies after bind, stop the public process too."""
    while True:
        time.sleep(0.4)
        if pages.poll() is not None or channel.poll() is not None:
            print(
                "serve-dev: a worker exited — stopping the public process",
                file=sys.stderr,
            )
            os.kill(os.getpid(), signal.SIGTERM)
            return


def run(
    *,
    app_ref: str,
    host: str,
    port: int,
    reload_dirs: list[str],
    cwd: str | None = None,
    start_css_watcher: Callable[[], subprocess.Popen | None] | None = None,
) -> int:
    """Start the css watcher + both workers, then block on the public process."""
    import uvicorn

    root = cwd or os.getcwd()
    pages_sock = listen_loopback()
    channel_sock = listen_loopback()
    pages_port = int(pages_sock.getsockname()[1])
    channel_port = int(channel_sock.getsockname()[1])
    pages_url = f"http://127.0.0.1:{pages_port}"
    channel_url = f"http://127.0.0.1:{channel_port}"

    os.environ[PAGES_URL_ENV] = pages_url
    os.environ[CHANNEL_URL_ENV] = channel_url
    os.environ["UXCOMPOSE_APP"] = app_ref

    py = sys.executable
    css_watcher = start_css_watcher() if start_css_watcher is not None else None

    channel_cmd = [
        py, "-m", "uvicorn", app_ref,
        "--fd", str(channel_sock.fileno()),
    ]
    pages_cmd = [
        py, "-m", "uvicorn", "ux_compose.hmr:asgi_factory",
        "--factory",
        "--fd", str(pages_sock.fileno()),
        "--reload",
        "--reload-include", "*.py",
        "--reload-exclude", "*.css",
        "--reload-exclude", "assets/*",
    ]
    for directory in reload_dirs:
        pages_cmd.extend(["--reload-dir", directory])

    channel_proc = pages_proc = None
    try:
        channel_proc = _spawn(
            channel_cmd, cwd=root, pass_fds=(channel_sock.fileno(),)
        )
        pages_proc = _spawn(
            pages_cmd,
            cwd=root,
            extra_env={"UXCOMPOSE_APP": app_ref},
            pass_fds=(pages_sock.fileno(),),
        )
        pages_sock.close()
        channel_sock.close()
        deadline = time.time() + 12
        while time.time() < deadline:
            if channel_proc.poll() is not None:
                print(f"serve-dev: channel worker exited {channel_proc.returncode}", file=sys.stderr)
                return 1
            if pages_proc.poll() is not None:
                print(f"serve-dev: pages worker exited {pages_proc.returncode}", file=sys.stderr)
                return 1
            if _port_open(pages_port) and _port_open(channel_port):
                break
            time.sleep(0.15)
        else:
            print("serve-dev: workers did not bind in time", file=sys.stderr)
            return 1
        print(
            f"serve-dev: public http://{host}:{port}  "
            f"pages {pages_url} (reload *.py)  "
            f"channel {channel_url} (stable)"
        )
        try:
            import watchfiles  # noqa: F401
        except ImportError:
            print(
                "serve-dev: install watchfiles so CSS writes do not reload pages "
                "(pip install watchfiles)",
                file=sys.stderr,
            )
        threading.Thread(
            target=_watch_workers,
            args=(pages_proc, channel_proc),
            name="serve-dev-workers",
            daemon=True,
        ).start()
        uvicorn.run(
            "ux_compose.serve_dev:public_asgi",
            host=host,
            port=port,
            factory=True,
            reload=False,
        )
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        _stop(pages_proc)
        _stop(channel_proc)
        _stop(css_watcher)
