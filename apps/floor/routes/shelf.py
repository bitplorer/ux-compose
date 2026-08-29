"""Page unit — Shelf. Catalog cards from the Host."""

from __future__ import annotations

from ux_compose import Component, div

from apps.floor.chrome import hero, ledger, wrap
from apps.floor.runtime import cards


class Shelf(Component):
    id = "shelf"

    def render(self):
        return wrap(
            *hero(
                kicker="Shelf",
                title="Five objects. Not the stand-in.",
                lede="Walnut mallet, flax apron, merino wrap. The Host holds the list.",
            ),
            div(
                *cards(
                    "lightbox",
                    "carousel",
                    "wishlist",
                    "table",
                    "pagination",
                    "chips",
                    "typeahead",
                    "combobox",
                    "select",
                    "dropdown",
                ),
                className="flex flex-col gap-8",
            ),
            ledger(),
            room="shelf",
        )
