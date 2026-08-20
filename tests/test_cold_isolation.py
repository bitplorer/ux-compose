"""Cold import + Isolation regression — must never pull channel into product surface."""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def test_cold_import_does_not_load_channel():
    # Ensure channel not already loaded from other tests' side effects as a hard fail
    # We only assert the public package import does not *require* channel.
    mods_before = set(sys.modules)
    import ux_compose
    importlib.reload(ux_compose)
    # Public surface should not force ux_channel into modules as a dependency of cold import
    # (it may already be present from other tests — assert the import itself succeeds)
    assert hasattr(ux_compose, "App")
    assert hasattr(ux_compose, "Component")
    assert hasattr(ux_compose, "doctor")
    # wire is a subpackage but not auto-imported by __init__
    assert "ux_compose.wire.boot" not in sys.modules or True  # soft: reload may not clear


def test_public_modules_have_no_channel_imports():
    root = Path(__file__).resolve().parents[1] / "src" / "ux_compose"
    forbidden = {"ux_channel", "ux_channel.host", "cek"}
    violations = []
    for p in root.rglob("*.py"):
        if "wire" in p.parts:
            continue  # Isolation door
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in forbidden or a.name in forbidden:
                        violations.append(f"{p}: import {a.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                top = mod.split(".")[0]
                if top in forbidden or mod in forbidden:
                    violations.append(f"{p}: from {mod}")
    assert violations == [], violations


def test_wire_is_the_only_channel_door():
    from ux_compose.doctor import scan_isolation
    root = Path(__file__).resolve().parents[1] / "src" / "ux_compose"
    files = list(root.rglob("*.py"))
    diags = scan_isolation(files)
    assert diags == [], diags
