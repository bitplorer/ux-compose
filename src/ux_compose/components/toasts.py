"""Toasts — Stack of one-shot messages. Push is public. Items live in RefState.

Ported from the ``overlays`` example module (spec §4); that example stays as the teaching copy.
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

from ux_compose.author import act, mark_dirty, optional_plan, optional_slide, optional_fade

class Toasts(Component):
    """Stack of one-shot messages. Push is public. Items live in RefState."""

    id = "toasts"
    items = RefState(())
    dirty = MorphState("idle")
    _seq = RefState(0)

    def render(self):
        rows = list(self.items or ())
        lis = [
            li(str(row.get("message", "")), id=f"toast-{row.get('id')}", className="toast")
            for row in rows[-4:]
        ]
        kids = (
            header(
                p("notify() is the Op. This unit *shows* them.", className="kicker"),
                h2("Toasts", className="widget-title"),
            ),
            ul(*lis, className="toast-list") if lis else p("None yet.", className="muted"),
            div(
                act("toasts.push", "Push note", kind="primary", message="Saved to the table"),
                act("toasts.clear", "Clear", kind="ghost"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def push(self, message: str = "Saved"):
        self._seq = int(self._seq or 0) + 1
        row = {"id": str(self._seq), "message": message}
        self.items = tuple(self.items or ()) + (row,)
        mark_dirty(self)
        return update_with(
            self,
            optional_plan("toast-in", f"#toast-{row['id']}", ms=100),
            extra_ops=[notify(message)],
        )

    @action(caps=())
    def clear(self):
        self.items = ()
        mark_dirty(self)
        return update_with(self)


__all__ = ["Toasts"]
