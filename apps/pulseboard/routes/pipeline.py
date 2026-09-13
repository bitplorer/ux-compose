"""GET /pipeline — Kanban focus."""

from __future__ import annotations

from ux_compose import Component

from apps.pulseboard.chrome import compose


class Pipeline(Component):
    id = "pipeline"

    def render(self):
        return compose(room="pipeline")
