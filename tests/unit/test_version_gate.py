"""One version, every surface (fixed list, fail closed)."""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = "0.2.0"


def test_pyproject_version_field():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == VERSION


def test_dunder_version():
    src = (ROOT / "src" / "ux_compose" / "__init__.py").read_text(encoding="utf-8")
    assert re.search(r'^__version__ = "([^"]+)"', src, re.M).group(1) == VERSION


def test_readme_version_row():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"| **Version** | `{VERSION}` |" in readme


def test_changelog_top_entry():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    first = re.search(r"^## \[?(\d+\.\d+\.\d+)", log, re.M).group(1)
    assert first == VERSION
