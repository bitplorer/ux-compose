"""A missing channel secret is one clear line, and serve dev shares one secret."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.cli.serve_dev import dev_session_env
from ux_compose.doctor import SECRET_MISSING, secret_readiness
from ux_compose.scaffold import create_app

SECRET = "explicit-secret-0123456789abcdef"
_SCRUB = ("DEBUG", "UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "REDIS_URL", "PYTHONPATH")


def test_secret_missing_line_names_both_ways_out():
    assert SECRET_MISSING == (
        "Channel secret missing: set UX_CHANNEL_SECRET (≥16 chars) for prod, "
        "or DEBUG=1 for a local build"
    )


@pytest.mark.parametrize(
    "env, missing",
    [
        ({}, True),
        ({"DEBUG": ""}, True),
        ({"DEBUG": "0"}, True),
        ({"DEBUG": "false"}, True),
        ({"DEBUG": "1"}, False),
        ({"DEBUG": " True "}, False),
        ({"DEBUG": "on"}, False),
        ({"DEBUG": "false", "UX_CHANNEL_SECRET": SECRET}, False),
        ({"UX_BEHAVIOR_SECRET": SECRET}, False),
    ],
)
def test_secret_readiness_truth_table(env, missing):
    assert secret_readiness(env) == (SECRET_MISSING if missing else None)


def test_secret_readiness_defaults_to_process_env(monkeypatch):
    for name in _SCRUB:
        monkeypatch.delenv(name, raising=False)
    assert secret_readiness() == SECRET_MISSING
    monkeypatch.setenv("DEBUG", "yes")
    assert secret_readiness() is None


def test_dev_session_env_mints_one_secret_for_both_workers():
    env = dev_session_env({})
    assert env["DEBUG"] == "1"
    assert len(env["UX_CHANNEL_SECRET"]) >= 16
    # One dict per serve dev session: ui and channel both get this one.
    assert dev_session_env({})["UX_CHANNEL_SECRET"] != env["UX_CHANNEL_SECRET"]


@pytest.mark.parametrize("name", ["UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET"])
def test_dev_session_env_keeps_an_explicit_secret(name):
    env = dev_session_env({name: SECRET})
    assert env == {"DEBUG": "1"}


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_serve_prod_without_secret_exits_2_with_one_line(tmp_path):
    app_dir = create_app(tmp_path / "demo", name="demo")
    env = {k: v for k, v in os.environ.items() if k not in _SCRUB}
    env["PYTHONPATH"] = str(ROOT / "src")
    cmd = [sys.executable, "-P", "-m", "ux_compose.cli", "serve", "prod",
           "--host", "127.0.0.1", "--port", str(_free_port())]
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=app_dir, env=env, capture_output=True, text=True, timeout=30)
    elapsed = time.monotonic() - started
    out = proc.stdout + proc.stderr
    assert proc.returncode == 2, out
    assert elapsed < 5, elapsed
    assert SECRET_MISSING in proc.stderr
    assert "Traceback" not in out
