"""Soft USE lock: helpers prefer ux-dom extract_by_id; walker is escape.

Cite ux-dom#19/#20 and compose#80 C2. No fragment.py. Cap door KEEP.
Do not import ux_compose at module level (sandbox may lack specialists).
"""
from __future__ import annotations

import importlib.util
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
