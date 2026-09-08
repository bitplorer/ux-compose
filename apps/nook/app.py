"""Nook composition root — Document-path host via build().

Isolation Law: this module never imports ux_channel.
Channel attaches only through build() → App.use_channel (wire/).
Cap Host is cek=require after Channel.
"""
from __future__ import annotations

from pathlib import Path

from ux_compose import doctor
from ux_compose.build import build

from .chrome import document_wrap
from .document import document
from .settings import webassets

PACKAGE = Path(__file__).resolve().parent


def _mount_css(asgi):
    """Serve compiled CSS at /css/output.css. Returns asgi (maybe wrapped)."""
    if asgi is None or webassets is None:
        return asgi
    mount = getattr(webassets, "mount_css", None)
    if callable(mount):
        return mount(asgi)
    return asgi


def main(*, use_htmx: bool = False):
    app, asgi, bundle = build(
        PACKAGE,
        name="Nook",
        host="auto",
        live="auto",
        level="auto",
        base="routes",
        use_htmx=use_htmx,
        document=document,
        wrap=document_wrap(document),
        cek="require",
    )
    asgi = _mount_css(asgi)
    return app, asgi, bundle


if __name__ == "__main__":
    app, asgi, bundle = main()
    print("Level:", int(app.level), f"({app.level.label})")
    print("Host ASGI:", type(asgi).__name__ if asgi is not None else None)
    print("Surfaces:", list(bundle.surfaces.keys()) if bundle else [])
    print("Routes:", [r.get("path") for r in (bundle.route_table or [])] if bundle else [])
    report = doctor([], fail=False, bundle=bundle, app=app)
    print("Doctor surfaces:", report.surfaces)
    print("Doctor routes:", report.routes)
    if asgi is not None:
        print("Path: uxcompose serve dev apps.nook.app:asgi")

# ASGI attribute for uvicorn apps.nook.app:asgi
_app, asgi, _bundle = main()
UX = _app
BUNDLE = _bundle
