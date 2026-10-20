"""Network: pip accepts every file in tests/unit/requirements_corpus (dry run).

That corpus is what ``scan_requirements`` must parse; this proves it is valid pip
syntax and not something only the scanner accepts.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

CORPUS = Path(__file__).resolve().parents[1] / "unit" / "requirements_corpus"


@pytest.mark.parametrize("name", ["hashed.txt", "index_options.txt", "includes.txt"])
def test_pip_accepts_corpus_file(name):
    pytest.importorskip("pip", reason="needs pip in this interpreter (CI installs it)")
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--dry-run", "--no-deps",
         "--ignore-installed", "--disable-pip-version-check", "-r", str(CORPUS / name)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Would install" in proc.stdout
