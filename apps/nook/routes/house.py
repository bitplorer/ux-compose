"""Page unit — House room."""

from __future__ import annotations

from ux_compose import Component, div

from apps.nook.chrome import hero
from apps.nook.theme import CARD


class House(Component):
    id = "house"

    def render(self):
        return div(
            *hero(
                kicker="House",
                title="Linen, oak, wool, clay.",
                lede="Search, filter, page the shelf. Swipe the stage.",
            ),
            id=self.id,
            className=CARD,
        )
