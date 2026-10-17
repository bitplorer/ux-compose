"""AppShell — Sidebar + current region. Collapsed is a boolean MorphState (legal live).

Ported from the ``shell`` example module (spec §4); that example stays as the teaching copy.
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
    nav,
    section,
    span,
    ul,
    li,
)

from ux_compose.author import act, mark_dirty

ROUTES = (
    ("table", "Table", "The working surface. Lists morph in place."),
    ("bag", "Bag", "Cart lives here. Checkout is a Cap on that unit."),
    ("inbox", "Inbox", "Badge is a magnitude — dirty + RefState, not MorphState(int)."),
    ("settings", "Settings", "Locale / density are names. Wipe is authority."),
)

class AppShell(Component):
    """Sidebar + current region. Collapsed is a boolean MorphState (legal live).

    Why not four Components? Because the verbs (go, collapse) belong to one
    unit. Split only when a region grows its own protected verbs.
    """

    id = "appshell"
    current = MorphState("table")
    collapsed = MorphState(False)

    def render(self):
        cur = str(self.current or "table")
        copy = {k: (title, body) for k, title, body in ROUTES}
        title, body = copy.get(cur, copy["table"])
        links = [
            act(
                "appshell.go",
                label,
                kind="primary" if key == cur else "ghost",
                key=key,
            )
            for key, label, _ in ROUTES
        ]
        kids = (
            header(
                p("Named route · bool collapsed", className="kicker"),
                h2("App shell", className="widget-title"),
            ),
            p(
                "Press a region. The page does not remount. Caps stay off this control.",
                className="lede",
            ),
            div(
                nav(*links, className="seg", aria_label="Primary"),
                act(
                    "appshell.toggle",
                    "Expand rail" if self.collapsed else "Collapse rail",
                    kind="text",
                ),
                className="shell-rail" + (" is-collapsed" if self.collapsed else ""),
            ),
            section(
                h2(title),
                p(body, className="lede"),
                p(
                    "Rail is " + ("narrow." if self.collapsed else "open."),
                    className="muted",
                ),
                id=f"shell-{cur}",
                className="tab-panel",
            ),
        )
        return div(
            *kids,
            id=self.id,
            className="widget",
            data_current=cur,
            data_collapsed="1" if self.collapsed else "0",
        )

    @action(caps=())
    def go(self, key: str = "table"):
        if key not in {k for k, _, _ in ROUTES}:
            key = "table"
        self.current = key
        return update_with(self, extra_ops=[notify(key)])

    @action(caps=())
    def toggle(self):
        self.collapsed = not bool(self.collapsed)
        return update_with(self)


__all__ = ["AppShell"]
