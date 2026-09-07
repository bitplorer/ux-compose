"""CTO gate: kit import + render() must not TypeError when HAS_DOM=False.

Toast / Login / Wave-1 (actionsheet, contextmenu, typeahead, pullrefresh)
use an HTML-string fragment fallback so Progressive Superpower is real on
Py3.13. Other kits fail at add/render with ``requires ux-dom (Py≥3.14)``.

Isolation: this file never imports ux_channel. No Cap kernel edits.
"""
from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
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

_FALLBACK = ("login", "toast", "actionsheet", "contextmenu", "typeahead", "pullrefresh")
_DOM_ONLY = tuple(sorted(k for k in CATALOG if k not in _FALLBACK))


@contextmanager
def _force_html(mod):
    """Exercise the string path even when ux-dom is installed (Py3.14 CI)."""
    prev = getattr(mod, "HAS_DOM", None)
    mod.HAS_DOM = False
    try:
        yield
    finally:
        if prev is None:
            delattr(mod, "HAS_DOM")
        else:
            mod.HAS_DOM = prev


def _load_kit(stem: str):
    return importlib.import_module(f"ux_compose.kit.{stem}")


def _cls(mod, stem: str):
    return getattr(mod, CATALOG[stem]["name"])


def _assert_kit_fragment(html: str, *, target_id: str) -> None:
    """Fragment law for morphing kits: root id is the unit, never a document.

    Child ids may share a prefix (``toast-1``, ``login-form``), so the hello
    helper's exact ``id="X"`` count does not apply.
    """
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


def _render_html(stem: str):
    mod = _load_kit(stem)
    with _force_html(mod):
        return _cls(mod, stem)().render()


def test_fallback_kits_import_and_render_without_typeerror():
    for stem in _FALLBACK:
        html = _render_html(stem)
        assert isinstance(html, str), stem
        assert html, stem
        _assert_kit_fragment(html, target_id=stem)


def test_dom_only_kits_import_ok_then_fail_loud_not_typeerror():
    for stem in _DOM_ONLY:
        mod = _load_kit(stem)
        with _force_html(mod):
            cls = _cls(mod, stem)
            with pytest.raises(ImportError, match=r"requires ux-dom \(Py≥3\.14\)"):
                cls().render()


def test_toast_demo_path_push_is_fragment():
    from ux_compose.kit.toast import Toast

    with _force_html(sys.modules[Toast.__module__]):
        inst = Toast()
        html = inst.render()
        assert isinstance(html, str)
        _assert_kit_fragment(html, target_id="toast")
        inst.push(message="Saved to the table")
        html = inst.render()
        assert "Saved to the table" in html
        _assert_kit_fragment(html, target_id="toast")
        assert "<html" not in html.lower()
        assert "stunning-root" not in html


def test_login_demo_path_render_is_fragment():
    from ux_compose.kit.login import Login

    with _force_html(sys.modules[Login.__module__]):
        inst = Login()
        html = inst.render()
        assert isinstance(html, str)
        _assert_kit_fragment(html, target_id="login")
        assert 'id="login"' in html
        inst.toggle_password(email="you@atelier.test", password="password12")
        html = inst.render()
        assert "password12" in html
        assert 'type="text"' in html
        _assert_kit_fragment(html, target_id="login")


def test_wave1_typeahead_hits_slot_is_fragment():
    from ux_compose.kit.typeahead import Typeahead

    with _force_html(sys.modules[Typeahead.__module__]):
        inst = Typeahead()
        html = inst.render()
        assert "input delay:300" in html
        assert 'id="typeahead-q"' in html
        _assert_kit_fragment(html, target_id="typeahead")
        ops = inst.query_hits(q="oak")
        blob = " ".join(str(op) for op in (ops or []))
        if isinstance(ops, list):
            for op in ops:
                payload = op if isinstance(op, dict) else getattr(op, "payload", None)
                if isinstance(payload, dict):
                    blob += " " + str(payload.get("html") or "")
        assert "typeahead-hits" in blob
        assert "typeahead-q" not in blob
        assert "Oak serving board" in blob


def test_wave1_actionsheet_closed_is_fragment():
    from ux_compose.kit.actionsheet import ActionSheet

    with _force_html(sys.modules[ActionSheet.__module__]):
        html = ActionSheet().render()
        assert "Open actions" in html
        assert "Share this piece" not in html
        _assert_kit_fragment(html, target_id="actionsheet")


def test_copy_toast_when_has_dom_false(tmp_path, monkeypatch):
    monkeypatch.setattr("ux_compose.kit.copy.HAS_DOM", False)
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    written = copy_component("toast", root=tmp_path)
    text = written["py"].read_text(encoding="utf-8")
    assert "class Toast" in text
    assert "HAS_DOM" in text
    assert "_render_html" in text


def test_copy_tabs_fails_closed_when_has_dom_false(tmp_path, monkeypatch):
    monkeypatch.setattr("ux_compose.kit.copy.HAS_DOM", False)
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    with pytest.raises(KitCopyError, match=r"requires ux-dom \(Py≥3\.14\)"):
        copy_component("tabs", root=tmp_path)
