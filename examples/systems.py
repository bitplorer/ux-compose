"""Systems — chat, notification center, tree, skeleton, consent, theme, stepper, rating, chips, inline edit.

These are the remaining 99% cases: each is still Morph/Ref + @action + update_with.
No new framework verbs.

Run:
  PYTHONPATH=src:. python examples/systems.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.chat import Chat
from ux_compose.components.chips import Chips
from ux_compose.components.consent import Consent
from ux_compose.components.inlineedit import InlineEdit
from ux_compose.components.notifycenter import NotifyCenter
from ux_compose.components.rating import Rating
from ux_compose.components.skeleton import Skeleton
from ux_compose.components.stepper import Stepper
from ux_compose.components.theme import Theme
from ux_compose.components.tree import Tree


def demo() -> None:
    app = App.boot("Systems")
    app.add(
        Chat, NotifyCenter, Tree, Skeleton, Consent, Theme, Stepper, Rating, Chips, InlineEdit
    )
    with app.trust():
        print("chat", app.dispatch("chat.send", text="held"))
    print("tree", app.dispatch("tree.select", key="oak"))
    print("step", app.dispatch("stepper.next"))
    print("rate", app.dispatch("rating.choose", key="five"))


if __name__ == "__main__":
    demo()
