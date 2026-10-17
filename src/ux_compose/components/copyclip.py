"""CopyClip — Copied is a boolean MorphState. Payload is RefState (not re-painted as MorphState).

Ported from the ``ops`` example module (spec §4); that example stays as the teaching copy.
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
)

from ux_compose.author import act, mark_dirty, status

class CopyClip(Component):
    """Copied is a boolean MorphState. Payload is RefState (not re-painted as MorphState)."""

    id = "copyclip"
    copied = MorphState(False)
    text = RefState("atelier://piece/linen")
    dirty = MorphState("idle")

    def render(self):
        kids = (
            header(
                p("Bool copied · text silent", className="kicker"),
                h2("Copy", className="widget-title"),
            ),
            p(str(self.text or ""), className="lede"),
            status("Copied to the clipboard stand-in.", kind="ok") if self.copied else p(""),
            div(
                act("copyclip.copy", "Copy link", kind="primary"),
                act("copyclip.reset", "Clear flag", kind="text"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def copy(self):
        self.copied = True
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("copied")])

    @action(caps=())
    def reset(self):
        self.copied = False
        return update_with(self)


__all__ = ["CopyClip"]
