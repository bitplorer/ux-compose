"""Page unit — Desk room. Stem matches class name."""

from __future__ import annotations

from ux_compose import Component, MorphState, action, div, update_with

from ..chrome import hero
from ..theme import CARD


class Desk(Component):
    id = "desk"
    lit = MorphState(False)

    def render(self):
        return div(
            *hero(
                kicker="Desk",
                title="The house keeps a quiet list.",
                lede="Companions mount beside this unit: rail, tabs, pull, accordion, palette.",
            ),
            id=self.id,
            className=CARD,
        )

    @action(caps=())
    def poke(self):
        self.lit = not bool(self.lit)
        return update_with(self)
