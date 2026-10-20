"""``uxcompose serve prod`` imports ``app`` from the cwd without PYTHONPATH."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_serve_prod_imports_app_from_cwd(tmp_path):
    app_dir = create_app(tmp_path / "demo", name="demo")
    port = _free_port()
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "DEBUG")}
    # Only this checkout's src is on the path, never the app dir.
    env["PYTHONPATH"] = str(ROOT / "src")
    env["UX_CHANNEL_SECRET"] = "serve-prod-import-secret-0123456789"
    log = tmp_path / "serve.log"
    # -P keeps the cwd off sys.path, as the installed console script does.
    # Plain ``python -m`` would put the app dir on sys.path and hide the bug.
    cmd = [sys.executable, "-P", "-m", "ux_compose.cli", "serve", "prod",
           "--host", "127.0.0.1", "--port", str(port)]
    with log.open("wb") as out:
        proc = subprocess.Popen(cmd, cwd=app_dir, env=env, stdout=out, stderr=subprocess.STDOUT)
        try:
            status, body = None, ""
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and proc.poll() is None:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as resp:
                        status, body = resp.status, resp.read().decode("utf-8")
                    break
                except (urllib.error.URLError, ConnectionError):
                    time.sleep(0.2)
        finally:
            proc.terminate()
            proc.wait(timeout=10)
    output = log.read_text(encoding="utf-8", errors="replace")
    assert status == 200, output
    assert "data-uxcompose-hmr" not in body
