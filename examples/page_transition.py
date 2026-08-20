"""
Page / region transition sketch — elevated surface.

Demonstrates:
- Two region Components (list view + detail view)
- MorphState for which view is active
- update_with for morph; when Motion is present, authors pass a scene Plan
- XOR-safe path: morph the region unit, Plan carries enter/exit recipes only (no html=)

Offline L1: plain morph between views.
L3 (when ux-motion installed): same actions can attach scene(...).exit().enter().play()
via update_with without rewriting Component code.

Run:
  PYTHONPATH=src python examples/page_transition.py
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
    control,
)

try:
    from ux_compose import scene, fade, rise
except Exception:
    scene = fade = rise = None


class ShopView(Component):
    id = "shop-view"
    mode = MorphState("list")   # "list" | "detail"
    selected = RefState("")

    def render(self):
        if self.mode == "detail":
            back = control("show_list")
            back_s = " ".join(f'{k}="{v}"' for k, v in back.items())
            return (
                f'<section id="{self.id}" class="detail">'
                f"<h1>{self.selected or 'Item'}</h1>"
                f"<button {back_s}>Back</button>"
                f"</section>"
            )
        # list
        go = control("show_detail", sku="tee")
        go_s = " ".join(f'{k}="{v}"' for k, v in go.items())
        return (
            f'<section id="{self.id}" class="list">'
            f"<h1>Products</h1>"
            f"<button {go_s}>Tee →</button>"
            f"</section>"
        )

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
        return update_with(self, self._plan("to_detail"), extra_ops=[notify(f"Detail {sku}")])

    @action(caps=())
    def show_list(self):
        self.mode = "list"
        self.selected = ""
        return update_with(self, self._plan("to_list"), extra_ops=[notify("List")])


if __name__ == "__main__":
    app = App.boot("Shop", strict_caps=False)
    app.add(ShopView)

    print("Level:", int(app.level), f"({app.level.label})")
    print("→ detail:", app.dispatch("shop-view.show_detail", sku="tee"))
    print("→ list:", app.dispatch("shop-view.show_list"))
    print("Motion available:", scene is not None)
