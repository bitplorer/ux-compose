"""Hard-deps floor: pins, extras, fail-loud doors. Isolation: no ux_channel."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

UX_DOM_SHA = "e8be99a52bfecd6026c200fa1c3dc6a74f87aacb"
UX_CHANNEL_SHA = "b0cc17d87348fa65578f41e95879b35c43b0ecfa"
UX_BEHAVIOR_SHA = "793f120e3b1388925772cd069b070d7918b78baa"
UX_MOTION_SHA = "67ff3f0c4912b70b7056f8226a6f226b6fe93f60"
COMPOSE_SHA = "6d61c9e616652d996e55a36886ccfec218308c30"


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
    assert "25338a6" not in text
    assert "76adc72" not in text


def test_pin_ssot_lockstep_makefile_scaffold_ci():
    """pyproject / Makefile / scaffold / CI tell one pin story."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    scaffold = (ROOT / "src" / "ux_compose" / "scaffold.py").read_text(encoding="utf-8")
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    nook = (ROOT / "apps" / "nook" / "requirements.txt").read_text(encoding="utf-8")
    for sha in (UX_DOM_SHA, UX_CHANNEL_SHA, UX_BEHAVIOR_SHA, UX_MOTION_SHA):
        assert sha in makefile
        assert sha in scaffold
        assert sha in nook
    assert "git+https://github.com/bitplorer/ux-compose.git@" in scaffold
    assert "git+https://github.com/bitplorer/ux-compose.git@" in nook
    assert COMPOSE_SHA in scaffold
    assert COMPOSE_SHA in nook
    assert "e6b5ea4" not in scaffold
    assert "e6b5ea4" not in nook
    assert "25338a6" not in makefile
    assert "76adc72" not in makefile
    assert "25338a6" not in scaffold
    assert "76adc72" not in scaffold
    assert 'python-version: "3.14"' in ci
    assert "3.12" not in ci
    assert "offline-shim" not in ci
    assert 'pip install -e ".[dev]"' in ci
    assert "25338a6" not in ci
    assert "76adc72" not in ci
    assert "PYTHONPATH=src:. $(PY314) -m uvicorn apps.pulse.server:app" in makefile


def test_probe_exposes_incomplete_stack_messages():
    from ux_compose.dx.probe import ProbeResult

    assert hasattr(ProbeResult, "incomplete_stack_messages")
    assert not hasattr(ProbeResult, "unlock_messages")


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


def test_helpers_use_specialist_facades_not_parallel_shims():
    import ux_compose.helpers as helpers
    import inspect

    src = inspect.getsource(helpers)
    assert "html_escape" not in src
    assert "html_attrs" not in src
    assert "_HAS_BEHAVIOR" not in src
    assert "to_html_bytes" in src
    from ux_compose.author import optional_plan

    plan = optional_plan("x", "#y", ms=10)
    assert plan is not None
    assert type(plan).__name__ in {"Scene", "Plan"} or hasattr(plan, "enter") or hasattr(plan, "ops")


def test_chrome_is_document_path_brand_wrap_not_string_shell():
    """GET chrome is Document-path brand_wrap. wrap_get_chrome stays gone."""
    from ux_compose import chrome as chrome_mod
    from ux_compose.chrome import brand_wrap

    assert callable(brand_wrap)
    assert not hasattr(chrome_mod, "wrap_get_chrome")
    src = (ROOT / "src" / "ux_compose" / "chrome.py").read_text(encoding="utf-8")
    assert "wrap_get_chrome" not in src
    assert "<!DOCTYPE html>" not in src
    assert "HAS_DOM" not in src
    with pytest.raises(TypeError, match="callable Document"):
        brand_wrap(None)


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
