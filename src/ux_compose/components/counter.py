"""Counter — Increment is public. Reset is Cap-protected (Authority Clock).

Ported from the ``foundation`` example module (spec §4); this module is canonical and the example imports it.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    div,
    h2,
    p,
    span,
    header,
)

from ux_compose.author import act, optional_plan, mark_dirty

class Counter(Component):
    """Increment is public. Reset is Cap-protected (Authority Clock).

    ``n`` is RefState because Channel's session plane refuses quantity
    MorphState values. ``dirty`` is the qualitative MorphState so the unit still morphs.
    """

    id = "counter"
    n = RefState(0)
    last = RefState("")
    dirty = MorphState("idle")

    def render(self):
        n = int(self.n or 0)
        last = str(self.last or "—")
        body = (
            header(
                p("Magnitude lives in RefState", className="kicker"),
                h2("Counter", className="widget-title"),
                className="widget-head",
            ),
            p(
                span(str(n), className="num"),
                span(f"last {last}", className="muted"),
                className="counter-face",
            ),
            div(
                act("counter.dec", "Decrease", kind="ghost"),
                act("counter.inc", "Increase", kind="primary", sku="tick"),
                act("counter.reset", "Reset", kind="text"),
                className="row-actions",
            ),
        )
        return div(*body, id=self.id, className="widget", data_dirty=str(self.dirty))

    @action(caps=())
    def inc(self, sku: str = ""):
        self.n = int(self.n or 0) + 1
        self.last = sku or "inc"
        mark_dirty(self)
        return update_with(
            self,
            optional_plan("counter-inc", f"#{self.id}", ms=120),
            extra_ops=[notify(f"n={self.n}")],
        )

    @action(caps=())
    def dec(self):
        self.n = max(0, int(self.n or 0) - 1)
        self.last = "dec"
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(f"n={self.n}")])

    @action(caps=("admin.reset",))
    def reset(self):
        """Fails closed offline under strict_caps; live path needs a minted Cap."""
        self.n = 0
        self.last = ""
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("reset")])


__all__ = ["Counter"]
