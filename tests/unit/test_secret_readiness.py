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


def test_run_gives_both_workers_and_the_respawn_one_session_env(tmp_path, monkeypatch):
    """serve_dev.run hands the same dev_session_env to ui, channel and a channel respawn."""
    import signal

    import uvicorn

    from ux_compose.cli import serve_dev

    for name in _SCRUB:
        monkeypatch.delenv(name, raising=False)
    spawned: list[tuple[list[str], dict]] = []

    class _Proc:
        returncode = None

        def poll(self):
            return None

    def fake_spawn(cmd, *, cwd, extra_env=None, pass_fds=()):
        spawned.append((cmd, dict(extra_env or {})))
        return _Proc()

    def fake_origin(*args, **kwargs):
        # Ask for one channel restart, as `serve restart-channel` does.
        handler = signal.getsignal(signal.SIGUSR1)
        handler(signal.SIGUSR1, None)
        deadline = time.monotonic() + 5
        while len(spawned) < 3 and time.monotonic() < deadline:
            time.sleep(0.05)

    monkeypatch.setattr(serve_dev, "_spawn", fake_spawn)
    monkeypatch.setattr(serve_dev, "_stop", lambda *procs: None)
    monkeypatch.setattr(serve_dev, "_port_open", lambda port, host="127.0.0.1": True)
    monkeypatch.setattr(serve_dev, "_watch_workers", lambda *a: None)
    monkeypatch.setattr(serve_dev, "prepare_shared_state", lambda root: None)
    monkeypatch.setattr(serve_dev, "drop_shared_state", lambda root: None)
    monkeypatch.setattr(serve_dev, "clear_shared_state", lambda: True)
    monkeypatch.setattr(uvicorn, "run", fake_origin)
    old_usr1 = signal.getsignal(signal.SIGUSR1)
    try:
        rc = serve_dev.run(
            app_ref="app:asgi", host="127.0.0.1", port=_free_port(),
            reload_dirs=["."], cwd=str(tmp_path), css_watch=False,
        )
    finally:
        signal.signal(signal.SIGUSR1, old_usr1)
    assert rc == 0
    assert len(spawned) == 3, spawned
    secrets_seen = {env.get("UX_CHANNEL_SECRET") for _cmd, env in spawned}
    assert len(secrets_seen) == 1 and None not in secrets_seen
    assert all(env.get("DEBUG") == "1" for _cmd, env in spawned)
    assert "UX_CHANNEL_SECRET" not in os.environ
