"""CTO gate: kit copy refuses without ux-dom; render() is DOM-only.

Hard-deps: HAS_DOM is True on a complete install. Monkeypatching it False
must fail loud at ``uxcompose add`` — no HTML-string fallback.

Isolation: this file never imports ux_channel. No Cap kernel edits.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.kit.catalog import CATALOG
from ux_compose.kit.copy import KitCopyError, copy_component

from tests.feature.morph import (
    KERNEL_SSOT_ID,
    SHELL_BRAND,
    SHELL_ROOT_ID,
    first_id,
)


def _load_kit(stem: str):
    return importlib.import_module(f"ux_compose.kit.{stem}")


def _cls(mod, stem: str):
    return getattr(mod, CATALOG[stem]["name"])


def _assert_kit_fragment(html: str, *, target_id: str) -> None:
    blob = html or ""
    lower = blob.lower()
    assert first_id(blob) == target_id, blob[:400]
    assert SHELL_ROOT_ID not in blob
    assert SHELL_BRAND not in blob
    assert KERNEL_SSOT_ID not in blob
    assert "<html" not in lower
    assert "<head" not in lower
    assert "<body" not in lower
    assert "<!doctype" not in lower
    assert "stylesheet" not in lower


def _serialize(tree) -> str:
    from ux_compose.helpers import _serialize_tree

    if isinstance(tree, str):
        return tree
    return _serialize_tree(tree)


def test_catalog_has_no_html_fallback():
    for stem, meta in CATALOG.items():
        assert not meta.get("html_fallback"), stem


def test_kits_render_dom_trees_as_fragments():
    for stem in ("login", "toast", "actionsheet", "contextmenu", "typeahead", "pullrefresh", "tabs"):
        mod = _load_kit(stem)
        tree = _cls(mod, stem)().render()
        assert not isinstance(tree, str), stem
        html = _serialize(tree)
        _assert_kit_fragment(html, target_id=stem)


def test_copy_refuses_loud_when_has_dom_false(tmp_path, monkeypatch):
    monkeypatch.setattr("ux_compose.kit.copy.HAS_DOM", False)
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    for stem in ("toast", "login", "tabs"):
        with pytest.raises(KitCopyError, match=r"requires ux-dom"):
            copy_component(stem, root=tmp_path)
