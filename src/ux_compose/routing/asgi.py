"""Pure ASGI adapter — DirectoryRoutes without FastAPI/Starlette.

Degrade path (host="asgi"), not a peer product. Clock A still holds:
resolve → render → payload dispatch. HTML goes through apply_html_document.
CSP middleware is FastAPI-only; doctor reports that when Document.mount
cannot attach.
"""
from __future__ import annotations

import inspect
import logging
import re
from typing import Any, Callable, Optional
from urllib.parse import unquote

from ux_compose.routing.core import (
    DirectoryRoutes,
    DirectoryRoutesError,
    RouteRecord,
    RouterHooks,
    _html_chunk_bytes,
    apply_html_document,
    is_json_payload,
    is_stream_payload,
    _non_identifier_param,
)

logger = logging.getLogger("ux_compose.routing.asgi")

__all__ = ["DirectoryASGI", "match_record"]


def _compile_path(path: str) -> tuple[re.Pattern[str], list[str]]:
    bad = _non_identifier_param(path)
    if bad is not None:
        raise DirectoryRoutesError(
            f"path parameter {bad!r} is not a Python identifier"
        )
    names: list[str] = []
    parts = []
    for seg in path.strip("/").split("/"):
        if not seg:
            continue
        if seg.startswith("{") and seg.endswith("}"):
            name = seg[1:-1]
            names.append(name)
            parts.append(rf"(?P<{name}>[^/]+)")
        else:
            parts.append(re.escape(seg))
    if not parts:
        return re.compile(r"^/?$"), names
    return re.compile(r"^/" + "/".join(parts) + r"/?$"), names


def match_record(
    records: list[RouteRecord],
    method: str,
    path: str,
) -> Optional[tuple[RouteRecord, dict[str, str]]]:
    method_u = method.upper()
    path = unquote(path or "/")
    if not path.startswith("/"):
        path = "/" + path
    for rec in records:
        if rec.method.upper() != method_u and not (
            method_u == "HEAD" and rec.method.upper() == "GET"
        ):
            continue
        if rec.path == path or rec.path.rstrip("/") == path.rstrip("/"):
            return rec, {}
        if "{" in rec.path:
            try:
                rx, _names = _compile_path(rec.path)
            except DirectoryRoutesError:
                continue
            m = rx.match(path)
            if m:
                return rec, {k: unquote(v) for k, v in m.groupdict().items()}
    return None


def _invoke(rec: RouteRecord, hooks: RouterHooks, path_params: dict) -> Any:
    resolve = hooks.resolve_unit if hooks else None
    if rec.kind == "explicit" and rec.handler is not None:
        handler = rec.handler
        try:
            return handler(**path_params) if path_params else handler()
        except TypeError:
            return handler()
    page_cls = rec.page_cls
    if page_cls is None:
        return None
    inst = None
    if resolve is not None:
        inst = resolve(page_cls, rec.path, rec.name)
    if inst is None:
        inst = page_cls()
    render = getattr(inst, "render", None) or getattr(inst, "__render__", None)
    if callable(render):
        try:
            return render(**path_params) if path_params else render()
        except TypeError:
            return render()
    return inst


def _body_bytes(result: Any) -> bytes:
    try:
        from ux_dom.response.serialize import to_html_bytes

        return to_html_bytes(result)
    except Exception:
        if result is None:
            return b""
        if isinstance(result, (bytes, bytearray)):
            return bytes(result)
        return str(result).encode("utf-8")


def _encode(result: Any) -> tuple[bytes, bytes]:
    """Return (body, content-type). Payload type picks media type."""
    if is_json_payload(result):
        import json

        return json.dumps(result).encode("utf-8"), b"application/json"
    return _body_bytes(result), b"text/html; charset=utf-8"


def _chunk_bytes(chunk: Any) -> bytes:
    return _html_chunk_bytes(chunk)


async def _send_stream(send: Callable, iterable: Any, *, content_type: bytes) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", content_type)],
        }
    )
    try:
        if hasattr(iterable, "__aiter__"):
            async for chunk in iterable:
                data = _chunk_bytes(chunk)
                if data:
                    await send(
                        {"type": "http.response.body", "body": data, "more_body": True}
                    )
        else:
            for chunk in iterable:
                data = _chunk_bytes(chunk)
                if data:
                    await send(
                        {"type": "http.response.body", "body": data, "more_body": True}
                    )
    except Exception:
        logger.exception("DirectoryASGI stream failed")
        await send({"type": "http.response.body", "body": b"", "more_body": False})
        return
    await send({"type": "http.response.body", "body": b"", "more_body": False})


class DirectoryASGI:
    """Pure ASGI application over :class:`DirectoryRoutes`.

    No FastAPI / Starlette imports. Uses ux-dom ``to_html_bytes`` when
    present; otherwise stringifies the render result.
    """

    def __init__(self, core: DirectoryRoutes, *, document: Any = None) -> None:
        if not core.records:
            core.discover()
        self.core = core
        self.hooks = core.hooks or RouterHooks()
        self.document = document
        self._records = list(core.records)
        for rec in self._records:
            if "{" in (rec.path or ""):
                _compile_path(rec.path)

    @property
    def route_table(self) -> list:
        return self.core.route_table()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b"", "more_body": False})
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "/") or "/"
        hit = match_record(self._records, method, path)
        if hit is None:
            body = b"Not Found"
            payload = b"" if str(method).upper() == "HEAD" else body
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [
                        (b"content-type", b"text/plain; charset=utf-8"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": payload, "more_body": False}
            )
            return

        rec, params = hit
        try:
            result = _invoke(rec, self.hooks, params)
            if inspect.isawaitable(result):
                result = await result
            if is_stream_payload(result):
                if str(method).upper() == "HEAD":
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 200,
                            "headers": [
                                (b"content-type", b"text/html; charset=utf-8"),
                            ],
                        }
                    )
                    await send(
                        {"type": "http.response.body", "body": b"", "more_body": False}
                    )
                    return
                await _send_stream(
                    send, result, content_type=b"text/html; charset=utf-8"
                )
                return
            if not is_json_payload(result):
                result = apply_html_document(self.document, result)
            body, content_type = _encode(result)
            status = 200
        except Exception:
            logger.exception("DirectoryASGI request failed")
            body = b"Internal Server Error"
            content_type = b"text/plain; charset=utf-8"
            status = 500

        outbound = b"" if str(method).upper() == "HEAD" else body
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", content_type),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": outbound, "more_body": False})
