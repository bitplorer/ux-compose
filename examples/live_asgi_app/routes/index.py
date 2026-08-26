"""Page unit — module stem matches class name (index.py → Index → GET /).

Clock A GET is the product host pipeline. Isolation: no ux_channel import.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    control,
    HAS_DOM,
    div,
    h1,
    span,
    button,
)

try:
    from ux_compose import scene, rise
except Exception:
    scene = rise = None


class Index(Component):
    id = "livecounter"
    n = RefState(0)
    stamp = MorphState("idle")

    def render(self):
        val = int(self.n or 0)
        if HAS_DOM and div is not None:
            return div(
                h1(f"Count: {val}"),
                span("+ via Channel Intent when live"),
                button("+1", **control("inc")),
                id=self.id,
                className="counter",
            )
        return f'<div id="{self.id}"><h1>Count: {val}</h1></div>'

    @action(caps=())
    def inc(self):
        self.n = int(self.n or 0) + 1
        self.stamp = "tock" if self.stamp == "tick" else "tick"
        plan = None
        if scene is not None and rise is not None:
            try:
                plan = scene("inc").enter(f"#{self.id}", rise.enter(ms=100))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(f"n={self.n}")])
