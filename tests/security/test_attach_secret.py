"""Outside dev, an attach failure must fail the boot.

A missing secret already raises inside ux-behavior. A 13-character secret
does not: Channel refuses it, and without ``strict_attach`` compose
continues. ``live_asgi``, ``build()``, and both Atelier servers must
exit non-zero for that secret. The missing-secret Atelier checks passed
on base because ux-behavior already raises; a short secret does not.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
# 13 characters. Channel refuses a capability secret shorter than 16.
SHORT_SECRET = "shortsecret13"


def _env_without_secret() -> dict[str, str]:
    env = os.environ.copy()
    for key in ("UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "DEBUG"):
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}{os.pathsep}{ROOT}"
    return env


def _run(
    argv: list[str], extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = _env_without_secret()
    if extra:
        env.update(extra)
    return subprocess.run(
        argv,
        cwd=ROOT,
        env=env,
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


def test_live_asgi_fails_on_13_char_secret():
    """A short secret is an attach failure. The process must not stay up."""
    assert len(SHORT_SECRET) == 13
    proc = _run([PY, "examples/live_asgi.py"], {"UX_CHANNEL_SECRET": SHORT_SECRET})
    blob = proc.stdout + proc.stderr
    assert proc.returncode != 0, blob


def test_build_fails_on_13_char_secret():
    """build() on the live FastAPI path must raise, not return an app."""
    code = (
        "from pathlib import Path\n"
        "from ux_compose.build import build\n"
        "build(Path('examples/live_asgi_app'), name='LiveDemo', host='fastapi', live='auto')\n"
    )
    proc = _run([PY, "-c", code], {"UX_CHANNEL_SECRET": SHORT_SECRET})
    blob = proc.stdout + proc.stderr
    assert proc.returncode != 0, blob


def test_atelier_shop_boot_fails_on_13_char_secret():
    proc = _run(
        [PY, "-c", "import apps.atelier_shop.server"],
        {"UX_CHANNEL_SECRET": SHORT_SECRET},
    )
    blob = proc.stdout + proc.stderr
    assert proc.returncode != 0, blob


def test_atelier_studio_boot_fails_on_13_char_secret():
    proc = _run(
        [PY, "-c", "import apps.atelier_studio.server"],
        {"UX_CHANNEL_SECRET": SHORT_SECRET},
    )
    blob = proc.stdout + proc.stderr
    assert proc.returncode != 0, blob
