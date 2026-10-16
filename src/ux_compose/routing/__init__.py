"""Product page-unit routing (filesystem → HTTP).

Owned here because this is Next-style file routing, not render.

    from ux_compose.routing import DirectoryRoutes, RouterHooks, DirectoryASGI
    from ux_compose.routing.host import open, bind

Product apps use ``ux_compose.build`` / ``App.mount``; page routes attach
through one verb, ``ux_compose.routing.host.bind``.
"""
from __future__ import annotations

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
]
