"""Network: the scaffold's requirements.txt resolves with uv (CI step).

create-app pins the running checkout's HEAD, which may be a local commit
GitHub has never seen (an unpushed branch, a local merge before landing).
So the ux-compose ref comes from ``fetchable_ref()``: ``GITHUB_SHA`` in CI,
else the nearest ancestor of HEAD that is on a remote branch.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import scaffold

SPECIALISTS = ("ux-dom", "ux-channel", "ux-behavior", "ux-motion")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True
    ).stdout


def fetchable_ref() -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    walk = _git("rev-list", "--boundary", "HEAD", "--not", "--remotes").split()
    if not walk:
        return _git("rev-parse", "HEAD").strip()
    boundary = [sha[1:] for sha in walk if sha.startswith("-")]
    assert boundary, "HEAD has no ancestor on a remote branch; fetch or push first"
    return boundary[0]


def test_scaffold_requirements_resolve(tmp_path, monkeypatch):
    uv = shutil.which("uv")
    assert uv, "uv is required: this test resolves requirements.txt over the network"
    ref = fetchable_ref()
    line = f"ux-compose @ git+{scaffold.COMPOSE_GIT}@{ref}"
    monkeypatch.setattr(scaffold, "compose_requirement", lambda: (line, None))
    root = scaffold.create_app(tmp_path / "demo", name="demo")
    assert (root / "requirements.txt").read_text(encoding="utf-8").splitlines()[0] == line

    out = tmp_path / "resolved.txt"
    argv = [uv, "pip", "compile", str(root / "requirements.txt"), "--python-version", "3.14"]
    argv += ["--no-header", "-o", str(out)]
    if os.environ.get("UV_EXCLUDE_NEWER"):
        argv += ["--exclude-newer", os.environ["UV_EXCLUDE_NEWER"]]
    result = subprocess.run(argv, check=False, capture_output=True, text=True)
    assert result.returncode == 0, (ref, result.stderr)

    resolved = out.read_text(encoding="utf-8")
    pyproject = _git("show", f"{ref}:pyproject.toml")
    for dist in SPECIALISTS:
        pin = re.findall(rf"{dist} @ git\+https://github\.com/bitplorer/{dist}\.git@([0-9a-f]{{40}})", pyproject)
        assert len(pin) == 1, (dist, ref)
        assert f"{dist}.git@{pin[0]}" in resolved, (dist, pin[0], ref)
