"""Host bind for page routes — boundary only.

Authors never see this module. Host choice happens via::

    app.use_host("fastapi")          # or "auto"
    app.mount(..., asgi_app=api)

Preferred path: ``ux_compose.routing.host.open/bind``.
Leftover ``DirectoryRouter`` (ux-dom batteries) is not a product path.

``wrap=`` is the author HTML shell. ``document=`` is mounted (CSP/static).
Same split as ``build()``. A synthesized Document never wraps GET.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("ux_compose.surfaces_host")


from ux_compose.routing.host import ProductBatteriesRejected, _BATTERIES_TEACH


def attach_page_router(
    *,
    asgi_app: Any,
    package_dir: str | Path,
    base_directory: str,
    unit_registry: dict,
    fail_closed: bool = True,
    host: str = "auto",
    document: Any = None,
    wrap: Any = None,
) -> Optional[list]:
    """Attach filesystem page routes to ``asgi_app``. Returns route_table or None.

    host:
      - "auto" / "fastapi" / "asgi" → DirectoryRoutes + host.bind
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
            "unknown host %r — use auto|fastapi|asgi" % host
        )

    from ux_compose.routing.core import DirectoryRoutes, RouterHooks
    from ux_compose.routing.host import bind as host_bind, open as host_open

    hooks = RouterHooks(resolve_unit=_resolve_unit)
    core = DirectoryRoutes(
        Path(package_dir).resolve(),
        base_directory=base_directory,
        hooks=hooks,
        fail_closed=fail_closed,
    )
    core.discover()
    if not core.records:
        return []

    asgi, kind = host_open(name="App", host=host, asgi_app=asgi_app)
    host_bind(
        asgi=asgi,
        kind=kind,
        core=core,
        document=document,
        wrap=wrap,
        resolve_unit=_resolve_unit,
    )
    return core.route_table()
