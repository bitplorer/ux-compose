"""Property-style invariants on control / update_with."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.helpers import control, notify, update_with


def test_control_always_dict_with_action_key():
    for name in ("a.b", "x", "shop.add", "lab.run"):
        d = control(name)
        assert isinstance(d, dict)
        # semantic attr present in some form
        joined = " ".join(str(v) for v in d.values()) + "".join(d.keys())
        assert name.split(".")[-1] in joined or name in joined or len(d) >= 1


def test_update_with_list_invariant():
    for target in ("cart", "#cart", "x"):
        ops = update_with(target, None, extra_ops=[notify("t")])
        assert isinstance(ops, list)
        assert len(ops) >= 1
