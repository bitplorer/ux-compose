"""Presence widgets — Tabs, Accordion, Dropdown, Drawer.

These are open/value MorphState plus an open-mint action.
No Cap unless the verb spends money, deletes, or changes identity.

Stable ids on panels (``#tab-cut``) let Motion stagger later without rewrite.

Run:
  PYTHONPATH=src:. python examples/presence.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.accordion import Accordion
from ux_compose.components.drawer import Drawer
from ux_compose.components.dropdown import Dropdown
from ux_compose.components.tabs import Tabs

TABS = (
    ("cut", "Cut", "The pattern book. Tabs morph one region; they do not remount the page."),
    ("make", "Make", "Actions stay on the same Component. Motion, when attached, is a Plan."),
    ("keep", "Keep", "Caps stay off this control. Opening a tab is not an authority event."),
)


def demo() -> None:
    app = App.boot("Chrome")
    app.add(Tabs, Accordion, Dropdown, Drawer)
    print("tabs", app.dispatch("tabs.select", tab="make"))
    print("acc", app.dispatch("accordion.toggle", key="law"))
    print("drop", app.dispatch("dropdown.choose", key="oak"))
    print("drawer", app.dispatch("sheet.open_sheet"))


if __name__ == "__main__":
    demo()
