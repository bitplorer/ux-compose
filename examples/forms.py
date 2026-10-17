"""Forms — field errors, wizard, search/typeahead.

Validation is MorphState (must repaint). Attempt counters are RefState.
The submit that *creates* an account is Cap-protected; checking an email is not.

Wizard: step MorphState as a name, not an int (Channel plane). Payload in RefState.

Run:
  PYTHONPATH=src:. python examples/forms.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.search import Search
from ux_compose.components.signupform import SignupForm
from ux_compose.components.wizard import Wizard


def demo() -> None:
    app = App.boot("Forms")
    app.add(SignupForm, Wizard, Search)
    print("bad", app.dispatch("signup.submit", email="nope", _trusted=True))
    print("ok", app.dispatch("signup.submit", email="you@atelier.test", _trusted=True))
    print("wiz", app.dispatch("wizard.next", name="Noor"))
    print("search", app.dispatch("search.type", q="oak"))
    strict = App.boot("Forms", strict_caps=True)
    strict.add(SignupForm)
    try:
        strict.dispatch("signup.create_account")
        print("UNEXPECTED")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
