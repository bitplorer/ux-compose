"""CompareTray — Up to three skus. Selection is a list — RefState + dirty. Not MorphState(int).

Ported from the ``commerce_more`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
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

class CompareTray(Component):
    """Up to three skus. Selection is a list — RefState + dirty. Not MorphState(int)."""

    id = "compare"
    ids = RefState(("linen", "oak"))
    dirty = MorphState("idle")
    LIMIT = 3

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
                        "compare.toggle",
                        "In tray" if on else "Compare",
                        kind="primary" if on else "ghost",
                        sku=sku,
                    ),
                    id=f"cmp-{sku}",
                    className="bag-line" + (" is-on" if on else ""),
                )
            )
        tray = [
            li(span(CATALOG[s][0], className="bag-line-name"), span(str(CATALOG[s][1]), className="num"), className="bag-line")
            for s in have
        ] or [li("Tray empty.", className="muted")]
        kids = (
            header(
                p("Max three ids", className="kicker"),
                h2("Compare", className="widget-title"),
            ),
            p(f"{len(have)} / {self.LIMIT} in the tray.", className="lede"),
            ul(*lis, className="bag-lines"),
            p("Tray", className="kicker"),
            ul(*tray, className="bag-lines"),
            act("compare.clear", "Clear tray", kind="text"),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def toggle(self, sku: str = ""):
        cur = list(self.ids or ())
        if sku in cur:
            cur = [s for s in cur if s != sku]
        elif sku in CATALOG and len(cur) < self.LIMIT:
            cur.append(sku)
        self.ids = tuple(cur)
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.ids = ()
        mark_dirty(self)
        return update_with(self)


__all__ = ["CompareTray"]
