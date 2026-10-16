"""ConfirmModal — ConfirmModal

Ported from the ``modal`` example module (spec §4); that example stays as the teaching copy.
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

class ConfirmModal(Component):
    id = "demomodal"
    open = MorphState(False)
    title = RefState("Confirm")
    body = RefState("")

    def render(self):
        if not self.open:
            return div(
                header(
                    p("Presence flag + Cap confirm", className="kicker"),
                    h2("Modal", className="widget-title"),
                ),
                p("Closed. The unit keeps its id in the tree.", className="lede"),
                act(
                    "demomodal.open_modal",
                    "Open dialog",
                    kind="primary",
                    title="Delete this piece?",
                    body="This cannot be undone.",
                ),
                id=self.id,
                className="widget",
                data_open="0",
            )
        return div(
            header(h2(str(self.title))),
            p(str(self.body), className="lede"),
            div(
                act("demomodal.close", "Cancel", kind="ghost"),
                act("demomodal.confirm", "Confirm", kind="primary"),
                className="row-actions",
            ),
            id=self.id,
            className="widget dialog",
            role="dialog",
            data_open="1",
        )

    @action(caps=())
    def open_modal(self, title: str = "Confirm", body: str = ""):
        self.open = True
        self.title = title or "Delete this piece?"
        self.body = body or "This cannot be undone."
        return update_with(
            self,
            optional_plan("modal-open", f"#{self.id}", ms=140),
            extra_ops=[notify(f"Opened: {self.title}")],
        )

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=("orders.confirm",))
    def confirm(self):
        self.open = False
        return update_with(self, extra_ops=[notify("Confirmed")])


__all__ = ["ConfirmModal"]
