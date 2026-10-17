"""The frame — app frame, breadcrumbs, bottom nav, popover, overflow.

99% of product *frames* are the same two MorphState keys:

    current / open / collapsed   qualitative MorphState
    last-clicked payload         RefState + dirty (if a magnitude or list)

A shell is **not** a second Document. One HTML shell, many units. Opening a
route is public. Spending money / deleting / changing identity is a Cap on
the *destination* Component, never on the nav.

Stable ids (``#shell-table``, ``#crumb-linen``) survive morph so Motion can
later address the surviving region with zero rewrite.

Run:
  PYTHONPATH=src:. python examples/shell.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.appshell import AppShell
from ux_compose.components.bottomnav import BottomNav
from ux_compose.components.breadcrumbs import Breadcrumbs
from ux_compose.components.overflowmenu import OverflowMenu
from ux_compose.components.popover import Popover


ROUTES = (
    ("table", "Table", "The working surface. Lists morph in place."),
    ("bag", "Bag", "Cart lives here. Checkout is a Cap on that unit."),
    ("inbox", "Inbox", "Badge is a magnitude — dirty + RefState, not MorphState(int)."),
    ("settings", "Settings", "Locale / density are names. Wipe is authority."),
)


def demo() -> None:
    app = App.boot("Shell")
    app.add(AppShell, Breadcrumbs, BottomNav, Popover, OverflowMenu)
    print("go", app.dispatch("appshell.go", key="bag"))
    print("crumb", app.dispatch("crumbs.go", key="linen"))
    print("nav", app.dispatch("bottomnav.select", key="search"))
    print("pop", app.dispatch("popover.toggle"))
    print("over", app.dispatch("overflow.choose", key="duplicate"))


if __name__ == "__main__":
    demo()
