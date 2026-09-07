"""Hard-deps floor: pins, extras, fail-loud doors. Isolation: no ux_channel."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

UX_DOM_SHA = "25338a6d624b764bb79615de52fca48084ce2c55"
UX_CHANNEL_SHA = "31a60bdd40a1b52aea1fd13159ad09c293c63fd6"
UX_BEHAVIOR_SHA = "76adc72ff8e8d2f6a784d8b988b720934bd8a612"
UX_MOTION_SHA = "67ff3f0c4912b70b7056f8226a6f226b6fe93f60"


def test_pyproject_requires_314_and_pins_specialists():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.14"' in text
    assert UX_DOM_SHA in text
    assert UX_CHANNEL_SHA in text
    assert UX_BEHAVIOR_SHA in text
    assert UX_MOTION_SHA in text
    assert "cek-host>=0.1.3" in text
    assert "cek-surface>=0.1.3" in text
    assert 'subdirectory=python' in text


def test_specialist_extras_are_empty_aliases():
    import tomllib

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = data["project"]["optional-dependencies"]
    for name in ("dom", "behavior", "motion", "channel", "full"):
        assert extras[name] == []


def test_has_dom_is_constant_true():
    from ux_compose import HAS_DOM
    from ux_compose.dom import require_dom

    assert HAS_DOM is True
    require_dom()


def test_chrome_module_removed():
    with pytest.raises(ModuleNotFoundError):
        __import__("ux_compose.chrome")


def test_use_channel_fail_loud(monkeypatch):
    from ux_compose.app import App
    import ux_compose.wire.boot as boot

    def boom(*_a, **_k):
        raise ImportError("missing ux-channel")

    monkeypatch.setattr(boot, "attach_channel", boom)
    with pytest.raises(ImportError, match="ux-channel is required"):
        App.boot("T").use_channel()


def test_use_motion_fail_loud(monkeypatch):
    from ux_compose.app import App
    import ux_compose.wire.boot as boot

    def boom():
        raise ImportError("missing ux-motion")

    monkeypatch.setattr(boot, "attach_motion", boom)
    with pytest.raises(ImportError, match="ux-motion is required"):
        App.boot("T").use_motion()


def test_use_behavior_fail_loud(monkeypatch):
    from ux_compose.app import App

    import builtins

    real_import = builtins.__import__

    def fake(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "ux_behavior":
            raise ImportError("missing ux-behavior")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake)
    with pytest.raises(ImportError, match="ux-behavior is required"):
        App("T").use_behavior()


def test_attach_document_fail_loud(monkeypatch):
    from ux_compose.build import _attach_document

    import builtins

    real_import = builtins.__import__

    def fake(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "ux_dom" or name.startswith("ux_dom."):
            raise ImportError("missing ux-dom")
        return real_import(name, globals, locals, fromlist, level)

    class _App:
        def use_dom(self, document, *, author=True):
            self.document = document

    monkeypatch.setattr(builtins, "__import__", fake)
    with pytest.raises(ImportError, match="ux-dom is required"):
        _attach_document(_App(), None, use_htmx=False)
