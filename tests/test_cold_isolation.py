"""Cold import + Isolation regression — must never pull channel into product surface."""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def test_cold_import_does_not_load_channel():
    boot_before = "ux_compose.wire.boot" in sys.modules
    import ux_compose
    importlib.reload(ux_compose)
    assert hasattr(ux_compose, "App")
    assert hasattr(ux_compose, "Component")
    assert hasattr(ux_compose, "doctor")
    if not boot_before:
        assert "ux_compose.wire.boot" not in sys.modules


def test_init_does_not_import_wire_or_channel():
    init = Path(__file__).resolve().parents[1] / "src" / "ux_compose" / "__init__.py"
    tree = ast.parse(init.read_text(encoding="utf-8"), filename=str(init))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith(("ux_compose.wire", "ux_channel")):
                    hits.append(a.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith(("ux_compose.wire", "ux_channel")):
                hits.append(mod)
    assert hits == [], hits
    text = init.read_text(encoding="utf-8")
    assert "ux_compose.wire" not in text
    assert "import ux_channel" not in text


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
