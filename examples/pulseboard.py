"""Pulseboard — offline L1 dispatch of the live desk units.

The product host is ``apps/pulseboard`` (``make pulseboard``).
Atelier serves the same units at ``/pulseboard``.

Run:
  PYTHONPATH=src:. python examples/pulseboard.py
"""
from __future__ import annotations

from ux_compose import App

from apps.pulseboard.widgets import (
    PulseClose,
    PulseKanban,
    PulseKpis,
    PulsePresence,
    PulseTimeline,
)


def demo() -> None:
    app = App.boot("PulseboardDemo", strict_caps=False)
    app.add(PulseKpis, PulseKanban, PulseTimeline, PulsePresence, PulseClose)
    print("kpi", app.dispatch("desk_kpis.tick_up"))
    print("move", app.dispatch("desk_kanban.move", sku="oslo", to="negotiate"))
    print("lane", app.dispatch("desk_timeline.choose", key="revenue"))
    print("here", app.dispatch("desk_presence.set", key="away"))
    strict = App.boot("PulseboardCaps", strict_caps=True)
    strict.add(PulseClose)
    try:
        strict.dispatch("desk_close.wipe")
        print("UNEXPECTED")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
