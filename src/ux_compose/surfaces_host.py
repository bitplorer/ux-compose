"""Host bind for page routes — boundary only (Invisible Strategy).

Authors never see this module or any adapter type.
Host choice happens via::

    app.use_host("fastapi")          # or "auto"
    app.mount(..., asgi_app=api)

Preferred path is always ``ux_compose.routing.DirectoryRoutes`` + thin adapter.
Leftover ``DirectoryRouter`` (ux-dom batteries) is not a product path.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("ux_compose.surfaces_host")


class ProductBatteriesRejected(RuntimeError):
    """Raised when a caller asks for leftover DirectoryRouter batteries."""


_BATTERIES_TEACH = (
    "host='batteries' is leftover ux-dom DirectoryRouter, not the product path. "
    "Use host='fastapi' | 'asgi' | 'auto' (ux_compose.routing.DirectoryRoutes). "
    "Scaffold: uxcompose create-app / ux_compose.build(host=)."
)


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
      - "auto" / "fastapi" / "starlette" / "asgi" → DirectoryRoutes + thin adapter
      - "batteries" / "directory_router" → fail-closed (leftover, not product)
    """

    def _resolve_unit(cls, path, name):
        sid = str(getattr(cls, "id", None) or cls.__name__.lower())
        return unit_registry.get(sid)

    host = (host or "auto").lower().strip()

    if host in ("batteries", "directory_router"):
        raise ProductBatteriesRejected(_BATTERIES_TEACH)

    if host not in ("auto", "fastapi", "starlette", "asgi"):
        raise ValueError(
            "unknown host %r — use auto|fastapi|starlette|asgi" % host
        )

    from ux_compose.routing.core import DirectoryRoutes, RouterHooks
    from ux_compose.routing.adapters.fastapi import mount as mount_routes

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
