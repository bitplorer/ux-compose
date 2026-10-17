"""SliderField — Magnitude in RefState. Named band is derived, never stored as an int MorphState.

Ported from the ``fields`` example module (spec §4); this module is canonical and the example imports it.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    update_with,
    div,
    h2,
    p,
    header,
    span,
)

from ux_compose.author import act, mark_dirty

class SliderField(Component):
    """Magnitude in RefState. Named band is derived, never stored as an int MorphState."""

    id = "slider"
    value = RefState(40)
    dirty = MorphState("idle")
    STEPS = (0, 25, 50, 75, 100)

    def render(self):
        v = int(self.value or 0)
        band = "empty" if v == 0 else "low" if v < 50 else "mid" if v < 100 else "full"
        segs = [
            act(
                "slider.set",
                str(n),
                kind="primary" if n == v else "ghost",
                n=str(n),
            )
            for n in self.STEPS
        ]
        kids = (
            header(
                p("RefState magnitude · named band derived", className="kicker"),
                h2("Slider", className="widget-title"),
            ),
            p(
                span(f"{v}%", className="num"),
                span(band, className="chip"),
                className="counter-face",
            ),
            div(className=f"bar bar-{band}"),
            div(*segs, className="seg"),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def set(self, n: str = "40"):
        try:
            v = int(n)
        except ValueError:
            v = 40
        self.value = max(0, min(100, v))
        mark_dirty(self)
        return update_with(self)


__all__ = ["SliderField"]
