"""Composition root — one place to set host + live plane.

::

    from ux_compose.build import build

    app, asgi, bundle = build(
        Path(__file__).parent,
        name="Shop",
        host="auto",   # auto|fastapi|asgi
        live="auto",   # auto|channel|null
        level="auto",
    )
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

__all__ = ["build", "BuildResult"]


class BuildResult(tuple):
    """(compose_app, asgi_app, bundle) with named attributes."""

    @property
    def app(self):
        return self[0]

    @property
    def asgi(self):
        return self[1]

    @property
    def bundle(self):
        return self[2]


def build(
    package_dir: str | Path,
    *,
    name: str = "App",
    host: str = "auto",
    live: str = "auto",
    level: int | str = "auto",
    base: str = "routes",
    fail_closed: bool = True,
    use_htmx: bool = False,
    asgi_app: Any = None,
) -> BuildResult:
    """Boot specialists + mount page units. Host and live set only here.

    host:
      - ``"auto"`` — FastAPI if importable, else pure ASGI
      - ``"fastapi"`` — FastAPI + route adapter / DirectoryRouter batteries
      - ``"asgi"`` — DirectoryASGI (no FastAPI)

    live:
      - ``"auto"`` — Channel when ux_channel importable
      - ``"channel"`` — prefer Channel
      - ``"null"`` — offline Behavior only
    """
    from ux_compose import App

    package_dir = Path(package_dir).resolve()
    host_l = (host or "auto").lower()
    live_l = (live or "auto").lower()

    want_channel = live_l in ("auto", "channel")
    if live_l == "null":
        want_channel = False

    asgi = asgi_app
    host_kind = host_l
    if host_l == "auto":
        if asgi is not None:
            host_kind = "fastapi" if hasattr(asgi, "include_router") else "asgi"
        else:
            try:
                from fastapi import FastAPI  # noqa: F401

                host_kind = "fastapi"
            except ImportError:
                host_kind = "asgi"

    if host_kind == "fastapi" and asgi is None:
        try:
            from fastapi import FastAPI

            asgi = FastAPI(title=name)
        except ImportError as e:
            if host_l == "fastapi":
                raise ImportError(
                    "host='fastapi' requires fastapi. pip install fastapi"
                ) from e
            host_kind = "asgi"
            asgi = None

    app = App.boot(name, strict_caps=False, level=level)

    try:
        from ux_dom import Document
        from ux_dom.runtime import XElement, Csp

        runtimes: list[Any] = [XElement(), Csp.auto()]
        if use_htmx:
            try:
                from ux_dom.runtime import Htmx

                runtimes.insert(1, Htmx())
            except ImportError:
                pass
        app.use_dom(Document(head=[], body=[], ensure_csrf_token=False).use(*runtimes))
    except ImportError:
        pass

    if want_channel:
        try:
            if asgi is not None and host_kind == "fastapi":
                app.use_channel(asgi_app=asgi)
            else:
                app.use_channel()
        except Exception:
            if live_l == "channel":
                raise
    try:
        app.use_motion()
    except Exception:
        pass

    if host_kind == "asgi":
        bundle = app.mount(
            package_dir,
            asgi_app=None,
            base=base,
            fail_closed=fail_closed,
            include_directory_router=False,
        )
        try:
            from ux_dom.routing.core import DirectoryRoutes, RouterHooks
            from ux_dom.routing.adapters.asgi import DirectoryASGI

            registry = dict(getattr(bundle, "unit_registry", {}) or {})

            def _resolve(cls, path, name):
                sid = str(getattr(cls, "id", None) or cls.__name__.lower())
                return registry.get(sid)

            core = DirectoryRoutes(
                package_dir,
                base_directory=base,
                hooks=RouterHooks(resolve_unit=_resolve),
                fail_closed=fail_closed,
            )
            core.discover()
            asgi = DirectoryASGI(core)
            if bundle is not None and core.records:
                bundle.route_table = core.route_table()
        except ImportError:
            pass
    else:
        bundle = app.mount(
            package_dir,
            asgi_app=asgi,
            base=base,
            fail_closed=fail_closed,
            include_directory_router=True,
        )

    return BuildResult((app, asgi, bundle))
