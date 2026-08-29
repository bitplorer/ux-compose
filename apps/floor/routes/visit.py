"""Page unit — Visit. Flow and overlays from the Host."""

from __future__ import annotations

from ux_compose import Component, div

from apps.floor.chrome import hero, ledger, wrap
from apps.floor.runtime import cards


class Visit(Component):
    id = "visit"

    def render(self):
        return wrap(
            *hero(
                kicker="Visit",
                title="Ask, then spend a Cap.",
                lede="Steps, plans, a day, a drawer. Confirm writes the Host.",
            ),
            div(
                *cards(
                    "stepper",
                    "plans",
                    "calendar",
                    "dialog",
                    "sheet",
                    "actionsheet",
                    "contextmenu",
                    "command",
                    "sidebar",
                ),
                className="flex flex-col gap-8",
            ),
            ledger(),
            room="visit",
        )
