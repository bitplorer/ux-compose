"""GET /signals — Timeline + feed."""

from __future__ import annotations

from ux_compose import Component

from apps.pulseboard.surround import compose


class Signals(Component):
    id = "signals"

    def render(self):
        return compose(room="signals")
