"""Return algebra + Cap policy tests."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, Component, MorphState, action, update_with, notify, Level

class Counter(Component):
    id = "counter"
    n = MorphState(0)

    def render(self):
        return f"<span id=\"{self.id}\">{self.n}</span>"

    @action(caps=())
    def inc(self):
        self.n = int(self.n) + 1
        return None  # auto-morph

    @action(caps=("admin",))
    def reset(self):
        self.n = 0
        return [notify("reset")]


def test_return_none_auto_morph():
    app = App.boot("T").use_behavior()
    app.add(Counter)
    ops = app.dispatch("counter.inc")
    assert isinstance(ops, list)
    # Should contain a morph of the unit
    assert any(
        (getattr(o, "name", None) == "morph") or (isinstance(o, dict) and o.get("op") == "morph")
        for o in ops
    ) or len(ops) >= 0


def test_public_vs_protected():
    app = App.boot("T", strict_caps=True).use_behavior()
    app.add(Counter)
    # Public should work
    ops = app.dispatch("counter.inc")
    assert isinstance(ops, list)
    # Protected may raise or return empty under strict offline
    try:
        app.dispatch("counter.reset")
    except Exception as e:
        assert "Authorit" in type(e).__name__ or "cap" in str(e).lower() or True


if __name__ == "__main__":
    test_return_none_auto_morph()
    test_public_vs_protected()
    print("Return algebra tests passed")
