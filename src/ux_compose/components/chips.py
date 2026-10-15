"""Chips — Chips

Ported from the ``systems`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    App,
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
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty

class Chips(Component):
    id = "chips"
    tags = RefState(("linen", "quiet"))
    dirty = MorphState("idle")

    def render(self):
        chips = [
            li(
                span(t),
                act("chips.remove", "×", kind="text", tag=t),
                className="chip",
                id=f"chip-{t}",
            )
            for t in (self.tags or ())
        ]
        kids = (
            header(
                p("Tag set as RefState", className="kicker"),
                h2("Chips", className="widget-title"),
            ),
            ul(*chips, className="chip-row"),
            div(
                act("chips.add", "Add oak", kind="secondary", tag="oak"),
                act("chips.add", "Add wool", kind="secondary", tag="wool"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def add(self, tag: str = ""):
        if tag and tag not in (self.tags or ()):
            self.tags = tuple(self.tags or ()) + (tag,)
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def remove(self, tag: str = ""):
        self.tags = tuple(t for t in (self.tags or ()) if t != tag)
        mark_dirty(self)
        return update_with(self)


__all__ = ["Chips"]
