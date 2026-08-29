"""Page unit — Bench. Work cards from the Host."""

from __future__ import annotations

from ux_compose import Component, div

from apps.floor.chrome import hero, ledger, wrap
from apps.floor.runtime import cards


class Bench(Component):
    id = "bench"

    def render(self):
        return wrap(
            *hero(
                kicker="Bench",
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
            ledger(),
            room="bench",
        )
