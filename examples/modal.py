"""
Modal / sheet pattern — elevated surface.

Demonstrates:
- MorphState for open/closed presence
- RefState for silent payload
- Public open + Cap-protected confirm
- update_with for XOR-safe morph (+ optional motion)
- Progressive Superpower: same class at L1–L3
- render() returns ux-dom tags (HTML string fallback without ux-dom)

Id is ``demomodal`` so it does not collide with the product shop's confirm-modal.

Run:
  PYTHONPATH=src:. python examples/modal.py
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
    HAS_DOM,
    div,
    h2,
    p,
    header,
)

from examples._common import act, maybe_plan


class ConfirmModal(Component):
    id = "demomodal"
    open = MorphState(False)
    title = RefState("Confirm")
    body = RefState("")

    def render(self):
        if HAS_DOM:
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
        if not self.open:
            return f'<div id="{self.id}" class="modal closed"></div>'
        return (
            f'<div id="{self.id}" class="modal open" role="dialog">'
            f"<h2>{self.title}</h2><p>{self.body}</p></div>"
        )

    @action(caps=())
    def open_modal(self, title: str = "Confirm", body: str = ""):
        self.open = True
        self.title = title or "Delete this piece?"
        self.body = body or "This cannot be undone."
        return update_with(
            self,
            maybe_plan("modal-open", f"#{self.id}", ms=140),
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


if __name__ == "__main__":
    app = App.boot("Shop", strict_caps=False)
    app.add(ConfirmModal)

    ops = app.dispatch(
        "demomodal.open_modal",
        title="Delete item?",
        body="This cannot be undone.",
    )
    print("Level:", int(app.level), f"({app.level.label})")
    print("Open ops:")
    for op in ops:
        print(" ", op)

    ops = app.dispatch("demomodal.close")
    print("Close ops:", ops)

    strict = App.boot("Shop", strict_caps=True)
    strict.add(ConfirmModal)
    try:
        strict.dispatch("demomodal.confirm")
        print("UNEXPECTED success")
    except Exception as e:
        print("Cap Law:", type(e).__name__, "— confirm refused offline under strict_caps")
