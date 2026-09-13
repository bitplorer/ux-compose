"""Pulseboard composition — L1 import, boot, and key actions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from ux_compose import App

from apps.pulseboard.widgets import (
    BOARD_CLASSES,
    PulseClose,
    PulseKanban,
    PulseKpis,
    PulsePresence,
    PulseTimeline,
)


def test_board_classes_have_unique_ids():
    ids = [cls.id for cls in BOARD_CLASSES]
    assert len(ids) == len(set(ids))
    assert all(str(i).startswith("desk_") for i in ids)


def test_kpis_tick_up_rewrites_refstate():
    app = App.boot("PulseboardKpi", strict_caps=False)
    app.add(PulseKpis)
    app.dispatch("desk_kpis.tick_up")
    inst = dict(app.behavior.components())["desk_kpis"]
    values = {row[0]: row[2] for row in inst.items}
    assert values["mrr"] == "$186.4k"
    html = str(inst.render(shell=False))
    assert "186" in html or "MRR" in html


def test_kanban_move_is_presence_safe():
    app = App.boot("PulseboardKanban", strict_caps=False)
    app.add(PulseKanban)
    app.dispatch("desk_kanban.move", sku="oslo", to="negotiate")
    inst = dict(app.behavior.components())["desk_kanban"]
    assert "oslo" not in inst.qualify
    assert "oslo" in inst.negotiate
    html = str(inst.render())
    assert "deal-oslo" in html


def test_timeline_lane_is_a_name():
    app = App.boot("PulseboardTl", strict_caps=False)
    app.add(PulseTimeline)
    app.dispatch("desk_timeline.choose", key="revenue")
    inst = dict(app.behavior.components())["desk_timeline"]
    assert inst.which == "revenue"


def test_presence_self_is_named():
    app = App.boot("PulseboardPre", strict_caps=False)
    app.add(PulsePresence)
    app.dispatch("desk_presence.set", key="away")
    inst = dict(app.behavior.components())["desk_presence"]
    assert inst.self_state == "away"


def test_wipe_is_cap_gated():
    app = App.boot("PulseboardCap", strict_caps=True)
    app.add(PulseClose)
    with pytest.raises(Exception):
        app.dispatch("desk_close.wipe")
