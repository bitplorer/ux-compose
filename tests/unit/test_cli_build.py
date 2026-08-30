"""Unit: product build CLI owns the Tailwind resolver."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main
from ux_compose.cli_build import find_product_root, run_product_build
from ux_compose.scaffold import create_app


def test_help_lists_build(capsys):
    assert main(["--help"]) == 0
    out = capsys.readouterr().out
    assert "uxcompose build" in out
    assert "create-app → serve dev → build → deploy" in out
    assert "CSS minify: uxcompose build" in out
    assert "ux_dom.cli.tailwind" not in out
