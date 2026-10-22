"""Hard-deps floor: pins, extras, fail-loud doors. Isolation: no ux_channel."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

UX_DOM_SHA = "9a8623342315720f9fa07eeaf0699c598e340c97"
UX_CHANNEL_SHA = "0ffe8e9907cd1a0701ffc8cb2e5414d6b39d2996"
UX_BEHAVIOR_SHA = "f12321fa7a5399753a21fd6e5c4e88de43027222"
UX_MOTION_SHA = "bbe7d73466a6c1eccb47e711568c80ce3b4d5487"


def test_pyproject_requires_314_and_pins_specialists():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.14"' in text
    assert UX_DOM_SHA in text
    assert UX_CHANNEL_SHA in text
    assert UX_BEHAVIOR_SHA in text
    assert UX_MOTION_SHA in text
    assert "cek-host>=0.2.0" in text
    assert "cek-surface>=0.2.0" in text
    assert "0626a10" not in text
    assert "subdirectory=cek-host" not in text
    assert "cek-host>=0.1.3" not in text
    assert "cek-surface>=0.1.3" not in text
    assert 'subdirectory=python' in text
    assert "25338a6" not in text
    assert "76adc72" not in text
    assert "e8be99a" not in text
    assert "d0412c6" not in text
    assert "793f120" not in text
    assert "67ff3f0" not in text
    assert "ad86d4c" not in text


def test_pin_ssot_lockstep_makefile_scaffold_ci():
    """pyproject / Makefile / scaffold / CI tell one pin story."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    scaffold = (ROOT / "src" / "ux_compose" / "scaffold.py").read_text(encoding="utf-8")
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for sha in (UX_DOM_SHA, UX_CHANNEL_SHA, UX_BEHAVIOR_SHA, UX_MOTION_SHA):
        assert sha in makefile
    for leaf in (makefile, scaffold):
        assert "cek-host>=0.2.0" in leaf
        assert "cek-surface>=0.2.0" in leaf
        assert "0626a10" not in leaf
    assert 'COMPOSE_GIT = "https://github.com/bitplorer/ux-compose.git"' in scaffold
    assert "_VCS_PIN" not in scaffold
    assert not list((ROOT / "apps").glob("*/requirements.txt"))
    assert "25338a6" not in makefile
    assert "76adc72" not in makefile
    assert "e8be99a" not in makefile
    assert "d0412c6" not in makefile
    assert "793f120" not in makefile
    assert "67ff3f0" not in makefile
    assert "ad86d4c" not in makefile
    assert 'python-version: "3.14"' in ci
    assert "3.12" not in ci
    assert "offline-shim" not in ci
    assert 'uv pip install --python "$venv" --exclude-newer "$UV_EXCLUDE_NEWER"' in ci
    assert '-e ".[dev]"' in ci
    assert "25338a6" not in ci
    assert "76adc72" not in ci
    assert "PYTHONPATH=src:. $(PY314) -m uvicorn apps.pulse.server:app" in makefile


def _specialist_pins(pyproject: str, dist: str) -> list[str]:
    return re.findall(
        rf'"{dist} @ git\+https://github\.com/bitplorer/{dist}\.git@([0-9a-f]{{40}})', pyproject
    )


def test_pins_agree_in_all_four_places(tmp_path):
    """Each specialist SHA is the same in pyproject, Makefile, this file, and
    the pyproject of the ux-compose commit that create-app's requirements.txt
    pins (the specialists a scaffolded app installs)."""
    from ux_compose.scaffold import create_app

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    req = (create_app(tmp_path / "app") / "requirements.txt").read_text(encoding="utf-8")
    compose = [ln for ln in req.splitlines() if ln.startswith("ux-compose")]
    assert len(compose) == 1, req
    pinned = re.fullmatch(
        r"ux-compose @ git\+https://github\.com/bitplorer/ux-compose\.git@([0-9a-f]{40})",
        compose[0],
    )
    assert pinned, compose
    scaffold_pyproject = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{pinned.group(1)}:pyproject.toml"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    expected = {
        "ux-dom": ("UX_DOM_SHA", UX_DOM_SHA),
        "ux-channel": ("UX_CHANNEL_SHA", UX_CHANNEL_SHA),
        "ux-behavior": ("UX_BEHAVIOR_SHA", UX_BEHAVIOR_SHA),
        "ux-motion": ("UX_MOTION_SHA", UX_MOTION_SHA),
    }
    for dist, (make_var, test_sha) in expected.items():
        from_pyproject = _specialist_pins(pyproject, dist)
        from_makefile = re.findall(rf"^{make_var} = ([0-9a-f]{{40}})$", makefile, re.M)
        from_scaffold = _specialist_pins(scaffold_pyproject, dist)
        assert from_pyproject == from_makefile == from_scaffold == [test_sha], (
            dist,
            from_pyproject,
            from_makefile,
            from_scaffold,
            test_sha,
        )


def test_probe_exposes_incomplete_stack_messages():
    from ux_compose.dx.probe import ProbeResult

    assert hasattr(ProbeResult, "incomplete_stack_messages")
    assert not hasattr(ProbeResult, "unlock_messages")


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
    # Serialize is ux-dom's, behind the one HTML sink contract (dom.html_text).
    assert "from ux_compose.dom import TrustedHtml, html_text" in src
    assert "to_html_bytes" in inspect.getsource(inspect.getmodule(helpers.html_text))
    from ux_compose.author import optional_plan

    plan = optional_plan("x", "#y", ms=10)
    assert plan is not None
    assert type(plan).__name__ in {"Scene", "Plan"} or hasattr(plan, "enter") or hasattr(plan, "ops")


def test_brand_is_document_path_not_string_shell():
    """Brand bar is Document-path brand_wrap. wrap_get_chrome stays gone."""
    import ux_compose.brand as brand_mod
    from ux_compose.brand import brand_wrap

    assert callable(brand_wrap)
    assert not hasattr(brand_mod, "wrap_get_chrome")
    src = (ROOT / "src" / "ux_compose" / "brand.py").read_text(encoding="utf-8")
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
