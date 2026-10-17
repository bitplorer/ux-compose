"""UndoSnack — Delete now, undo window via follow-up-shaped public action.

Ported from the ``lists`` example module (spec §4); that example stays as the teaching copy.
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
)

from ux_compose.author import act, mark_dirty, optional_plan
from ux_compose import scene, rise

CATALOG = (("linen", "Work shirt", 48), ("oak", "Serving board", 72), ("wool", "Throw", 96), ("clay", "Pourer", 38))

class UndoSnack(Component):
    """Delete now, undo window via follow-up-shaped public action."""

    id = "undo"
    items = RefState(("linen", "oak", "wool"))
    gone = RefState("")
    open = MorphState(False)
    dirty = MorphState("idle")

    def render(self):
        names = dict((s, n) for s, n, _ in CATALOG)
        lis = [
            li(
                span(names.get(s, s)),
                act("undo.remove", "Remove", kind="text", sku=s),
                id=f"undo-{s}",
                className="bag-line",
            )
            for s in (self.items or ())
        ] or [li("Nothing on the shelf.", className="muted")]
        snack = (
            div(
                span(f"Removed {self.gone}."),
                act("undo.restore", "Undo", kind="primary"),
                className="snack",
                role="status",
            )
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Undo is a public reverse of a public delete", className="kicker"),
                h2("Undo", className="widget-title"),
            ),
            ul(*lis, className="bag-lines"),
            snack,
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def remove(self, sku: str = ""):
        self.items = tuple(s for s in (self.items or ()) if s != sku)
        self.gone = sku
        self.open = True
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(f"removed {sku}")])

    @action(caps=())
    def restore(self):
        if self.gone and self.gone not in (self.items or ()):
            self.items = tuple(self.items or ()) + (self.gone,)
        self.gone = ""
        self.open = False
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("restored")])


__all__ = ["UndoSnack"]
