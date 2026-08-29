"""Page unit — Stone. Flow and overlays from the Host."""

from __future__ import annotations

from ux_compose import Component, div

from apps.lumen.chrome import hero, wrap
from apps.lumen.runtime import cards


class Stone(Component):
    id = "stone"

    def render(self):
        return wrap(
            *hero(
                kicker="Stone",
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
            room="stone",
        )
