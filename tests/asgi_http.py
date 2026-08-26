"""ASGI HTTP helper for Clock A tests. No Starlette TestClient / httpx."""
from __future__ import annotations

import asyncio
import json
from typing import Any


def asgi_http(app: Any, path: str, *, method: str = "GET") -> tuple[int, dict[str, str], bytes]:
    """One HTTP request against any ASGI app. Returns (status, headers, body)."""
    status = {"code": 0, "headers": {}}
    chunks: list[bytes] = []

    received = {"http": False}
    finished = asyncio.Event()

    async def receive():
        if not received["http"]:
            received["http"] = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.wait_for(finished.wait(), timeout=5)
        return {"type": "http.disconnect"}

    async def send(msg):
        if msg["type"] == "http.response.start":
            status["code"] = int(msg.get("status") or 0)
            hdrs: dict[str, str] = {}
            for key, val in msg.get("headers") or []:
                k = key.decode("latin-1") if isinstance(key, (bytes, bytearray)) else str(key)
                v = val.decode("latin-1") if isinstance(val, (bytes, bytearray)) else str(val)
                hdrs[k.lower()] = v
            status["headers"] = hdrs
        elif msg["type"] == "http.response.body":
            chunks.append(bytes(msg.get("body") or b""))
            if not msg.get("more_body", False):
                finished.set()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [(b"host", b"test")],
        "server": ("test", 80),
        "client": ("test", 123),
        "root_path": "",
    }
    asyncio.run(app(scope, receive, send))
    return status["code"], status["headers"], b"".join(chunks)


class AsgiResponse:
    def __init__(self, status_code: int, headers: dict[str, str], body: bytes):
        self.status_code = status_code
        self.headers = headers
        self.content = body
        self.text = body.decode("utf-8", "replace")

    def json(self):
        return json.loads(self.text)


def asgi_get(app: Any, path: str) -> AsgiResponse:
    code, headers, body = asgi_http(app, path, method="GET")
    return AsgiResponse(code, headers, body)
