"""Unit: CLI help and unknown command."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main


def test_help_exits_zero():
    assert main(["--help"]) == 0


def test_unknown_command():
    assert main(["not-a-real-cmd"]) == 2
