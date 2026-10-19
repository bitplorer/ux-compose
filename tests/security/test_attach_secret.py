"""Outside dev, a missing channel secret must fail the boot.

ux-behavior refuses ``attach()`` without ``UX_CHANNEL_SECRET`` (or
``UX_BEHAVIOR_SECRET``) when ``DEBUG`` is not a dev value. Compose must
not boot the live ASGI path anyway. Atelier already raises. ``examples/live_asgi.py``
still exits 0 because ``build()`` swallows the error.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable


def _env_without_secret() -> dict[str, str]:
    env = os.environ.copy()
    for key in ("UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "DEBUG"):
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}{os.pathsep}{ROOT}"
    return env


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=ROOT,
        env=_env_without_secret(),
        capture_output=True,
        text=True,
        check=False,
    )


def test_live_asgi_fails_loudly_when_channel_secret_missing():
    """build() on the live FastAPI path must not continue without Caps."""
    proc = _run([PY, "examples/live_asgi.py"])
    blob = proc.stdout + proc.stderr
    assert proc.returncode != 0, blob
    assert "UX_CHANNEL_SECRET" in blob


def test_atelier_shop_boot_fails_without_channel_secret():
    proc = _run([PY, "-c", "import apps.atelier_shop.server"])
    blob = proc.stdout + proc.stderr
    assert proc.returncode != 0, blob
    assert "UX_CHANNEL_SECRET" in blob


def test_atelier_studio_boot_fails_without_channel_secret():
    proc = _run([PY, "-c", "import apps.atelier_studio.server"])
    blob = proc.stdout + proc.stderr
    assert proc.returncode != 0, blob
    assert "UX_CHANNEL_SECRET" in blob
