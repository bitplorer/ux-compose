"""Load / stress: many dispatches (lightweight, CI-friendly)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, Component, MorphState, action


class LoadComp(Component):
    id = "load"
    n = MorphState(0)

    def render(self):
        return str(int(self.n or 0))

    @action(caps=())
    def bump(self):
        self.n = int(self.n or 0) + 1
        return None


def test_stress_1000_dispatches():
    app = App.boot("Load", level=1)
    app.add(LoadComp)
    t0 = time.perf_counter()
    for _ in range(1000):
        app.dispatch("load.bump")
    elapsed = time.perf_counter() - t0
    # Soft budget: should finish under a few seconds offline
    assert elapsed < 15.0
