"""Host bind for page routes — boundary only (Invisible Strategy).

Authors never see this module or any adapter type.
Host choice happens via::

    app.use_host("fastapi")          # or "auto"
    app.mount(..., asgi_app=api)

Preferred path is always pure ux-dom core + thin adapter.
DirectoryRouter is never the primary path for compose users.
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
    host: str = "auto",
) -> Optional[list]:
    """Attach filesystem page routes to ``asgi_app``. Returns route_table or None.

    host:
      - "auto" / "fastapi" / "starlette" / "asgi" → pure core + thin adapter (preferred)
      - "batteries" → DirectoryRouter convenience path (explicit last-resort only)
    """

    def _resolve_unit(cls, path, name):
        sid = str(getattr(cls, "id", None) or cls.__name__.lower())
        return unit_registry.get(sid)

    host = (host or "auto").lower().strip()

    # ------------------------------------------------------------------
    # Preferred path for all normal compose usage (Invisible Strategy)
    # ------------------------------------------------------------------
    if host in ("auto", "fastapi", "starlette", "asgi"):
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
            return []
        except ImportError:
            if fail_closed:
                raise
            logger.warning("ux-dom core/adapter unavailable; page gate skipped")
            return None
        except Exception as exc:
            logger.warning("core + thin adapter failed (%s)", exc)
            if fail_closed:
                raise

    # ------------------------------------------------------------------
    # Explicit last-resort only (never the default for compose)
    # ------------------------------------------------------------------
    if host in ("batteries", "directory_router"):
        try:
            from ux_dom.routing.fastapi import DirectoryRouter, StreamingRoute, RouterHooks

            logger.info("using DirectoryRouter convenience path (host=%s)", host)
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
                return live if live else []
            if isinstance(table, list) and table:
                return list(table)
            return []
        except ImportError:
            if fail_closed:
                raise
            logger.warning("DirectoryRouter not available; page gate skipped")
            return None

    return None
