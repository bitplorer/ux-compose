"""Composition root — one place to set host + live plane.

::

    from ux_compose.build import build
    from document import document

    app, asgi, bundle = build(
        Path(__file__).parent,
        name="Shop",
        host="auto",   # auto|fastapi|asgi
        live="auto",   # auto|channel|null
        level="auto",
        document=document,
    )

Orchestra only: host.open → L1 boot → document → channel on asgi →
DirectoryRoutes.discover → host.bind. Path law and HTML wrap live elsewhere.
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


def _attach_document(app: Any, document: Any, *, use_htmx: bool) -> Any:
    """Attach the author's Document, or synthesize one if none given.

    Author-provided Document is the SSoT. HTMX stays opt-in.
    Missing ux-dom is a soft skip (L1 HTML-string path).
    """
    if document is not None:
        if use_htmx:
            try:
                from ux_dom.runtime import Htmx

                document.use(Htmx())
            except Exception:
                pass
        app.use_dom(document)
        return document
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
        document = Document(head=[], body=[], ensure_csrf_token=False).use(*runtimes)
        app.use_dom(document, author=False)
        return document
    except ImportError:
        return None


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
    document: Any = None,
) -> BuildResult:
    """Boot specialists + mount page units. Host and live set only here.

    host:
      - ``"auto"`` — FastAPI if importable, else DirectoryASGI
      - ``"fastapi"`` — FastAPI + page binder (preferred)
      - ``"asgi"`` — DirectoryASGI (no FastAPI)

    live:
      - ``"auto"`` — Channel when ux_channel importable
      - ``"channel"`` — prefer Channel
      - ``"null"`` — offline Behavior only
    """
    from ux_compose import App
    from ux_compose.routing.core import DirectoryRoutes, RouterHooks
    from ux_compose.routing.host import KIND_FASTAPI, bind as host_bind
    from ux_compose.routing.host import open as host_open

    package_dir = Path(package_dir).resolve()
    host_l = (host or "auto").lower()
    live_l = (live or "auto").lower()

    want_channel = live_l in ("auto", "channel")
    if live_l == "null":
        want_channel = False

    auto_level = isinstance(level, str) and str(level).lower() == "auto"
    # Boot is L1. Channel/Motion attach below, after the process exists.
    boot_level: int | str = 1 if auto_level else min(int(level), 1)

    asgi, kind = host_open(name=name, host=host_l, asgi_app=asgi_app)

    app = App.boot(name, strict_caps=False, level=boot_level)
    author_document = document
    document = _attach_document(app, author_document, use_htmx=use_htmx)

    if want_channel and kind == KIND_FASTAPI and asgi is not None:
        try:
            app.use_channel(asgi_app=asgi)
        except Exception:
            if live_l == "channel":
                raise
    elif want_channel:
        try:
            app.use_channel()
        except Exception:
            if live_l == "channel":
                raise

    pinned = None if auto_level else max(0, min(3, int(level)))
    want_motion = live_l != "null" and (auto_level or (pinned is not None and pinned >= 3))
    if want_motion:
        try:
            app.use_motion()
        except Exception:
            if pinned is not None and pinned >= 3:
                raise

    bundle = app.mount(
        package_dir,
        asgi_app=None,
        base=base,
        fail_closed=fail_closed,
        bind_pages=False,
    )

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
    asgi = host_bind(
        asgi=asgi,
        kind=kind,
        core=core,
        document=document,
        wrap=author_document,
        resolve_unit=_resolve,
    )
    if bundle is not None and core.records:
        bundle.route_table = core.route_table()

    return BuildResult((app, asgi, bundle))
