"""Unit: CLI help and unknown command."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main


def test_help_exits_zero():
    assert main(["--help"]) == 0


def test_help_lists_css_watch_clock():
    src = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    assert "--css-watch" in src
    assert "--no-css-watch" not in src
    assert "def _start_tailwind_watch" in src


def test_unknown_command():
    assert main(["not-a-real-cmd"]) == 2
