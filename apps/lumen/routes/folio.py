"""Page unit — Folio. Catalog cards from the Host."""

from __future__ import annotations

from ux_compose import Component, div

from apps.lumen.chrome import hero, wrap
from apps.lumen.runtime import cards


class Folio(Component):
    id = "folio"

    def render(self):
        return wrap(
            *hero(
                kicker="Folio",
                title="Five objects. Not the stand-in.",
                lede="Steel punch, press folio, linen wick. The Host holds the list.",
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
            room="folio",
        )
