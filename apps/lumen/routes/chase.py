"""Page unit — Chase. Work cards from the Host."""

from __future__ import annotations

from ux_compose import Component, div

from apps.lumen.chrome import hero, wrap
from apps.lumen.runtime import cards


class Chase(Component):
    id = "chase"

    def render(self):
        return wrap(
            *hero(
                kicker="Chase",
                title="The pour, the stars, the lanes.",
                lede="Magnitudes stay silent. The Host writes when you move.",
            ),
            div(
                *cards(
                    "rating",
                    "kanban",
                    "timeline",
                    "slider",
                    "progress",
                    "empty",
                    "skeleton",
                    "pullrefresh",
                    "accordion",
                    "tabs",
                ),
                className="flex flex-col gap-8",
            ),
            room="chase",
        )
