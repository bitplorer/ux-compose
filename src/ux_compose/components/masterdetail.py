"""MasterDetail — Split: list selection MorphState, body from RefState catalog.

Ported from the ``navigation`` example module (spec §4); this module is canonical and the example imports it.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    action,
    update_with,
    div,
    h2,
    p,
    header,
    section,
)

from ux_compose.author import act

PIECES = {
    "linen": ("Work shirt", "Washed flax, open collar."),
    "oak": ("Serving board", "Quarter-sawn oak, oil finish."),
    "wool": ("Throw", "Undyed merino, blanket stitch."),
}

class MasterDetail(Component):
    """Split: list selection MorphState, body from RefState catalog."""

    id = "split"
    selected = MorphState("linen")

    def render(self):
        sel = str(self.selected or "linen")
        name, line = PIECES.get(sel, ("", ""))
        nav = [
            act(
                "split.select",
                n,
                kind="primary" if s == sel else "ghost",
                sku=s,
            )
            for s, (n, _) in PIECES.items()
        ]
        kids = (
            header(
                p("Master / detail", className="kicker"),
                h2("Split", className="widget-title"),
            ),
            div(*nav, className="seg"),
            section(
                h2(name),
                p(line, className="lede"),
                id=f"split-{sel}",
                className="tab-panel",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def select(self, sku: str = "linen"):
        self.selected = sku
        return update_with(self)


__all__ = ["MasterDetail"]
