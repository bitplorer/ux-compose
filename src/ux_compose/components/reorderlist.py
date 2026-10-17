"""ReorderList — Order is a tuple of ids in RefState. Move is public. Presence ids stay stable.

Ported from the ``feeds`` example module (spec §4); this module is canonical and the example imports it.
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

class ReorderList(Component):
    """Order is a tuple of ids in RefState. Move is public. Presence ids stay stable."""

    id = "reorder"
    order = RefState(("linen", "oak", "wool", "clay"))
    dirty = MorphState("idle")
    NAMES = {"linen": "Work shirt", "oak": "Serving board", "wool": "Throw", "clay": "Pourer"}

    def render(self):
        rows = list(self.order or ())
        lis = []
        for i, sku in enumerate(rows):
            lis.append(
                li(
                    span(self.NAMES.get(sku, sku), className="bag-line-name"),
                    act("reorder.up", "Up", kind="text", sku=sku) if i else span(""),
                    act("reorder.down", "Down", kind="text", sku=sku)
                    if i < len(rows) - 1
                    else span(""),
                    id=f"ord-{sku}",
                    className="bag-line",
                )
            )
        kids = (
            header(
                p("Stable item ids · order silent", className="kicker"),
                h2("Reorder", className="widget-title"),
            ),
            p("Moving a row is public. Archiving it would take a Cap.", className="lede"),
            ul(*lis, className="bag-lines"),
        )
        return div(*kids, id=self.id, className="widget")

    def _move(self, sku: str, delta: int):
        rows = list(self.order or ())
        if sku not in rows:
            return
        i = rows.index(sku)
        j = max(0, min(len(rows) - 1, i + delta))
        rows.pop(i)
        rows.insert(j, sku)
        self.order = tuple(rows)
        mark_dirty(self)

    @action(caps=())
    def up(self, sku: str = ""):
        self._move(sku, -1)
        return update_with(self, extra_ops=[notify("up")])

    @action(caps=())
    def down(self, sku: str = ""):
        self._move(sku, 1)
        return update_with(self, extra_ops=[notify("down")])


__all__ = ["ReorderList"]
