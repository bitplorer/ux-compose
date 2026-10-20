"""Regression (#114): outside dev a missing channel secret still fails boot.

UC4 made the failure readable. It did not make it optional.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.scaffold import create_app

_SCRUB = ("DEBUG", "UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "REDIS_URL")


def _boot(root: Path, **extra: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in _SCRUB}
    env["PYTHONPATH"] = os.pathsep.join([str(root), str(ROOT / "src")])
    env.update(extra)
    return subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=root, env=env, capture_output=True, text=True, timeout=60,
    )


@pytest.fixture(scope="module")
def app_root(tmp_path_factory):
    return create_app(tmp_path_factory.mktemp("boot") / "demo", name="demo")


@pytest.mark.parametrize("debug", [None, "0", "false"])
def test_missing_secret_outside_dev_fails_boot(app_root, debug):
    extra = {} if debug is None else {"DEBUG": debug}
    proc = _boot(app_root, **extra)
    assert proc.returncode != 0
    assert "RuntimeError: attach() requires UX_CHANNEL_SECRET" in proc.stderr


def test_short_secret_fails_boot(app_root):
    proc = _boot(app_root, UX_CHANNEL_SECRET="thirteen-char")
    assert proc.returncode != 0
    assert "ValueError: capability secret must be at least 16 characters" in proc.stderr


def test_published_dev_secret_fails_boot(app_root):
    proc = _boot(app_root, UX_CHANNEL_SECRET="dev-secret-key-32chars-minimum!!!!")
    assert proc.returncode != 0
    assert "the public dev secret is not accepted" in proc.stderr


def test_prod_boots_with_a_secret(app_root):
    proc = _boot(app_root, DEBUG="false", UX_CHANNEL_SECRET="regression-secret-0123456789")
    assert proc.returncode == 0, proc.stderr
