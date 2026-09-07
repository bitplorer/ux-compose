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
    div,
    h1,
    span,
    button,
    scene,
    rise,
)


class Index(Component):
    id = "livecounter"
    n = RefState(0)
    dirty = MorphState("idle")

    def render(self):
        val = int(self.n or 0)
        return div(
            h1(f"Count: {val}"),
            span("+ via Channel Intent when live"),
            button("+1", **control("inc")),
            id=self.id,
            className="counter",
        )

    @action(caps=())
    def inc(self):
        self.n = int(self.n or 0) + 1
        self.dirty = "tock" if self.dirty == "tick" else "tick"
        plan = scene("inc").enter(f"#{self.id}", rise.enter(ms=100))
        return update_with(self, plan, extra_ops=[notify(f"n={self.n}")])
