"""ASGI HTTP helper for Clock A tests. No Starlette TestClient / httpx."""
from __future__ import annotations

import asyncio
import json
from typing import Any


def asgi_http(
    app: Any,
    path: str,
    *,
    method: str = "GET",
    body: bytes = b"",
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    """One HTTP request against any ASGI app. Returns (status, headers, body)."""
    status = {"code": 0, "headers": {}}
    chunks: list[bytes] = []

    received = {"http": False}
    finished = asyncio.Event()
    payload = body or b""

    async def receive():
        if not received["http"]:
            received["http"] = True
            return {"type": "http.request", "body": payload, "more_body": False}
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

    hdrs: list[tuple[bytes, bytes]] = [(b"host", b"test")]
    for key, val in (headers or {}).items():
        hdrs.append((str(key).lower().encode("latin-1"), str(val).encode("latin-1")))
    if payload and not any(k == b"content-length" for k, _ in hdrs):
        hdrs.append((b"content-length", str(len(payload)).encode("ascii")))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": hdrs,
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


def asgi_post_json(
    app: Any,
    path: str,
    payload: dict,
    *,
    headers: dict[str, str] | None = None,
) -> AsgiResponse:
    """POST JSON Intent. Sends ``X-Channel: 1`` (Cap Host CSRF header)."""
    hdrs = {
        "content-type": "application/json",
        "x-channel": "1",
    }
    if headers:
        hdrs.update(headers)
    raw = json.dumps(payload).encode("utf-8")
    code, out_headers, body = asgi_http(
        app, path, method="POST", body=raw, headers=hdrs
    )
    return AsgiResponse(code, out_headers, body)
