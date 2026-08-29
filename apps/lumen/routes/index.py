"""Page unit — Hall. Stem Index → /."""

from __future__ import annotations

from ux_compose import Component, div

from apps.lumen.chrome import hero, rooms, wrap
from apps.lumen.runtime import cards


class Index(Component):
    id = "index"

    def render(self):
        return wrap(
            *hero(
                kicker="Hall",
                title="The press keeps the books.",
                lede=(
                    "Kit cards are polished once. Lumen feeds them from the Host. "
                    "Clock A serves the page. Channel morphs the card. There is no app JavaScript."
                ),
            ),
            rooms(),
            div(*cards("kpi", "presence", "toast", "breadcrumb"), className="flex flex-col gap-8"),
            room="hall",
        )
