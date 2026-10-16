"""Gate: every file that states the ux-compose version states the real one.

Same pattern as ux-dom ``tests/04_production/test_version_gate.py``. The
version comes from ``pyproject.toml``. There is a fixed list of
version-bearing files: each must mention the version, and every X.Y.Z in it
must equal the version unless it is listed as a known non-ux-compose string.
A repo-wide check also makes sure no "ux-compose X.Y" brand line names
another version. Add a file here when it starts stating the version.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
V = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
MAJOR_MINOR = ".".join(V.split(".")[:2])
SEMVER = re.compile(r"(?<![\w.])v?(\d+\.\d+\.\d+)(?!\w|\.\d)")

# file -> X.Y.Z strings in it that are not the ux-compose version
# pyproject.toml is the source of V (not listed: its cek-host/cek-surface
# ">=0.2.0" floors match V only by coincidence).
VERSION_FILES: dict[str, frozenset[str]] = {
    "src/ux_compose/__init__.py": frozenset(),
    "README.md": frozenset(),
}

REQUIRED_FORMS = {
    "README.md": rf"^\| \*\*Version\*\* \| `{re.escape(V)}` \|",
    "src/ux_compose/__init__.py": rf'^__version__ = "{re.escape(V)}"$',
    "SECURITY.md": rf"^\| {re.escape(MAJOR_MINOR)}\.x\s+\| Yes",
    "CHANGELOG.md": rf"^## {re.escape(V)}\b",
}

# "ux-compose X.Y", "ux_compose==X.Y.Z", "uxcompose vX.Y.Z" brand lines outside history
BRAND = re.compile(r"\bux[-_]?compose(?:\s+v?|\s*==\s*v?)(\d+\.\d+(?:\.\d+)?)\b", re.I)
SKIP_DIRS = {".venv", ".git", "node_modules", "__pycache__", ".pytest_cache"}
SKIP_PATHS = {"docs/plans", "docs/adr"}  # dated records, history by design
HISTORY = {"CHANGELOG.md", "CRITIC.md"}  # CRITIC.md: the 0.1.0 critic pass, a record


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dunder_version_matches_pyproject():
    import ux_compose

    assert ux_compose.__version__ == V


@pytest.mark.parametrize("rel", sorted(VERSION_FILES))
def test_listed_file_states_the_version(rel):
    mentions = [m for m in SEMVER.findall(_text(rel)) if m not in VERSION_FILES[rel]]
    assert mentions, f"{rel}: no version mention (stale list?)"
    wrong = sorted({m for m in mentions if m != V})
    assert not wrong, f"{rel}: {wrong} != version {V}"


@pytest.mark.parametrize("rel", sorted(REQUIRED_FORMS))
def test_required_version_forms(rel):
    assert re.search(REQUIRED_FORMS[rel], _text(rel), re.M), rel


def test_changelog_top_versioned_entry_is_the_version():
    first = re.search(r"^## \[?(\d+\.\d+\.\d+)", _text("CHANGELOG.md"), re.M).group(1)
    assert first == V
    heading = re.search(rf"^## {re.escape(V)}\b.*$", _text("CHANGELOG.md"), re.M).group(0)
    assert "unreleased" not in heading.lower(), heading  # "## Unreleased" carries that


def test_no_stale_brand_version_anywhere():
    stale = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".py", ".toml", ".txt"}:
            continue
        rel = path.relative_to(ROOT)
        if set(rel.parts) & SKIP_DIRS or path.name in HISTORY:
            continue
        if any(rel.as_posix().startswith(p + "/") for p in SKIP_PATHS):
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for m in BRAND.finditer(line):
                if m.group(1) not in (V, MAJOR_MINOR):
                    stale.append(f"{rel}:{n}: {m.group(0)}")
    assert not stale, "\n".join(stale)
