"""Network: the scaffold's requirements.txt resolves with uv (CI step)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app


def test_scaffold_requirements_resolve(tmp_path):
    uv = shutil.which("uv")
    assert uv, "uv is required: this test resolves requirements.txt over the network"
    root = create_app(tmp_path / "demo", name="demo")
    argv = [uv, "pip", "compile", str(root / "requirements.txt"), "--python-version", "3.14"]
    argv += ["--no-header", "-o", str(tmp_path / "resolved.txt")]
    if os.environ.get("UV_EXCLUDE_NEWER"):
        argv += ["--exclude-newer", os.environ["UV_EXCLUDE_NEWER"]]
    result = subprocess.run(argv, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
