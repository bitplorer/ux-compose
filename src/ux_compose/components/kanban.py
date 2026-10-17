"""Kanban — Kanban

Ported from the ``table_board`` example module (spec §4); this module is canonical and the example imports it.
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
    ul,
    li,
    span,
)

from ux_compose.author import act, mark_dirty

ROWS = (
    ("linen-01", "Work shirt", "cut", "48"),
    ("oak-02", "Serving board", "make", "72"),
    ("wool-03", "Throw", "keep", "96"),
    ("clay-04", "Pourer", "cut", "38"),
)

class Kanban(Component):
    id = "kanban"
    cut = RefState(("linen-01", "clay-04"))
    make = RefState(("oak-02",))
    keep = RefState(("wool-03",))
    dirty = MorphState("idle")
    COLS = ("cut", "make", "keep")

    def _col(self, name: str):
        return list(getattr(self, name) or ())

    def render(self):
        names = {s: n for s, n, _, _ in ROWS}
        cols = []
        for col in self.COLS:
            cards = []
            for sku in self._col(col):
                nxt = self.COLS[(self.COLS.index(col) + 1) % 3]
                cards.append(
                    li(
                        span(names.get(sku, sku)),
                        act("kanban.move", f"To {nxt}", kind="text", sku=sku, to=nxt),
                        id=f"card-{sku}",
                        className="card-mini",
                    )
                )
            cols.append(
                div(
                    h2(col.title()),
                    ul(*cards, className="kanban-col"),
                    className="kanban-lane",
                )
            )
        kids = (
            header(
                p("Three RefState columns, one dirty", className="kicker"),
                h2("Kanban", className="widget-title"),
            ),
            div(*cols, className="kanban"),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def move(self, sku: str = "", to: str = "make"):
        if to not in self.COLS:
            return update_with(self)
        for col in self.COLS:
            setattr(self, col, tuple(x for x in self._col(col) if x != sku))
        setattr(self, to, tuple(self._col(to) + [sku]))
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(f"{sku} → {to}")])


__all__ = ["Kanban"]
