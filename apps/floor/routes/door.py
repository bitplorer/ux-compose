"""Page unit — Door. Auth seams hit the Host books."""

from __future__ import annotations

from ux_compose import Component, div

from apps.floor.chrome import hero, ledger, wrap
from apps.floor.runtime import cards


class Door(Component):
    id = "door"

    def render(self):
        return wrap(
            *hero(
                kicker="Door",
                title="The books know one pair.",
                lede="you@floor.test / housewood1. OTP 246810. Anything else is refused.",
            ),
            div(*cards("login", "otp"), className="flex flex-col gap-8"),
            ledger(),
            room="door",
        )
