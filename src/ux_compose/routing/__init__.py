"""Product page-unit routing (filesystem → HTTP).

Owned here because this is Next-style file routing, not render.

    from ux_compose.routing import DirectoryRoutes, RouterHooks, DirectoryASGI
    from ux_compose.routing.host import open, bind

Leftover standalone FastAPI trees that cannot import compose still use
``ux_dom.routing.fastapi.DirectoryRouter`` (labeled leftover). Product
apps use ``ux_compose.build`` / ``App.mount``.
"""
from __future__ import annotations

import warnings

from ux_compose.routing.core import (
    AcceptSymbol,
    DirectoryRoutes,
    DirectoryRoutesError,
    OnRoute,
    ResolveUnit,
    RouteRecord,
    RouterHooks,
    http_path,
    is_json_payload,
    is_stream_payload,
    apply_html_document,
    module_exports,
    pick_page_type,
)
from ux_compose.routing.asgi import DirectoryASGI, match_record

__all__ = [
    "DirectoryRoutes",
    "DirectoryRoutesError",
    "DirectoryRouterError",
    "RouterHooks",
    "RouteRecord",
    "ResolveUnit",
    "AcceptSymbol",
    "OnRoute",
    "DirectoryASGI",
    "match_record",
    "module_exports",
    "pick_page_type",
    "http_path",
    "is_json_payload",
    "is_stream_payload",
    "apply_html_document",
    "materialize",
    "mount",
]


def __getattr__(name: str):
    if name == "DirectoryRouterError":
        warnings.warn(
            "DirectoryRouterError is deprecated; use DirectoryRoutesError. "
            "The alias shipped in 0.1.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return DirectoryRoutesError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def materialize(*args, **kwargs):
    from ux_compose.routing.fastapi import materialize as _m

    return _m(*args, **kwargs)


def mount(*args, **kwargs):
    from ux_compose.routing.fastapi import mount as _m

    return _m(*args, **kwargs)
