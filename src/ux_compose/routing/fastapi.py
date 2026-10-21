"""Product FastAPI host — Clock A (page GET).

The only compose module that imports FastAPI. Authors never import this;
maintainers open it to answer "what happens on GET /hello?".

Page units have no HTTP verbs. This file:
  resolve_unit → render() → payload dispatch → response

Media type is the payload, not Accept:
  tree / str / bytes → apply_html_document(wrap) → HTMLResponse
    (str / bytes are untrusted: ux-dom sanitize_html; Markup is trusted)
  dict / list-of-dicts → returned as-is (FastAPI JSON-encodes)
  async/sync generator → sanitize_html_stream → StreamingResponse
    (a stream that fails before its first piece is a 500)
  Response subclass (JSONResponse, StreamingResponse, FileResponse, …) → pass through

JSON author routes stay JSON: this module does **not** set FastAPI's
default_response_class. Streaming is a return value, not a route_class.
"""
from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Optional

from ux_compose.routing.core import (
    DirectoryRoutes,
    apply_html_document,
    is_json_payload,
    is_stream_payload,
    open_html_stream,
    sanitize_stream_payload,
)

logger = logging.getLogger("ux_compose.routing.fastapi")

__all__ = ["create", "bind", "page_endpoint"]


def create(name: str = "App", *, openapi: bool = False) -> Any:
    """FastAPI process. Fail closed if FastAPI is missing.

    No default_response_class — page GET wraps HTML explicitly so
    author JSON routes (``@app.get("/api/...")``) stay JSON.

    OpenAPI / Swagger is off by default so ``routes/docs.py`` can own
    GET ``/docs``. Opt in with ``openapi=True`` (``build(openapi=True)``
    or ``settings.OPENAPI = True``).
    """
    from fastapi import FastAPI

    if openapi:
        return FastAPI(title=name)
    return FastAPI(
        title=name,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )


def _live_instance(rec, resolve_unit: Optional[Callable], path_params: dict) -> Any:
    inst = None
    if resolve_unit is not None and rec.page_cls is not None:
        inst = resolve_unit(rec.page_cls, rec.path, rec.name)
    if inst is None and rec.page_cls is not None:
        inst = rec.page_cls()
    return inst


def _call_render(inst: Any, path_params: dict) -> Any:
    render = getattr(inst, "render", None) or getattr(inst, "__render__", None)
    if not callable(render):
        return inst
    if path_params:
        try:
            return render(**path_params)
        except TypeError:
            pass
    return render()


def _as_html_response(tree: Any) -> Any:
    if _is_response(tree):
        return tree
    from ux_dom.response.starlette import HTMLResponse

    return HTMLResponse(tree)


def _as_stream_response(payload: Any) -> Any:
    from starlette.responses import StreamingResponse
    from ux_dom.response.starlette import StreamingResponse as DomStreamingResponse

    try:
        return DomStreamingResponse(payload)
    except TypeError:
        # ux-dom's StreamingResponse rejects sync generators; Starlette accepts them.
        return StreamingResponse(payload, media_type="text/html; charset=utf-8")


def _as_http_response(payload: Any, *, document: Any = None) -> Any:
    """Payload type picks media type. Same spirit as ux-dom html_response.

    A page GET opens streams with :func:`_open_stream_response` instead, so
    a stream that fails before its first piece is a 500.
    """
    if _is_response(payload) or is_json_payload(payload):
        return payload
    if is_stream_payload(payload):
        return _as_stream_response(sanitize_stream_payload(payload))
    tree = apply_html_document(document, payload)
    return _as_html_response(tree)


async def _open_stream_response(payload: Any) -> Any:
    """Sanitized stream response, or a logged 500 if it fails before byte one."""
    from starlette.responses import PlainTextResponse

    try:
        stream = await open_html_stream(payload)
    except Exception:
        logger.exception("page stream failed before its first byte")
        return PlainTextResponse("Internal Server Error", status_code=500)
    return _as_stream_response(stream)


def page_endpoint(
    rec,
    *,
    document: Any = None,
    resolve_unit: Optional[Callable] = None,
    partial: Optional[Callable[[Any], bool]] = None,
) -> Callable:
    """Closed-signature GET. Path params come from the Request, not Component."""

    async def endpoint(request: Any = None):
        path_params: dict[str, Any] = {}
        if request is not None:
            path_params = dict(getattr(request, "path_params", {}) or {})
        if rec.kind == "explicit" and rec.handler is not None:
            handler = rec.handler
            try:
                tree = handler(**path_params) if path_params else handler()
            except TypeError:
                tree = handler()
        else:
            inst = _live_instance(rec, resolve_unit, path_params)
            if inst is None:
                return _as_html_response("")
            tree = _call_render(inst, path_params)
        if inspect.isawaitable(tree):
            tree = await tree
        if is_stream_payload(tree):
            return await _open_stream_response(tree)
        if partial is None or _is_response(tree) or is_json_payload(tree):
            return _as_http_response(tree, document=document)
        fragment = request is not None and partial(request)
        response = _as_http_response(tree, document=None if fragment else document)
        # Fragment or full page by HX-Request: caches must key on it.
        response.headers.append("Vary", "HX-Request")
        return response

    # from __future__ import annotations stringifies types. FastAPI must see
    # the Request class object or it treats `request` as a body field (422).
    from starlette.requests import Request

    endpoint.__annotations__["request"] = Request
    endpoint.__name__ = rec.name.replace(".", "_")
    endpoint.__doc__ = getattr(rec.page_cls, "__doc__", None)
    return endpoint


def _is_response(obj: Any) -> bool:
    if obj is None:
        return False
    name = type(obj).__name__
    if name in {
        "Response",
        "HTMLResponse",
        "JSONResponse",
        "StreamingResponse",
        "PlainTextResponse",
        "FileResponse",
        "RedirectResponse",
        "UJSONResponse",
        "ORJSONResponse",
    }:
        return True
    if hasattr(obj, "children") or hasattr(obj, "__render__"):
        return False
    if not hasattr(obj, "status_code"):
        return False
    return any(
        hasattr(obj, attr)
        for attr in ("body", "body_iterator", "content", "path", "headers")
    )


def bind(
    asgi: Any,
    core: DirectoryRoutes,
    *,
    document: Any = None,
    resolve_unit: Optional[Callable] = None,
    prefix: str = "",
    partial: Optional[Callable[[Any], bool]] = None,
) -> Any:
    """Include page routes on a FastAPI/Starlette app. Document wrap is here."""
    from fastapi import APIRouter

    if not core.records:
        core.discover()
    router = APIRouter()
    for rec in core.records:
        router.add_api_route(
            rec.path,
            page_endpoint(
                rec, document=document, resolve_unit=resolve_unit, partial=partial
            ),
            methods=[rec.method.upper()],
            name=rec.name,
        )
    if not hasattr(asgi, "include_router"):
        raise TypeError("asgi_app must support include_router (FastAPI/Starlette)")
    asgi.include_router(router, prefix=prefix)
    return router
