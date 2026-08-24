"""Product page-unit routing (filesystem → HTTP).

Owned here because this is Next-style file routing, not render.

    from ux_compose.routing import DirectoryRoutes, RouterHooks
    from ux_compose.routing.adapters.fastapi import mount
    from ux_compose.routing.adapters.asgi import DirectoryASGI

Leftover standalone FastAPI trees that cannot import compose still use
``ux_dom.routing.fastapi.DirectoryRouter`` (labeled leftover). Product
apps use ``App.mount`` / ``ux_compose.build``.
"""
from __future__ import annotations

from ux_compose.routing.core import (
    AcceptSymbol,
    DirectoryRouterError,
    DirectoryRoutes,
    DirectoryRoutesError,
    OnRoute,
    ResolveUnit,
    RouteRecord,
    RouterHooks,
    module_exports,
    pick_page_type,
)
from ux_compose.routing.adapters.asgi import DirectoryASGI, match_record

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
    "materialize",
    "mount",
]


def materialize(*args, **kwargs):
    from ux_compose.routing.adapters.fastapi import materialize as _m

    return _m(*args, **kwargs)


def mount(*args, **kwargs):
    from ux_compose.routing.adapters.fastapi import mount as _m

    return _m(*args, **kwargs)
