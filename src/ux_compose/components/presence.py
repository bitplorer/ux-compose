"""Presence — Self status is a name. Peer list is RefState. Typing would be a bool on chat.

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

class Presence(Component):
    """Self status is a name. Peer list is RefState. Typing would be a bool on chat."""

    id = "presence"
    self_state = MorphState("here")
    peers = RefState(("Noor · here", "Atelier · away"))
    dirty = MorphState("idle")

    def render(self):
        me = str(self.self_state or "here")
        lis = [li(x, className="hit") for x in (self.peers or ())]
        kids = (
            header(
                p("Self named · peers silent", className="kicker"),
                h2("Presence", className="widget-title"),
            ),
            p(
                span("You", className="bag-line-name"),
                span(me, className="chip" + (" is-on" if me == "here" else "")),
                className="counter-face",
            ),
            ul(*lis, className="hit-list"),
            div(
                act("presence.set", "Here", kind="primary" if me == "here" else "ghost", key="here"),
                act("presence.set", "Away", kind="primary" if me == "away" else "ghost", key="away"),
                className="seg",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def set(self, key: str = "here"):
        self.self_state = key if key in {"here", "away"} else "here"
        return update_with(self)


__all__ = ["Presence"]
