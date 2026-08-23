"""Regression: product lifecycle stays on uxcompose; HMR not Document API."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main
from ux_compose import hmr


def test_cli_has_product_commands_only_in_help(capsys):
    main(["--help"])
    out = capsys.readouterr().out
    assert "create-app" in out
    assert "serve" in out
    assert "deploy" in out
    assert "doctor" in out


def test_hmr_is_delivery_module():
    assert hasattr(hmr, "attach_hmr")
    assert hasattr(hmr, "client_script_tag")
    # HMR path is compose-owned, not a Document.use symbol
    assert hmr.HMR_PATH.startswith("/__uxcompose")
