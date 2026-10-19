"""Trust docs name the two doors and do not teach a bool."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_changelog_logout_does_not_teach_a_trust_bool():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert 'app.dispatch("login.logout", _trusted=True)' not in text
    assert "app.trust()" in text
    assert "dispatch_verified" in text


def test_bridge_actions_docstring_has_no_async_path():
    from ux_compose.wire.caps import bridge_actions

    doc = bridge_actions.__doc__ or ""
    assert "async path" not in doc
    assert "async_dispatch_verified" not in doc
    assert "dispatch_verified(name, payload)" in doc
