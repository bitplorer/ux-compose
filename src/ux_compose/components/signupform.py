"""SignupForm — SignupForm

Ported from the ``forms`` example module (spec §4); that example stays as the teaching copy.
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
    form,
    button,
    control,
    span,
)

from ux_compose.author import act, field, mark_dirty

class SignupForm(Component):
    id = "signup"
    email = MorphState("")
    error = MorphState("")
    ok = MorphState(False)
    attempts = RefState(0)

    def render(self):
        err = str(self.error or "")
        kids = (
            header(
                p("Errors are MorphState", className="kicker"),
                h2("Sign up", className="widget-title"),
            ),
            p("Validate publicly. Create the account under a Cap.", className="lede"),
            form(
                field("email", str(self.email or ""), placeholder="you@atelier.test"),
                button(
                    "Submit",
                    type="submit",
                    className="btn-primary",
                    **control("signup.submit"),
                ),
                method="post",
                action="/act/signup.submit",
                data_ux="1",
                data_target="#stage",
                className="stack",
            ),

            p(err, className="error", role="alert") if err else p(""),
            p("Welcome. The host would mint account.create here.", className="status status-ok")
            if self.ok
            else p(""),
            act("signup.create_account", "Create account (Cap)", kind="ghost"),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=("account.create",))
    def submit(self, email: str = ""):
        self.attempts = int(self.attempts or 0) + 1
        self.email = (email or self.email or "").strip()
        self.ok = False
        if "@" not in str(self.email) or "." not in str(self.email).split("@")[-1]:
            self.error = "Enter a valid email"
            return update_with(self, extra_ops=[notify("invalid")])
        self.error = ""
        self.ok = True
        return update_with(self, extra_ops=[notify(f"ok {self.email}")])

    @action(caps=("account.create",))
    def create_account(self):
        if not self.ok:
            self.error = "Submit a valid email first"
            return update_with(self, extra_ops=[notify("blocked")])
        return update_with(self, extra_ops=[notify("account created")])


__all__ = ["SignupForm"]
