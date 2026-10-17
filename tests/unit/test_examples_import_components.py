"""components/ is the single source of every component class (spec §4).

examples/ are thin usage demos. They import component classes from
``ux_compose.components`` and never define a class with a component's name.
"""
from __future__ import annotations

import ast
from pathlib import Path

import ux_compose.components as kit

ROOT = Path(__file__).resolve().parents[2]
COMPONENTS = ROOT / "src" / "ux_compose" / "components"


def _component_classes():
    names = {n for n in kit.__all__ if isinstance(getattr(kit, n), type)}
    for py in COMPONENTS.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        names |= {n.name for n in tree.body if isinstance(n, ast.ClassDef)}
    return names


KIT_CLASSES = _component_classes()


def _redefinitions():
    hits = []
    for py in sorted((ROOT / "examples").rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in KIT_CLASSES:
                hits.append(f"{py.relative_to(ROOT)}:{node.lineno} {node.name}")
    return hits


def test_examples_never_redefine_a_component_class():
    assert _redefinitions() == []


def test_catalog_component_classes_come_from_components():
    import sys

    sys.path.insert(0, str(ROOT))
    from examples.catalog import all_components

    for cls in all_components():
        if cls.__module__.startswith("apps."):
            continue  # product apps own their classes (e.g. atelier_shop)
        if cls.__name__ in KIT_CLASSES:
            assert cls.__module__.startswith("ux_compose.components"), (
                cls.__name__,
                cls.__module__,
            )
