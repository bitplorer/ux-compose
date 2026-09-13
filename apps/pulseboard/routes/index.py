"""GET / — Overview command center. Fragment; host wraps Document."""

from __future__ import annotations

from ux_compose import Component, MorphState, action, update_with

from apps.pulseboard.chrome import compose


class Index(Component):
    id = "index"
    ready = MorphState(True)

    def render(self):
        return compose(room="overview")

    @action(caps=())
    def poke(self):
        self.ready = not bool(self.ready)
        return update_with(self)
