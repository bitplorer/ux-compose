"""Pulseboard composition root — Document-path host via build().

Isolation Law: this module never imports ux_channel.
Channel attaches only through build() → App.use_channel (wire/).
Cap Host is cek=require after Channel.
"""
from __future__ import annotations

from pathlib import Path

from ux_compose import doctor
from ux_compose.build import build

from apps.pulseboard.chrome import document_wrap
from apps.pulseboard.document import document
from apps.pulseboard.registry import bind as bind_registry
from apps.pulseboard.settings import webassets
from apps.pulseboard.widgets import BOARD_CLASSES

PACKAGE = Path(__file__).resolve().parent


def _mount_static(asgi):
    if asgi is None:
        return asgi
    try:
        from fastapi.staticfiles import StaticFiles
    except ImportError:
        return asgi
    static = PACKAGE / "static"
    if static.is_dir() and not _has_route(asgi, "/static"):
        asgi.mount("/static", StaticFiles(directory=str(static)), name="static")
    mount = getattr(webassets, "mount_css", None)
    if callable(mount):
        asgi = mount(asgi)
    return asgi


def _has_route(asgi, prefix: str) -> bool:
    routes = getattr(asgi, "routes", None) or ()
    for route in routes:
        path = getattr(route, "path", "") or ""
        if path.startswith(prefix):
            return True
    return False


def register_board(app, bundle=None):
    """Add kit companions and bind the live registry (studio + product)."""
    return _register_board(app, bundle)


def _register_board(app, bundle):
    behavior = getattr(app, "_behavior", None) or getattr(app, "behavior", None)
    existing: set[str] = set()
    if behavior is not None and hasattr(behavior, "components"):
        try:
            existing = set(dict(behavior.components()).keys())
        except Exception:
            existing = set()
    missing = [
        cls
        for cls in BOARD_CLASSES
        if str(getattr(cls, "id", "") or cls.__name__.lower()) not in existing
    ]
    if missing:
        app.add(*missing)
    registry = dict(getattr(bundle, "unit_registry", {}) or {}) if bundle is not None else {}
    if behavior is not None and hasattr(behavior, "components"):
        try:
            registry.update(dict(behavior.components()))
        except Exception:
            pass
    for cls in BOARD_CLASSES:
        sid = str(getattr(cls, "id", "") or cls.__name__.lower())
        if sid in registry:
            continue
        try:
            registry[sid] = cls()
        except Exception:
            continue
    if bundle is not None:
        bundle.unit_registry = registry
    bind_registry(registry)
    return registry


def main(*, use_htmx: bool = True):
    app, asgi, bundle = build(
        PACKAGE,
        name="Pulseboard",
        host="auto",
        live="auto",
        level="auto",
        base="routes",
        fail_closed=False,
        use_htmx=use_htmx,
        document=document,
        wrap=document_wrap(document),
        cek="require",
    )
    _register_board(app, bundle)
    asgi = _mount_static(asgi)
    return app, asgi, bundle


if __name__ == "__main__":
    app, asgi, bundle = main()
    print("Level:", int(app.level), f"({app.level.label})")
    print("Host ASGI:", type(asgi).__name__ if asgi is not None else None)
    print("Surfaces:", list(bundle.surfaces.keys()) if bundle else [])
    print("Board:", sorted(k for k in (bundle.unit_registry or {}) if str(k).startswith("desk_")))
    report = doctor([], fail=False, bundle=bundle, app=app)
    print("Doctor surfaces:", report.surfaces)
    print("Doctor routes:", report.routes)
    if asgi is not None:
        print("Path: PYTHONPATH=src:. uxcompose serve apps.pulseboard.server:app --host 0.0.0.0 --port 8080")

_app, asgi, _bundle = main()
UX = _app
BUNDLE = _bundle
