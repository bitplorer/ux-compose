"""Page unit — Door room."""

from __future__ import annotations

from ux_compose import Component, div

from apps.nook.chrome import hero
from apps.nook.theme import CARD


class Enter(Component):
    id = "enter"

    def render(self):
        return div(
            *hero(
                kicker="Door",
                title="Come in.",
                lede="Sign in is a card. The six digits spend auth.otp.",
            ),
            id=self.id,
            className=CARD,
        )
