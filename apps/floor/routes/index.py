"""Page unit — Desk. Stem Index → /."""

from __future__ import annotations

from ux_compose import Component, div

from apps.floor.chrome import hero, ledger, rooms, wrap
from apps.floor.runtime import cards


class Index(Component):
    id = "index"

    def render(self):
        return wrap(
            *hero(
                kicker="Desk",
                title="The house keeps the books.",
                lede=(
                    "Kit cards are polished once. This floor feeds them from the Host. "
                    "Click a room. The ledger is the proof."
                ),
            ),
            rooms(),
            ledger(),
            div(*cards("kpi", "presence", "toast", "breadcrumb"), className="flex flex-col gap-8"),
            room="desk",
        )
