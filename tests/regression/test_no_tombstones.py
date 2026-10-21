"""Regression: nothing is published, so no tombstones, aliases or private imports.

ux-dom ADR 0004: a removed name is simply gone. An unknown value gets the
one generic error, never a message that teaches the old name.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"
sys.path.insert(0, str(ROOT / "src"))

SPECIALISTS = ("ux_dom", "ux_channel", "ux_behavior", "ux_motion", "cek_host", "cek_surface")


def _private(module: str) -> bool:
    parts = module.split(".")
    if parts[0] not in SPECIALISTS:
        return False
    return "src" in parts[1:] or any(p.startswith("_") and not p.startswith("__") for p in parts)


def test_src_imports_only_public_specialist_modules():
    hits = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            else:
                continue
            hits += [f"{path.relative_to(ROOT)}:{node.lineno} {m}" for m in mods if _private(m)]
    assert hits == []


@pytest.mark.parametrize(
    "module",
    ["ux_dom.dom.src.component", "ux_dom._x", "ux_channel.wire._codec", "ux_dom.dom.src"],
)
def test_private_guard_catches(module):
    assert _private(module)


@pytest.mark.parametrize("module", ["ux_dom.dom", "ux_dom", "importlib._bootstrap", "ux_compose.cli._ports"])
def test_private_guard_ignores(module):
    assert not _private(module)
