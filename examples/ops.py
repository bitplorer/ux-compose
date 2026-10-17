"""Ops / product systems — calendar, progress, copy, settings, offline, presence, KPI, shortcuts.

The last mile of the 99%: operational presence every working house grows.

    calendar     month is a name; day magnitude in RefState; book is a Cap
    progress     pct RefState; phase named MorphState
    copy         copied bool MorphState; text RefState
    settings     density / motion names; wipe is a Cap
    offline      online bool
    presence     peers list silent; self named
    KPI          values silent; dirty MorphState dirties
    shortcuts    same shape as the command palette

No new framework verbs. Morph / Ref / @action / update_with.

Run:
  PYTHONPATH=src:. python examples/ops.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.calendar import Calendar
from ux_compose.components.copyclip import CopyClip
from ux_compose.components.kpistrip import KpiStrip
from ux_compose.components.offlinebanner import OfflineBanner
from ux_compose.components.presence import Presence
from ux_compose.components.progressmeter import ProgressMeter
from ux_compose.components.settings import Settings
from ux_compose.components.shortcuts import Shortcuts


def demo() -> None:
    app = App.boot("Ops")
    app.add(
        Calendar,
        ProgressMeter,
        CopyClip,
        Settings,
        OfflineBanner,
        Presence,
        KpiStrip,
        Shortcuts,
    )
    print("cal", app.dispatch("calendar.pick", day="2026-08-21"))
    print("prog", app.dispatch("progress.bump"))
    print("copy", app.dispatch("copyclip.copy"))
    print("set", app.dispatch("settings.set_density", key="compact"))
    print("off", app.dispatch("offline.flip"))
    print("pre", app.dispatch("presence.set", key="away"))
    print("kpi", app.dispatch("kpi.tick_up"))
    print("keys", app.dispatch("shortcuts.open_keys"))
    strict = App.boot("Ops", strict_caps=True)
    strict.add(Settings)
    try:
        strict.dispatch("settings.wipe")
        print("UNEXPECTED wipe")
    except Exception as exc:
        print("Cap Law wipe:", type(exc).__name__)


if __name__ == "__main__":
    demo()
