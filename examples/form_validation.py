"""Back-compat path — full form lesson lives in ``examples/forms.py``."""
from __future__ import annotations

from examples.forms import SignupForm, demo  # noqa: F401

if __name__ == "__main__":
    from examples.forms import demo as _demo

    _demo()
