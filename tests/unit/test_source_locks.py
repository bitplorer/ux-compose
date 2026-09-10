"""Source-level locks. Do not import ux_compose (sandbox 3.10 / no specialists)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"
DOCS = ROOT / "docs"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _fn(src: str, name: str) -> str:
    needle = f"def {name}"
    start = src.index(needle)
    next_def = len(src)
    for token in ("\ndef ", "\nclass ", "\n@"):
        p = src.find(token, start + 1)
        if p != -1:
            next_def = min(next_def, p)
    return src[start:next_def]


def test_live_channel_swallows_importerror_only():
    src = _read("helpers.py")
    chunk = _fn(src, "_live_channel")
    assert "except ImportError" in chunk
    assert "except Exception" not in chunk
    assert "fail loud" in chunk
    assert "return None" in chunk
