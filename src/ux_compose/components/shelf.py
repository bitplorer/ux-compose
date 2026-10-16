"""Shelf — Filter + sort. Query is MorphState. Rows are RefState. dirty MorphState dirties.

Ported from the ``lists`` example module (spec §4); that example stays as the teaching copy.
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
from ux_compose import scene, rise

CATALOG = (("linen", "Work shirt", 48), ("oak", "Serving board", 72), ("wool", "Throw", 96), ("clay", "Pourer", 38))

class Shelf(Component):
    """Filter + sort. Query is MorphState. Rows are RefState. dirty MorphState dirties."""

    id = "shelf"
    query = MorphState("")
    order = MorphState("alpha")
    items = RefState(tuple(s for s, _, _ in CATALOG))
    dirty = MorphState("idle")

    def _visible(self):
        q = str(self.query or "").lower()
        by = {s: (n, p) for s, n, p in CATALOG}
        rows = [s for s in (self.items or ()) if q in s or q in by[s][0].lower()]
        if self.order == "price":
            rows = sorted(rows, key=lambda s: by[s][1])
        else:
            rows = sorted(rows, key=lambda s: by[s][0].lower())
        return rows

    def render(self):
        rows = self._visible()
        lis = [
            li(
                span(dict((s, n) for s, n, _ in CATALOG)[s], className="bag-line-name"),
                span(str(dict((s, p) for s, _, p in CATALOG)[s]), className="num"),
                id=f"item-{s}",
                className="bag-line",
            )
            for s in rows
        ] or [li("No pieces match.", className="muted", id="item-empty")]
        kids = (
            header(
                p("Stable item ids", className="kicker"),
                h2("Shelf", className="widget-title"),
            ),
            div(
                act("shelf.set_query", "All", kind="ghost", q=""),
                act("shelf.set_query", "Oak", kind="ghost", q="oak"),
                act("shelf.sort_price", "By price", kind="secondary"),
                act("shelf.sort_alpha", "By name", kind="secondary"),
                className="row-actions",
            ),
            ul(*lis, className="bag-lines"),
        )
        return div(*kids, id=self.id, className="widget")

    def _plan(self):
        return (
            scene("shelf-reorder")
            .stagger_in(
                '[id^="item-"]',
                rise.enter(ms=90),
                gap_ms=40,
            )
        )

    @action(caps=())
    def set_query(self, q: str = ""):
        self.query = q
        mark_dirty(self)
        return update_with(self, self._plan())

    @action(caps=())
    def sort_price(self):
        self.order = "price"
        mark_dirty(self)
        return update_with(self, self._plan(), extra_ops=[notify("price")])

    @action(caps=())
    def sort_alpha(self):
        self.order = "alpha"
        mark_dirty(self)
        return update_with(self, self._plan())


__all__ = ["Shelf"]
