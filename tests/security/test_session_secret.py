"""The suite must not commit a channel secret.

``tests/conftest.py`` generates one per session when the environment
has none. CI does not check a literal in.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LITERAL = "ux-compose-ci-channel-secret"


def test_ci_does_not_commit_a_channel_secret():
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert LITERAL not in text
    assert "UX_CHANNEL_SECRET:" not in text


def test_conftest_generates_a_session_secret():
    text = (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert LITERAL not in text
    assert "secrets.token_urlsafe(32)" in text
