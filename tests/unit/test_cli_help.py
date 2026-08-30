"""Unit: CLI help and unknown command."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main


def test_help_exits_zero():
    assert main(["--help"]) == 0


def test_help_lists_serve_modes():
    src = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    assert "uxcompose serve dev" in src
    assert "uxcompose serve prod" in src
    assert "--no-css-watch" not in src
    assert "--no-hmr" not in src
    assert "def _start_tailwind_watch" in src
    assert "run_serve_dev" in src
    assert "--one-process" not in src
    assert "def _missing_serve_dev_extras" in src


def test_serve_dev_rejects_one_process(capsys):
    assert main(["serve", "dev", "--one-process"]) == 2
    captured = capsys.readouterr()
    text = captured.out + captured.err
    assert "does not accept" in text


def test_serve_without_mode_exits_2(capsys):
    assert main(["serve"]) == 2
    err = capsys.readouterr()
    text = err.out + err.err
    assert "serve dev" in text
    assert "serve prod" in text


def test_serve_prod_rejects_clock_flags(capsys):
    assert main(["serve", "prod", "--hmr"]) == 2
    assert main(["serve", "prod", "--reload"]) == 2
    assert main(["serve", "prod", "--css-watch"]) == 2
    assert main(["serve", "prod", "--tunnel", "ngrok"]) == 2


def test_unknown_command():
    assert main(["not-a-real-cmd"]) == 2
