"""Concurrency: parallel offline dispatches."""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, Component, MorphState, action, Level


class Counter(Component):
    id = "c"
    n = MorphState(0)

    def render(self):
        return f"<span>{int(self.n or 0)}</span>"

    @action(caps=())
    def tick(self):
        self.n = int(self.n or 0) + 1
        return None


def test_parallel_dispatch_does_not_crash():
    app = App.boot("Conc", level=1)
    app.add(Counter)

    def once(_):
        return app.dispatch("c.tick")

    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(once, i) for i in range(40)]
        results = [f.result() for f in as_completed(futs)]
    assert len(results) == 40
    assert app.level >= Level.L1
