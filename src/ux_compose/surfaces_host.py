"""Host bind for page routes — boundary only.

Prefers ux-dom pure core + route adapter; falls back to DirectoryRouter
(FastAPI batteries: StreamingRoute, [id], …). Compose domain stays free of
FastAPI imports except via this door.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("ux_compose.surfaces_host")


def attach_page_router(
    *,
    asgi_app: Any,
    package_dir: str | Path,
    base_directory: str,
    unit_registry: dict,
    fail_closed: bool = True,
) -> Optional[list]:
    """Attach filesystem page routes to ``asgi_app``. Returns route_table or None."""

    def _resolve_unit(cls, path, name):
        sid = str(getattr(cls, "id", None) or cls.__name__.lower())
        return unit_registry.get(sid)

    # 1) Pure core + adapter (no APIRouter subclass as SSoT)
    try:
        from ux_dom.routing.core import DirectoryRoutes, RouterHooks
        from ux_dom.routing.adapters.fastapi import mount as mount_routes

        hooks = RouterHooks(resolve_unit=_resolve_unit)
        core = DirectoryRoutes(
            Path(package_dir).resolve(),
            base_directory=base_directory,
            hooks=hooks,
            fail_closed=fail_closed,
        )
        core.discover()
        if core.records and hasattr(asgi_app, "include_router"):
            mount_routes(core, asgi_app)
            table = core.route_table()
            if table:
                return table
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("core route adapter failed (%s); trying DirectoryRouter", exc)

    # 2) FastAPI batteries (full path-cleaning / StreamingRoute)
    try:
        from ux_dom.routing.fastapi import DirectoryRouter, StreamingRoute, RouterHooks

        hooks = RouterHooks(resolve_unit=_resolve_unit)
        router = DirectoryRouter(
            base_directory=base_directory,
            package_dir=Path(package_dir).resolve(),
            route_class=StreamingRoute,
            hooks=hooks,
            fail_closed=fail_closed,
        )
        if hasattr(asgi_app, "include_router"):
            asgi_app.include_router(router)
        table = getattr(router, "route_table", None)
        if callable(table):
            live = list(table())
            if live:
                return live
        if isinstance(table, list) and table:
            return list(table)
        return []
    except ImportError:
        if fail_closed:
            raise
        logger.warning("DirectoryRouter not available; page gate skipped")
        return None
