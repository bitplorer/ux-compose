"""Product HTTP pipeline — order of the process.

Authors never import this. Maintainers always do.

    asgi, kind = open(name=..., host=..., asgi_app=...)
    asgi = bind(asgi=asgi, kind=kind, core=..., document=..., resolve_unit=...)

open() creates the process. bind() wires Document (CSP/static) then pages.
Channel is attached by build() *before* bind(), once the ASGI object exists.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from ux_compose.routing.core import DirectoryRoutes

__all__ = ["open", "bind", "KIND_FASTAPI", "KIND_ASGI"]

KIND_FASTAPI = "fastapi"
KIND_ASGI = "asgi"


class ProductBatteriesRejected(RuntimeError):
    """Raised when a caller asks for leftover DirectoryRouter batteries."""


_BATTERIES_TEACH = (
    "host='batteries' is leftover ux-dom DirectoryRouter, not the product path. "
    "Use host='fastapi' | 'asgi' | 'auto' (ux_compose.routing.DirectoryRoutes). "
    "Scaffold: uxcompose create-app / ux_compose.build(host=)."
)


def open(*, name: str = "App", host: str = "auto", asgi_app: Any = None) -> tuple[Any, str]:
    """Return (asgi_or_none, kind) where kind is fastapi | asgi.

    host:
      auto     — FastAPI if importable, else DirectoryASGI
      fastapi  — fail closed if FastAPI missing
      asgi     — DirectoryASGI (no Starlette)
    """
    want = (host or "auto").lower().strip()
    if want in ("batteries", "directory_router"):
        raise ProductBatteriesRejected(_BATTERIES_TEACH)
    if want == "starlette":
        want = "auto"  # Starlette is FastAPI's runtime, not a product host

    if asgi_app is not None:
        if hasattr(asgi_app, "include_router"):
            return asgi_app, KIND_FASTAPI
        return asgi_app, KIND_ASGI

    if want in ("auto", "fastapi"):
        try:
            from ux_compose.routing.fastapi import create

            return create(name), KIND_FASTAPI
        except ImportError:
            if want == "fastapi":
                raise ImportError(
                    "host='fastapi' requires fastapi. pip install fastapi"
                )
    return None, KIND_ASGI


def bind(
    *,
    asgi: Any,
    kind: str,
    core: DirectoryRoutes,
    document: Any = None,
    resolve_unit: Optional[Callable] = None,
    mounted: Optional[list] = None,
) -> Any:
    """Attach Document runtimes + page routes. Returns the ASGI app.

    FastAPI: document.mount (CSP, SafeStatic) then page routes.
    DirectoryASGI: document() wrap on the body; CSP middleware is FastAPI-only.
    """
    if not core.records:
        core.discover()

    if kind == KIND_FASTAPI:
        if document is not None and hasattr(document, "mount") and hasattr(asgi, "add_middleware"):
            document.mount(asgi)
            if mounted is not None:
                mounted.append("document")
        from ux_compose.routing import fastapi as http

        http.bind(asgi, core, document=document, resolve_unit=resolve_unit)
        return asgi

    from ux_compose.routing.asgi import DirectoryASGI

    if isinstance(asgi, DirectoryASGI):
        if document is not None and getattr(asgi, "document", None) is None:
            asgi.document = document
        return asgi
    return DirectoryASGI(core, document=document)
