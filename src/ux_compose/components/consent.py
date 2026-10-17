"""Consent — Consent

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

class Consent(Component):
    id = "consent"
    choice = MorphState("ask")

    def render(self):
        if self.choice != "ask":
            kids = (
                header(h2("Consent")),
                p(f"Recorded as {self.choice}.", className="lede"),
                act("consent.reset", "Ask again", kind="text"),
            )
        else:
            kids = (
                header(
                    p("Cookie / consent gate", className="kicker"),
                    h2("Consent", className="widget-title"),
                ),
                p("Motion recipes stay off until you allow them.", className="lede"),
                div(
                    act("consent.decide", "Allow", kind="primary", value="allow"),
                    act("consent.decide", "Essential only", kind="ghost", value="essential"),
                    className="row-actions",
                ),
            )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def decide(self, value: str = "allow"):
        self.choice = value
        return update_with(self, extra_ops=[notify(value)])

    @action(caps=())
    def reset(self):
        self.choice = "ask"
        return update_with(self)


__all__ = ["Consent"]
