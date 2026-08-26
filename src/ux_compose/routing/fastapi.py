"""Product FastAPI host — Clock A (page GET).

The only compose module that imports FastAPI. Authors never import this;
maintainers open it to answer "what happens on GET /hello?".

Page units have no HTTP verbs. This file:
  resolve_unit → render() → payload dispatch → response

Media type is the payload, not Accept:
  tree / str / bytes → apply_html_document(wrap) → HTMLResponse
  dict / list-of-dicts → returned as-is (FastAPI JSON-encodes)
  async/sync generator → StreamingResponse
  Response subclass (JSONResponse, StreamingResponse, FileResponse, …) → pass through

JSON author routes stay JSON: this module does **not** set FastAPI's
default_response_class. Streaming is a return value, not a route_class.
"""
from __future__ import annotations

import inspect
from typing import Any, Callable, Optional

from ux_compose.routing.core import (
    DirectoryRoutes,
    RouterHooks,
    apply_html_document,
    is_json_payload,
    is_stream_payload,
)
from ux_compose.routing.host import ProductBatteriesRejected

__all__ = ["create", "bind", "page_endpoint", "materialize", "mount"]


def create(name: str = "App") -> Any:
    """FastAPI process. Fail closed if FastAPI is missing.

    No default_response_class — page GET wraps HTML explicitly so
    author JSON routes (``@app.get("/api/...")``) stay JSON.
    """
    from fastapi import FastAPI

    return FastAPI(title=name)


def _live_instance(rec, resolve_unit: Optional[Callable], path_params: dict) -> Any:
    inst = None
    if resolve_unit is not None and rec.page_cls is not None:
        try:
            inst = resolve_unit(rec.page_cls, rec.path, rec.name)
        except Exception:
            inst = None
    if inst is None and rec.page_cls is not None:
        try:
            inst = rec.page_cls()
        except Exception:
            inst = None
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
    try:
        from ux_dom.response.starlette import HTMLResponse

        return HTMLResponse(tree)
    except ImportError:
        from starlette.responses import HTMLResponse as StarletteHTML

        if tree is None:
            body = ""
        elif isinstance(tree, (bytes, bytearray)):
            return StarletteHTML(content=bytes(tree))
        else:
            body = tree if isinstance(tree, str) else str(tree)
        return StarletteHTML(content=body)


def _as_stream_response(payload: Any) -> Any:
    try:
        from ux_dom.response.starlette import StreamingResponse

        return StreamingResponse(payload)
    except ImportError:
        pass
    except TypeError:
        # ux-dom stream prepare rejects sync generators — Starlette accepts them.
        pass
    from starlette.responses import StreamingResponse as StarletteStream

    return StarletteStream(payload, media_type="text/html; charset=utf-8")


def _as_http_response(payload: Any, *, document: Any = None) -> Any:
    """Payload type picks media type. Same spirit as ux-dom html_response."""
    if _is_response(payload) or is_json_payload(payload):
        return payload
    if is_stream_payload(payload):
        return _as_stream_response(payload)
    tree = apply_html_document(document, payload)
    return _as_html_response(tree)


def page_endpoint(
    rec,
    *,
    document: Any = None,
    resolve_unit: Optional[Callable] = None,
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
        return _as_http_response(tree, document=document)

    # from __future__ import annotations stringifies types. FastAPI must see
    # the Request class object or it treats `request` as a body field (422).
    try:
        from starlette.requests import Request

        endpoint.__annotations__["request"] = Request
    except ImportError:
        pass
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
) -> Any:
    """Include page routes on a FastAPI/Starlette app. Document wrap is here."""
    from fastapi import APIRouter

    if not core.records:
        core.discover()
    router = APIRouter()
    for rec in core.records:
        router.add_api_route(
            rec.path,
            page_endpoint(rec, document=document, resolve_unit=resolve_unit),
            methods=[rec.method.upper()],
            name=rec.name,
        )
    if not hasattr(asgi, "include_router"):
        raise TypeError("asgi_app must support include_router (FastAPI/Starlette)")
    asgi.include_router(router, prefix=prefix)
    return router


def materialize(
    core: DirectoryRoutes,
    *,
    router: Any = None,
    route_class: Any = None,
    document: Any = None,
    resolve_unit: Optional[Callable] = None,
) -> Any:
    """Compat: build an APIRouter from DirectoryRoutes (tests / leftover callers)."""
    from fastapi import APIRouter

    if router is None:
        router = APIRouter()
    if route_class is not None:
        raise ProductBatteriesRejected(
            "route_class= is leftover StreamingRoute. Streaming is a "
            "return value from render(), not a route class. See docs/reference/host.md."
        )
    if not core.records:
        core.discover()
    hooks = core.hooks or RouterHooks()
    resolve = resolve_unit or hooks.resolve_unit
    for rec in core.records:
        router.add_api_route(
            rec.path,
            page_endpoint(rec, document=document, resolve_unit=resolve),
            name=rec.name,
            methods=[rec.method.upper()],
            description=getattr(rec.page_cls, "__doc__", None),
        )
    return router


def mount(
    core: DirectoryRoutes,
    asgi_app: Any,
    *,
    prefix: str = "",
    route_class: Any = None,
    document: Any = None,
    resolve_unit: Optional[Callable] = None,
) -> Any:
    """Compat: discover + include_router."""
    if route_class is not None:
        raise ProductBatteriesRejected(
            "route_class= is leftover StreamingRoute. Streaming is a "
            "return value from render(), not a route class. See docs/reference/host.md."
        )
    hooks = core.hooks or RouterHooks()
    resolve = resolve_unit or hooks.resolve_unit
    return bind(
        asgi_app,
        core,
        document=document,
        resolve_unit=resolve,
        prefix=prefix,
    )
