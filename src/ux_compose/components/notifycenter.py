"""NotifyCenter — NotifyCenter

Ported from the ``systems`` example module (spec §4); this module is canonical and the example imports it.
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
    ul,
    li,
    span,
)

from ux_compose.author import act, mark_dirty

class NotifyCenter(Component):
    id = "inbox"
    open = MorphState(False)
    unread = RefState(3)
    items = RefState(("Order reserved.", "Throw restocked.", "Cap minted for checkout."))
    dirty = MorphState("idle")

    def render(self):
        n = int(self.unread or 0)
        panel = (
            ul(*[li(x) for x in (self.items or ())], className="hit-list")
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Badge is derived from RefState", className="kicker"),
                h2("Notifications", className="widget-title"),
            ),
            div(
                act(
                    "inbox.toggle",
                    f"Inbox · {n}",
                    kind="primary" if n else "ghost",
                ),
                act("inbox.mark_read", "Mark read", kind="text"),
                className="row-actions",
            ),
            panel,
        )
        return div(*kids, id=self.id, className="widget", data_unread=str(n))

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def mark_read(self):
        self.unread = 0
        mark_dirty(self)
        return update_with(self)


__all__ = ["NotifyCenter"]
