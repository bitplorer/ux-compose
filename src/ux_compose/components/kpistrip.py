"""KpiStrip — Dashboard numbers. All magnitudes in RefState. Stamp dirties the strip.

Ported from the ``ops`` example module (spec §4); that example stays as the teaching copy.
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
    header,
    section,
)

from ux_compose.author import act, mark_dirty

class KpiStrip(Component):
    """Dashboard numbers. All magnitudes in RefState. Stamp dirties the strip.

    A real dashboard would source these from Host DB, never from the session plane.
    """

    id = "kpi"
    bag = RefState(3)
    held = RefState(48)
    placed = RefState(2)
    dirty = MorphState("idle")

    def render(self):
        cells = (
            ("In bag", int(self.bag or 0)),
            ("Held", int(self.held or 0)),
            ("Placed", int(self.placed or 0)),
        )
        tiles = [
            section(
                p(label, className="kicker"),
                p(str(n), className="num"),
                className="kpi-tile",
            )
            for label, n in cells
        ]
        kids = (
            header(
                p("Magnitudes silent · dirty MorphState dirties", className="kicker"),
                h2("KPI strip", className="widget-title"),
            ),
            div(*tiles, className="kpi-grid"),
            div(
                act("kpi.tick_up", "A sale lands", kind="primary"),
                act("kpi.reset", "Zero the board", kind="text"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def tick_up(self):
        self.bag = max(0, int(self.bag or 0) - 1)
        self.placed = int(self.placed or 0) + 1
        self.held = int(self.held or 0) + 12
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("sale")])

    @action(caps=())
    def reset(self):
        self.bag = 0
        self.held = 0
        self.placed = 0
        mark_dirty(self)
        return update_with(self)


__all__ = ["KpiStrip"]
