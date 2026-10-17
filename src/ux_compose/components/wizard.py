"""Wizard — Named steps, not integers. Payload rides in RefState until the last verb.

Ported from the ``forms`` example module (spec §4); this module is canonical and the example imports it.
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
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty

class Wizard(Component):
    """Named steps, not integers. Payload rides in RefState until the last verb."""

    id = "wizard"
    step = MorphState("who")
    name = RefState("")
    piece = RefState("linen")
    dirty = MorphState("idle")

    STEPS = ("who", "piece", "review")

    def render(self):
        step = str(self.step or "who")
        body = []
        if step == "who":
            body = [
                p("Who is the order for?", className="lede"),
                form(
                    field("name", str(self.name or ""), placeholder="Name"),
                    button("Continue", type="submit", className="btn-primary", **control("wizard.next")),
                    method="post",
                    action="/act/wizard.next",
                    data_ux="1",
                    data_target="#stage",
                    className="stack",
                ),

            ]
        elif step == "piece":
            body = [
                p(f"Hello {self.name or 'friend'}. Pick a piece.", className="lede"),
                div(
                    act("wizard.choose", "Linen", kind="secondary", piece="linen"),
                    act("wizard.choose", "Oak", kind="secondary", piece="oak"),
                    act("wizard.choose", "Wool", kind="secondary", piece="wool"),
                    className="row-actions",
                ),
            ]
        else:
            body = [
                p(
                    f"{self.name or 'Friend'} · {self.piece}. Placing the order is a Cap.",
                    className="lede",
                ),
                act("wizard.place", "Place order", kind="primary"),
                act("wizard.back", "Back", kind="text"),
            ]
        kids = (
            header(
                p(f"Step {step}", className="kicker"),
                h2("Wizard", className="widget-title"),
            ),
            *body,
        )
        return div(*kids, id=self.id, className="widget", data_step=step)

    @action(caps=())
    def next(self, name: str = ""):
        if name:
            self.name = name
        if not str(self.name or "").strip():
            return update_with(self, extra_ops=[notify("name required")])
        self.step = "piece"
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def choose(self, piece: str = "linen"):
        self.piece = piece
        self.step = "review"
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def back(self):
        order = list(self.STEPS)
        i = max(0, order.index(self.step) - 1) if self.step in order else 0
        self.step = order[i]
        return update_with(self)

    @action(caps=("orders.place",))
    def place(self):
        self.step = "who"
        self.name = ""
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("placed")])


__all__ = ["Wizard"]
