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
    assert "uxcompose serve restart-channel" in src
    assert "--reload-channel" not in src
    assert "--no-css-watch" not in src
    assert "--no-hmr" not in src
    assert "def start_tailwind_watch" not in src
    tw = (ROOT / "src" / "ux_compose" / "tailwind.py").read_text(encoding="utf-8")
    serve = (ROOT / "src" / "ux_compose" / "serve_dev.py").read_text(encoding="utf-8")
    assert "def start_tailwind_watch" in tw
    assert "start_tailwind_watch" not in src
    assert "start_tailwind_watch" in serve
    assert "start_css_watcher:" not in src
    assert "start_css_watcher:" not in serve
    assert "start_css_watcher=" in src
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
    assert "restart-channel" in text


def test_serve_prod_rejects_clock_flags(capsys):
    assert main(["serve", "prod", "--hmr"]) == 2
    assert main(["serve", "prod", "--reload"]) == 2
    assert main(["serve", "prod", "--css-watch"]) == 2
    assert main(["serve", "prod", "--tunnel", "ngrok"]) == 2


def test_unknown_command():
    assert main(["not-a-real-cmd"]) == 2


def test_create_argv_is_unknown(capsys):
    """Leftover alias. Frozen verb is create-app."""
    assert main(["create", "myapp"]) == 2
    text = capsys.readouterr().out + capsys.readouterr().err
    src = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    assert 'cmd in ("create-app", "create")' not in src
    assert 'cmd == "create-app"' in src


def test_serve_mode_synonyms_fail_closed(capsys):
    """Leftover aliases. Frozen modes are dev / prod / restart-channel."""
    assert main(["serve", "development"]) == 2
    assert main(["serve", "production"]) == 2
    assert main(["serve", "restart_channel"]) == 2
    src = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    assert '"development": "dev"' not in src
    assert '"production": "prod"' not in src
    assert '"restart_channel": "restart-channel"' not in src
    assert "argv ``development``" in src


def test_restart_channel_without_pidfile_fails_closed(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["serve", "restart-channel"])
    captured = capsys.readouterr()
    text = captured.out + captured.err
    assert code == 1
    assert "no running serve dev" in text
    assert "--reload-channel" not in text


def test_restart_channel_rejects_flags(capsys):
    assert main(["serve", "restart-channel", "--reload-channel"]) == 2
    captured = capsys.readouterr()
    text = captured.out + captured.err
    assert "does not accept" in text
