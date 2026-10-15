"""ShopView — ShopView

Ported from the ``navigation`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    App,
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
    section,
)

from ux_compose.author import act
from ux_compose import scene, fade, rise

PIECES = {
    "linen": ("Work shirt", "Washed flax, open collar."),
    "oak": ("Serving board", "Quarter-sawn oak, oil finish."),
    "wool": ("Throw", "Undyed merino, blanket stitch."),
}

class ShopView(Component):
    id = "shopview"
    mode = MorphState("list")
    selected = RefState("")

    def render(self):
        if self.mode == "detail":
            name, line = PIECES.get(self.selected, ("Piece", ""))
            kids = (
                header(
                    p("Detail region", className="kicker"),
                    h2(name, className="widget-title"),
                ),
                p(line, className="lede"),
                act("shopview.show_list", "Back to the table", kind="ghost"),
            )
            return section(*kids, id=self.id, className="widget detail")
        rows = [
            li(
                span(name, className="bag-line-name"),
                act("shopview.show_detail", "Open", kind="text", sku=sku),
                id=f"nav-{sku}",
                className="bag-line",
            )
            for sku, (name, _) in PIECES.items()
        ]
        kids = (
            header(
                p("List region", className="kicker"),
                h2("Table", className="widget-title"),
            ),
            ul(*rows, className="bag-lines"),
        )
        return section(*kids, id=self.id, className="widget list")

    def _plan(self, kind: str):
        if kind == "to_detail":
            return (
                scene("to-detail")
                .exit(f"#{self.id}", fade.exit(ms=120))
                .enter(f"#{self.id}", rise.enter(ms=160))
            )
        if kind == "to_list":
            return scene("to-list").enter(f"#{self.id}", fade.enter(ms=140))
        return None

    @action(caps=())
    def show_detail(self, sku: str = ""):
        self.mode = "detail"
        self.selected = sku
        return update_with(
            self, self._plan("to_detail"), extra_ops=[notify(f"detail {sku}")]
        )

    @action(caps=())
    def show_list(self):
        self.mode = "list"
        self.selected = ""
        return update_with(self, self._plan("to_list"), extra_ops=[notify("list")])


__all__ = ["ShopView"]
