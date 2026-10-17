"""OverflowMenu — Kebab / ⋯ menu. Presence is MorphState. Chosen verb is a public dispatch.

Ported from the ``shell`` example module (spec §4); that example stays as the teaching copy.
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
    span,
)

from ux_compose.author import act, mark_dirty

ROUTES = (
    ("table", "Table", "The working surface. Lists morph in place."),
    ("bag", "Bag", "Cart lives here. Checkout is a Cap on that unit."),
    ("inbox", "Inbox", "Badge is a magnitude — dirty + RefState, not MorphState(int)."),
    ("settings", "Settings", "Locale / density are names. Wipe is authority."),
)

class OverflowMenu(Component):
    """Kebab / ⋯ menu. Presence is MorphState. Chosen verb is a public dispatch.

    Destructive items inside an overflow still take a Cap on *their* action,
    not on opening the menu.
    """

    id = "overflow"
    open = MorphState(False)
    last = RefState("")
    dirty = MorphState("idle")

    def render(self):
        last = str(self.last or "—")
        menu = (
            div(
                act("overflow.choose", "Duplicate", kind="text", key="duplicate"),
                act("overflow.choose", "Move to Keep", kind="text", key="move"),
                act("overflow.choose", "Archive (Cap)", kind="text", key="archive"),
                className="menu",
                role="menu",
            )
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Open is MorphState · last is silent", className="kicker"),
                h2("Overflow", className="widget-title"),
            ),
            p(f"Last verb · {last}", className="muted"),
            div(
                act("overflow.toggle", "⋯", kind="secondary"),
                menu,
                className="dropdown-wrap",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def choose(self, key: str = ""):
        """Archive is demonstrated as a *named* choice here.

        The real archive verb lives on the table unit with caps records.archive.
        Overflow records intent; it does not spend authority.
        """
        self.last = key
        self.open = False
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(key or "none")])


__all__ = ["OverflowMenu"]
