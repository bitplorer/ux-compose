"""Attach notes are visible. The step-down itself still does not raise."""
from __future__ import annotations

from ux_compose.app import App
from ux_compose.degrade import AttachNotes, attach_notes, clear, format_report, note, using


def setup_function():
    clear()


def test_note_records_and_never_raises():
    ev = note("use_channel", "L2", "ux-channel missing", level_kept=1)
    assert ev.door == "use_channel"
    assert ev.level_kept == 1
    assert attach_notes()[0] is ev
    lines = format_report()
    assert lines and "use_channel" in lines[0]


def test_clear_is_test_only_reset():
    note("use_motion", "L3", "absent")
    clear()
    assert attach_notes() == ()


def test_two_notebooks_do_not_leak():
    a = AttachNotes()
    b = AttachNotes()
    with using(a):
        note("use_channel", "L2", "missing", level_kept=1)
    with using(b):
        note("use_motion", "L3", "absent", level_kept=1)
    assert [e.door for e in a.snapshot()] == ["use_channel"]
    assert [e.door for e in b.snapshot()] == ["use_motion"]
    doors = [e.door for e in attach_notes()]
    assert "use_channel" in doors
    assert "use_motion" in doors


def test_two_apps_do_not_leak():
    a = App("A")
    b = App("B")
    a._note("use_channel", "L2", "missing", level_kept=1)
    b._note("use_motion", "L3", "absent", level_kept=1)
    assert [e.door for e in a.attach_notes] == ["use_channel"]
    assert [e.door for e in b.attach_notes] == ["use_motion"]
    doors = [e.door for e in attach_notes()]
    assert "use_channel" in doors
    assert "use_motion" in doors
