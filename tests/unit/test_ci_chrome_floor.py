"""CI and the browser tests refuse a Chrome older than 155.

Both call ``scripts/chrome_floor.py``. 155 and 156 pass. 154, 99, a
version with no digits, a broken binary, and a missing binary each
exit non-zero.
"""
from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "scripts" / "chrome_floor.py"
_CI = _ROOT / ".github" / "workflows" / "ci.yml"


def _fake(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def _run(binary: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), str(binary)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_ci_calls_the_chrome_floor_script():
    text = _CI.read_text(encoding="utf-8")
    assert "scripts/chrome_floor.py" in text


def test_chrome_floor_accepts_155_and_156(tmp_path: Path):
    for major in (155, 156):
        binary = _fake(
            tmp_path,
            f"chrome-{major}",
            "#!/bin/sh\n"
            f"echo \"Google Chrome {major}.0.0.0\"\n",
        )
        result = _run(binary)
        assert result.returncode == 0, result.stderr
        assert f"Chrome major: {major}" in result.stdout


def test_chrome_floor_rejects_old_broken_and_missing(tmp_path: Path):
    cases = {
        "154": _fake(tmp_path, "chrome-154", "#!/bin/sh\necho \"Google Chrome 154.0.0.0\"\n"),
        "99": _fake(tmp_path, "chrome-99", "#!/bin/sh\necho \"Google Chrome 99.0.0.0\"\n"),
        "no-digits": _fake(tmp_path, "chrome-words", "#!/bin/sh\necho \"Google Chrome\"\n"),
        "broken": _fake(tmp_path, "chrome-broken", "#!/bin/sh\nexit 3\n"),
    }
    for name, binary in cases.items():
        result = _run(binary)
        assert result.returncode != 0, name
    missing = _run(tmp_path / "chrome-missing")
    assert missing.returncode != 0
