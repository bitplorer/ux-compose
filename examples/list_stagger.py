"""
List + filter pattern — elevated surface.

Demonstrates:
- MorphState list projection (dirty → morph the list unit)
- RefState for silent filter string
- Public add / filter actions
- update_with for ordered morph (+ optional future stagger Plan)
- Progressive Superpower: same class at every level

Run:
  PYTHONPATH=src python examples/list_stagger.py
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


class ItemList(Component):
    id = "items"
    items = MorphState(None)  # list[str]
    filter = RefState("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.items is None:
            self.items = []

    def render(self):
        q = (self.filter or "").lower()
        visible = [x for x in (self.items or []) if q in x.lower()]
        rows = "".join(f"<li class='item'>{x}</li>" for x in visible)
        attrs = control("add", text="new")
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return (
            f'<div id="{self.id}">'
            f"<ul>{rows or '<li class=\"empty\">No items</li>'}</ul>"
            f"<button {attr_str}>Add</button>"
            f"</div>"
        )

    @action(caps=())
    def add(self, text: str = "item"):
        cur = list(self.items or [])
        cur.append(text)
        self.items = cur
        # When Motion is present, authors can pass a stagger Plan into update_with
        return update_with(self, extra_ops=[notify(f"Added {text}")])

    @action(caps=())
    def set_filter(self, q: str = ""):
        self.filter = q
        # RefState alone does not dirty; force morph so filtered view paints
        return update_with(self)


if __name__ == "__main__":
    app = App.boot("Shop", strict_caps=False)
    app.add(ItemList)

    print("Level:", int(app.level), f"({app.level.label})")
    print("Add:", app.dispatch("items.add", text="tee"))
    print("Add:", app.dispatch("items.add", text="hoodie"))
    print("Filter:", app.dispatch("items.set_filter", q="tee"))
