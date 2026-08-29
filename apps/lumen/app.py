"""Lumen composition root. Clock A ``build()``. Isolation: no ux_channel."""

from __future__ import annotations

from pathlib import Path

from ux_compose.build import build

from .document import document
from .runtime import bind_app
from .seams import ALL, hydrate
from .settings import webassets

PACKAGE = Path(__file__).resolve().parent


def _open_public_actions(app) -> None:
    """Kit ``bind()`` emits ``data-channel-action`` without a Cap token.

    Production mints via Channel ``control()``. This gallery is development:
    public kit verbs must play. Registry lives on the attached Channel;
    product code does not import ``ux_channel``.
    """
    ch = getattr(app, "_channel", None)
    reg = getattr(ch, "registry", None)
    if reg is None:
        return
    setattr(reg, "require_cap", False)


def main():
    app, asgi, bundle = build(
        PACKAGE,
        name="Lumen",
        host="auto",
        live="auto",
        document=document,
    )
    app.add(*ALL)
    hydrate(app)
    bind_app(app)
    _open_public_actions(app)
    if asgi is not None and webassets is not None:
        asgi = webassets.mount_css(asgi)
        if callable(getattr(asgi, "get", None)):

            @asgi.get("/health")
            def health():
                return {
                    "app": "Lumen",
                    "ok": True,
                    "level": int(app.level),
                    "label": app.level.label,
                }

    return app, asgi, bundle


app, asgi, bundle = main()

__all__ = ["app", "asgi", "bundle", "main"]
