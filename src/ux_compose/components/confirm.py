"""Confirm — Ask, then Cap-protected confirm. Target id is silent RefState.

Ported from the ``overlays`` example module (spec §4); this module is canonical and the example imports it.
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
)

from ux_compose.author import act, optional_plan

class Confirm(Component):
    """Ask, then Cap-protected confirm. Target id is silent RefState."""

    id = "confirm"
    open = MorphState(False)
    target = RefState("")

    def render(self):
        if not self.open:
            kids = (
                header(
                    p("Public ask · protected confirm", className="kicker"),
                    h2("Confirm", className="widget-title"),
                ),
                p("Destroying a row is an authority event.", className="lede"),
                act("confirm.ask", "Delete the oak board…", kind="secondary", id="oak-02"),
            )
            return div(*kids, id=self.id, className="widget", data_open="0")
        kids = (
            header(h2("Delete this piece?")),
            p(f"Target {self.target or 'row'}. This cannot be undone.", className="lede"),
            div(
                act("confirm.cancel", "Keep it", kind="ghost"),
                act("confirm.confirm", "Delete", kind="primary"),
                className="row-actions",
            ),
        )
        return div(
            *kids,
            id=self.id,
            className="widget dialog",
            role="dialog",
            data_open="1",
        )

    @action(caps=())
    def ask(self, id: str = ""):
        self.target = id
        self.open = True
        return update_with(self, optional_plan("confirm-open", f"#{self.id}", ms=140))

    @action(caps=())
    def cancel(self):
        self.open = False
        self.target = ""
        return update_with(self)

    @action(caps=("items.delete",))
    def confirm(self):
        gone = self.target
        self.open = False
        self.target = ""
        return update_with(self, extra_ops=[notify(f"deleted {gone}")])


__all__ = ["Confirm"]
