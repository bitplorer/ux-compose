"""Page unit — Visit room."""

from __future__ import annotations

from ux_compose import Component, div

from apps.nook.chrome import hero
from apps.nook.theme import CARD


class Visit(Component):
    id = "visit"

    def render(self):
        return div(
            *hero(
                kicker="Visit",
                title="Book a morning at the bench.",
                lede="Plan, day, then finish. The last step spends a Cap.",
            ),
            id=self.id,
            className=CARD,
        )
