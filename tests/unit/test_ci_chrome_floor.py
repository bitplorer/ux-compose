"""CI refuses a Chrome older than 155."""
from __future__ import annotations

from pathlib import Path

_CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def test_ci_logs_chrome_version_and_requires_major_155():
    text = _CI.read_text(encoding="utf-8")
    assert "google-chrome --version" in text
    assert "if major < 155:" in text
