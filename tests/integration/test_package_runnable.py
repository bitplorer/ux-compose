"""Network: the bundle from ``uxcompose build --package`` runs from a fresh venv (CI step).

The bundle's ``requirements.txt`` must name a ux-compose commit GitHub has,
so the pin comes from ``fetchable_ref()`` as in the scaffold resolve test.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_scaffold_requirements_resolve import fetchable_ref

from ux_compose import scaffold
from ux_compose.cli import main

SECRET = "explicit-secret-0123456789abcdef"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status
    except OSError:
        return 0


def test_bundle_runs_from_fresh_venv(tmp_path, monkeypatch):
    uv = shutil.which("uv")
    assert uv, "uv is required: this test installs the bundle's requirements.txt"
    line = f"ux-compose @ git+{scaffold.COMPOSE_GIT}@{fetchable_ref()}"
    monkeypatch.setattr(scaffold, "compose_requirement", lambda: (line, None))
    for name in ("DEBUG", "UX_BEHAVIOR_SECRET", "REDIS_URL", "UXCOMPOSE_STATE_STORE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)
    root = scaffold.create_app(tmp_path / "demo", name="demo")
    monkeypatch.chdir(root)
    out = tmp_path / "out"
    assert main(["build", "--skip-tailwind", "--package", "--out", str(out)]) == 0

    elsewhere = tmp_path / "elsewhere"
    venv = elsewhere / "venv"
    subprocess.run([uv, "venv", str(venv), "--python", "3.14"], check=True)
    argv = [uv, "pip", "install", "--python", str(venv / "bin" / "python"), "-r", str(out / "demo" / "requirements.txt")]
    if os.environ.get("UV_EXCLUDE_NEWER"):
        argv += ["--exclude-newer", os.environ["UV_EXCLUDE_NEWER"]]
    subprocess.run(argv, check=True, cwd=elsewhere)

    port = _free_port()
    env = {
        "PATH": f"{venv / 'bin'}{os.pathsep}/usr/bin:/bin",
        "HOME": str(elsewhere),
        "UX_CHANNEL_SECRET": SECRET,
        "PORT": str(port),
        "HOST": "127.0.0.1",
    }
    proc = subprocess.Popen(["sh", str(out / "demo" / "run.sh")], cwd=elsewhere, env=env)
    try:
        base = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 60
        while _get(base + "/") != 200 and time.monotonic() < deadline:
            assert proc.poll() is None, "run.sh exited"
            time.sleep(0.5)
        for path in ("/", "/hello", "/ux-dom/static/x_element.js"):
            assert _get(base + path) == 200, path
    finally:
        proc.terminate()
        proc.wait(timeout=10)
