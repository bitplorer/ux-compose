"""Overlays — Toasts, Confirm, Lightbox, Command palette, Banner.

Overlays are Components with an open/items MorphState, not a second Document.
Document SSoT still holds: one HTML shell, many units.

Confirm's destructive verb is Cap-protected. Opening the dialog is public.

Run:
  PYTHONPATH=src:. python examples/overlays.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.banner import Banner
from ux_compose.components.confirm import Confirm
from ux_compose.components.lightbox import Lightbox
from ux_compose.components.palette import Palette
from ux_compose.components.toasts import Toasts


def demo() -> None:
    app = App.boot("Overlays")
    app.add(Toasts, Confirm, Lightbox, Palette, Banner)
    print("toast", app.dispatch("toasts.push", message="hi"))
    print("ask", app.dispatch("confirm.ask", id="oak-02"))
    print("light", app.dispatch("lightbox.open_box"))
    strict = App.boot("Overlays", strict_caps=True)
    strict.add(Confirm)
    try:
        strict.dispatch("confirm.confirm")
        print("UNEXPECTED confirm")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
