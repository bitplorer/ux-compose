"""Page unit — Gate. Auth seams hit the Host books."""

from __future__ import annotations

from ux_compose import Component, div

from apps.lumen.chrome import hero, wrap
from apps.lumen.runtime import cards


class Gate(Component):
    id = "gate"

    def render(self):
        return wrap(
            *hero(
                kicker="Gate",
                title="The books know one pair.",
                lede="you@lumen.test / pressroom1. OTP 314159. Anything else is refused.",
            ),
            div(*cards("login", "otp"), className="flex flex-col gap-8"),
            room="gate",
        )
