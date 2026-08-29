"""Floor composition root. Clock A ``build()``. Isolation: no ux_channel."""

from __future__ import annotations

from pathlib import Path

from ux_compose.build import build

from .document import document
from .host import HOUSE
from .runtime import bind_app
from .seams import ALL, hydrate

PACKAGE = Path(__file__).resolve().parent

app, asgi, bundle = build(
    PACKAGE,
    name="Floor",
    host="auto",
    live="auto",
    document=document,
)
app.add(*ALL)
hydrate(app)
bind_app(app)

__all__ = ["app", "asgi", "bundle", "HOUSE"]
