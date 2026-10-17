"""PasswordField — Reveal is boolean MorphState. The secret itself is RefState (not painted as MorphState).

Ported from the ``fields`` example module (spec §4); this module is canonical and the example imports it.
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
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty

class PasswordField(Component):
    """Reveal is boolean MorphState. The secret itself is RefState (not painted as MorphState)."""

    id = "password"
    shown = MorphState(False)
    secret = RefState("")
    dirty = MorphState("idle")

    def render(self):
        shown = bool(self.shown)
        raw_s = str(self.secret or "")
        face = raw_s if shown else ("•" * len(raw_s) if raw_s else "empty")
        kids = (
            header(
                p("Bool reveal · secret silent", className="kicker"),
                h2("Password", className="widget-title"),
            ),
            p(face, className="lede"),
            form(
                field("secret", raw_s if shown else "", placeholder="Passphrase", kind="text"),
                button("Hold", type="submit", className="btn-secondary", **control("password.set")),
                method="post",
                action="/act/password.set",
                data_ux="1",
                data_target="#stage",
                className="stack",
            ),

            div(
                act("password.toggle", "Hide" if shown else "Reveal", kind="ghost"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def set(self, secret: str = ""):
        self.secret = secret
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def toggle(self):
        self.shown = not bool(self.shown)
        return update_with(self)


__all__ = ["PasswordField"]
