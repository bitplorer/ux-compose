"""
Form validation pattern — elevated surface.

Demonstrates:
- MorphState for field values + error messages (dirty → morph)
- RefState for silent attempt counter
- Public validate + Cap-protected submit
- update_with for XOR-safe morph after validation
- Progressive Superpower: same class at every level

Run:
  PYTHONPATH=src python examples/form_validation.py
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
    control,
)


class SignupForm(Component):
    id = "signup"
    email = MorphState("")
    error = MorphState("")
    attempts = RefState(0)

    def render(self):
        err = f'<p class="error">{self.error}</p>' if self.error else ""
        attrs = control("submit", email=self.email or "")
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return (
            f'<form id="{self.id}">'
            f'<input name="email" value="{self.email}" placeholder="you@example.com" />'
            f"{err}"
            f"<button {attr_str}>Sign up</button>"
            f"</form>"
        )

    @action(caps=())
    def set_email(self, email: str = ""):
        self.email = email
        self.error = ""
        return update_with(self)

    @action(caps=())
    def submit(self, email: str = ""):
        self.attempts = int(self.attempts) + 1
        self.email = email or self.email
        if "@" not in str(self.email):
            self.error = "Enter a valid email"
            return update_with(self, extra_ops=[notify("Validation failed")])
        self.error = ""
        # Domain work would live here; Cap would protect the live path
        return update_with(self, extra_ops=[notify(f"Welcome {self.email}")])

    @action(caps=("account.create",))
    def create_account(self):
        # Cap-protected when live / strict
        return [notify("Account created")]


if __name__ == "__main__":
    app = App.boot("Auth", strict_caps=False)
    app.add(SignupForm)

    print("Level:", int(app.level), f"({app.level.label})")

    ops = app.dispatch("signup.submit", email="not-an-email")
    print("Invalid submit:")
    for op in ops:
        print(" ", op)

    ops = app.dispatch("signup.submit", email="you@example.com")
    print("Valid submit:")
    for op in ops:
        print(" ", op)

    strict = App.boot("Auth", strict_caps=True)
    strict.add(SignupForm)
    try:
        strict.dispatch("signup.create_account")
        print("UNEXPECTED success")
    except Exception as e:
        print("Cap Law:", type(e).__name__, "— create_account refused offline under strict_caps")
