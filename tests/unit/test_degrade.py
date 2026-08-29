"""Degrade events are visible. Degrade itself still does not raise."""
from __future__ import annotations

from ux_compose.degrade import clear, degrades, format_report, note


def setup_function():
    clear()


def test_note_records_and_never_raises():
    ev = note("use_channel", "L2", "ux-channel missing", level_kept=1)
    assert ev.door == "use_channel"
    assert ev.level_kept == 1
    assert degrades()[0] is ev
    lines = format_report()
    assert lines and "use_channel" in lines[0]


def test_clear_is_test_only_reset():
    note("use_motion", "L3", "absent")
    clear()
    assert degrades() == ()
