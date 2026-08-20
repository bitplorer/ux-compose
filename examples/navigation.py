"""Navigation — region swap, master/detail, shared-element seat.

The page does not remount. One Component owns ``mode``. Detail payload is
RefState. Motion Plan (when present) is exit/enter recipes with no html=.

Run:
  PYTHONPATH=src:. python examples/navigation.py
"""
from __future__ import annotations

from ux_compose import (
    HAS_DOM,
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

from examples._common import act, scene, fade, rise

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
            if HAS_DOM:
                return section(*kids, id=self.id, className="widget detail")
            return f'<section id="{self.id}">{name}</section>'
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
        if HAS_DOM:
            return section(*kids, id=self.id, className="widget list")
        return f'<section id="{self.id}">list</section>'

    def _plan(self, kind: str):
        if scene is None:
            return None
        try:
            if kind == "to_detail" and fade and rise:
                return (
                    scene("to-detail")
                    .exit(f"#{self.id}", fade.exit(ms=120))
                    .enter(f"#{self.id}", rise.enter(ms=160))
                )
            if kind == "to_list" and fade:
                return scene("to-list").enter(f"#{self.id}", fade.enter(ms=140))
        except Exception:
            return None
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
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{sel}</div>'

    @action(caps=())
    def select(self, sku: str = "linen"):
        self.selected = sku
        return update_with(self)


def demo() -> None:
    app = App.boot("Nav", strict_caps=False)
    app.add(ShopView, MasterDetail)
    print("detail", app.dispatch("shopview.show_detail", sku="oak"))
    print("list", app.dispatch("shopview.show_list"))
    print("split", app.dispatch("split.select", sku="wool"))


if __name__ == "__main__":
    demo()
