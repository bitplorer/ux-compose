"""OfflineBanner — Connectivity is a boolean MorphState. Copy switches. Not a second Document.

Ported from the ``ops`` example module (spec §4); that example stays as the teaching copy.
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

from ux_compose.author import act, mark_dirty, status

class OfflineBanner(Component):
    """Connectivity is a boolean MorphState. Copy switches. Not a second Document."""

    id = "offline"
    online = MorphState(True)

    def render(self):
        on = bool(self.online)
        kids = (
            header(
                p("Bool connectivity", className="kicker"),
                h2("Offline banner", className="widget-title"),
            ),
            p(
                "The house is on the wire."
                if on
                else "Working from the table. Actions queue until the wire returns.",
                className="lede",
            ),
            status("Offline — queued.", kind="ok") if not on else p(""),
            act(
                "offline.flip",
                "Go online" if not on else "Cut the wire",
                kind="primary" if on else "secondary",
            ),
        )
        return div(*kids, id=self.id, className="widget", data_online="1" if on else "0")

    @action(caps=())
    def flip(self):
        self.online = not bool(self.online)
        return update_with(self, extra_ops=[notify("on" if self.online else "off")])


__all__ = ["OfflineBanner"]
