"""ux-dom's ``runtime/`` alias module is going away (ux-dom F-18 follow-up).

ux-compose imports the Document plugins from top-level ``ux_dom`` instead, so
it keeps working on both the pinned ux-dom and a ux-dom without ``runtime/``.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN = ("src", "apps", "examples")


def _hits() -> list[str]:
    hits: list[str] = []
    for top in SCAN:
        for py in sorted((ROOT / top).rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
            for node in ast.walk(tree):
                mods: list[str] = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module]
                elif isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                for m in mods:
                    if m == "ux_dom.runtime" or m.startswith("ux_dom.runtime."):
                        hits.append(f"{py.relative_to(ROOT)}:{node.lineno}")
            if "ux_dom.runtime import" in py.read_text(encoding="utf-8"):
                hits.append(f"{py.relative_to(ROOT)} (generated source)")
    return hits


def test_no_ux_dom_runtime_imports():
    assert _hits() == []


def test_top_level_ux_dom_exports_document_plugins():
    import ux_dom
    from ux_dom.plugins.control import HtmxControl
    from ux_dom.plugins.csp import Csp
    from ux_dom.plugins.runtime import UxChannelRuntime, XElementRuntime

    assert ux_dom.XElement is XElementRuntime
    assert ux_dom.Htmx is HtmxControl
    assert ux_dom.Csp is Csp
    assert ux_dom.Channel is UxChannelRuntime
