"""Toggle — Boolean MorphState is qualitative — legal on the session plane.

Ported from the ``foundation`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    App,
    Component,
    MorphState,
    RefState,
    action,
    doctor,
    notify,
    update_with,
    div,
    h2,
    p,
    span,
    header,
)

from ux_compose.author import act, optional_plan, mark_dirty

class Toggle(Component):
    """Boolean MorphState is qualitative — legal on the session plane."""

    id = "toggle"
    on = MorphState(False)

    def render(self):
        on = bool(self.on)
        label = "On" if on else "Off"
        kids = (
            header(
                p("Boolean MorphState", className="kicker"),
                h2("Quiet hours", className="widget-title"),
            ),
            p(
                "The house hushes notifications after dusk."
                if on
                else "Notifications reach the table.",
                className="lede",
            ),
            act(
                "toggle.flip",
                f"Turn {('off' if on else 'on')}",
                kind="primary" if not on else "ghost",
            ),
        )
        return div(
            *kids,
            id=self.id,
            className="widget",
            data_on="1" if on else "0",
            aria_pressed="true" if on else "false",
        )

    @action(caps=())
    def flip(self):
        self.on = not bool(self.on)
        return update_with(self, extra_ops=[notify("on" if self.on else "off")])


__all__ = ["Toggle"]
