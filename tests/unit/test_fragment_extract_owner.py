"""Soft USE lock: helpers prefer ux-dom extract_by_id; walker is escape.

Cite ux-dom#19/#20 and compose#80 C2. No fragment.py. Cap door KEEP.
Do not import ux_compose at module level (sandbox may lack specialists).
Isolated loader stubs specialists so prefer/escape run without Python 3.14.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"
BOOT = SRC / "wire" / "boot.py"
HELPERS = SRC / "helpers.py"

_HAS_SPECIALISTS = (
    importlib.util.find_spec("ux_behavior") is not None
    and importlib.util.find_spec("ux_dom") is not None
)

_STUB_KEYS = (
    "ux_behavior",
    "ux_behavior.ops",
    "ux_dom",
    "ux_dom.response",
    "ux_dom.response.serialize",
    "ux_compose",
    "ux_compose.helpers",
)


def _stub_specialists(*, extract_by_id=False):
    """Install stub specialists. Caller must restore via the returned map."""
    saved = {key: sys.modules.get(key) for key in _STUB_KEYS}
    ops = types.ModuleType("ux_behavior.ops")

    class Op:
        def __init__(self, ns, name, payload=None):
            self.ns = ns
            self.name = name
            self.payload = payload or {}

    ops.Op = Op
    behavior = types.ModuleType("ux_behavior")
    behavior.bind = lambda *a, **k: {}
    behavior.notify = lambda *a, **k: None
    behavior.update = lambda *a, **k: None
    behavior.ops = ops
    serialize = types.ModuleType("ux_dom.response.serialize")
    serialize.to_html_bytes = lambda tree: b""
    serialize.__all__ = ["to_html_bytes"]
    if extract_by_id is not False:
        serialize.extract_by_id = extract_by_id
        serialize.__all__ = ["to_html_bytes", "extract_by_id"]
    response = types.ModuleType("ux_dom.response")
    response.serialize = serialize
    if extract_by_id is not False:
        response.extract_by_id = extract_by_id
    ux_dom = types.ModuleType("ux_dom")
    ux_dom.response = response
    pkg = types.ModuleType("ux_compose")
    pkg.__path__ = [str(SRC)]
    sys.modules.update(
        {
            "ux_behavior": behavior,
            "ux_behavior.ops": ops,
            "ux_dom": ux_dom,
            "ux_dom.response": response,
            "ux_dom.response.serialize": serialize,
            "ux_compose": pkg,
        }
    )
    return saved


def _restore_modules(saved: dict) -> None:
    for key, prior in saved.items():
        if prior is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = prior


def _load_isolated_helpers(*, extract_by_id=False):
    """Import helpers.py against stub specialists. Stubs stay until restore."""
    saved = _stub_specialists(extract_by_id=extract_by_id)
    try:
        spec = importlib.util.spec_from_file_location("ux_compose.helpers", HELPERS)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules["ux_compose.helpers"] = mod
        spec.loader.exec_module(mod)
        return mod, saved
    except Exception:
        _restore_modules(saved)
        raise


def test_no_fragment_py_and_helpers_names_owner():
    src = HELPERS.read_text(encoding="utf-8")
    assert "extract_by_id" in src
    assert "def _owner_extract_by_id" in src
    assert "def _element_end" in src
    assert "def _open_tag_id" in src
    assert "def _fragment_for_target" in src
    assert not (SRC / "fragment.py").exists()
    assert not (SRC / "helpers").exists()


def test_soft_use_keeps_channel_boot_cap_door():
    """Cap / mount_channel KEEP. Soft USE does not invent a compose remount."""
    boot = BOOT.read_text(encoding="utf-8")
    assert "Channel.boot" in boot
    assert "Compose door is Channel.boot" in boot
    assert "ActionRegistry.from_config" in boot
    assert "def attach_channel" in boot
    assert "mount_channel(" not in boot


def test_isolated_fragment_prefers_owner_when_importable():
    seen: list[tuple[str, str]] = []

    def owner(html: str, target_id: str) -> str:
        seen.append((html, target_id))
        return '<div id="hello">owner</div>'

    helpers, saved = _load_isolated_helpers(extract_by_id=owner)
    try:
        html = '<main id="page"><div id="hello">x</div></main>'
        assert helpers._owner_extract_by_id() is owner
        assert helpers._fragment_for_target(html, "hello") == '<div id="hello">owner</div>'
        assert seen == [(html, "hello")]
    finally:
        _restore_modules(saved)


def test_isolated_fragment_homemade_escape_when_owner_absent():
    helpers, saved = _load_isolated_helpers(extract_by_id=False)
    try:
        assert helpers._owner_extract_by_id() is None
        html = '<main id="page"><div id="hello">x</div></main>'
        assert helpers._fragment_for_target(html, "#hello") == '<div id="hello">x</div>'
        assert helpers._fragment_for_target(html, "") == html
        assert helpers._fragment_for_target("", "hello") == ""
    finally:
        _restore_modules(saved)


@pytest.mark.skipif(not _HAS_SPECIALISTS, reason="ux-dom + ux-behavior required")
def test_live_owner_probe_matches_serialize_symbol():
    """After #82 the pin has extract_by_id; probe must bind that callable."""
    import ux_compose.helpers as helpers
    import ux_dom.response.serialize as serialize

    helpers._EXTRACT_BY_ID = helpers._UNSET
    probed = helpers._owner_extract_by_id()
    live = getattr(serialize, "extract_by_id", None)
    assert probed is live


@pytest.mark.skipif(not _HAS_SPECIALISTS, reason="ux-dom + ux-behavior required")
def test_fragment_prefers_owner_when_present(monkeypatch):
    import ux_compose.helpers as helpers

    seen: list[tuple[str, str]] = []

    def owner(html: str, target_id: str) -> str:
        seen.append((html, target_id))
        return '<div id="hello">owner</div>'

    monkeypatch.setattr(helpers, "_EXTRACT_BY_ID", owner)
    html = '<main id="page"><div id="hello">x</div></main>'
    assert helpers._fragment_for_target(html, "hello") == '<div id="hello">owner</div>'
    assert seen == [(html, "hello")]


@pytest.mark.skipif(not _HAS_SPECIALISTS, reason="ux-dom + ux-behavior required")
def test_fragment_homemade_escape_when_owner_absent(monkeypatch):
    import ux_compose.helpers as helpers

    monkeypatch.setattr(helpers, "_EXTRACT_BY_ID", None)
    html = '<main id="page"><div id="hello">x</div></main>'
    assert helpers._fragment_for_target(html, "#hello") == '<div id="hello">x</div>'
    assert helpers._fragment_for_target(html, "") == html
    assert helpers._fragment_for_target("", "hello") == ""
