"""Wishlist — Heart / unheart is public. The bag (checkout) is a different unit with a Cap.

Ported from the ``commerce_more`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    div,
    h2,
    p,
    header,
    ul,
    li,
    span,
)

from ux_compose.author import act, mark_dirty

CATALOG = {
    "linen": ("Work shirt", 48),
    "oak": ("Serving board", 72),
    "wool": ("Throw", 96),
    "clay": ("Pourer", 38),
}

class Wishlist(Component):
    """Heart / unheart is public. The bag (checkout) is a different unit with a Cap."""

    id = "wishlist"
    ids = RefState(("linen",))
    dirty = MorphState("idle")

    def render(self):
        have = tuple(self.ids or ())
        lis = []
        for sku, (name, price) in CATALOG.items():
            on = sku in have
            lis.append(
                li(
                    span(name, className="bag-line-name"),
                    span(str(price), className="muted"),
                    act(
                        "wishlist.toggle",
                        "Saved" if on else "Save",
                        kind="primary" if on else "ghost",
                        sku=sku,
                    ),
                    id=f"wish-{sku}",
                    className="bag-line" + (" is-on" if on else ""),
                )
            )
        kids = (
            header(
                p("Ids silent · heart public", className="kicker"),
                h2("Wishlist", className="widget-title"),
            ),
            p(f"{len(have)} saved. Saving is not placing.", className="lede"),
            ul(*lis, className="bag-lines"),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def toggle(self, sku: str = ""):
        cur = set(self.ids or ())
        if sku in cur:
            cur.remove(sku)
        elif sku in CATALOG:
            cur.add(sku)
        self.ids = tuple(s for s in CATALOG if s in cur)
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(sku)])


__all__ = ["Wishlist"]
