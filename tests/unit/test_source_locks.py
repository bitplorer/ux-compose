"""Source-level locks. Do not import ux_compose (sandbox 3.10 / no specialists)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"
DOCS = ROOT / "docs"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _fn(src: str, name: str) -> str:
    m = re.search(rf"^([ \t]*)def {re.escape(name)}\\b", src, re.M)
    if not m:
        raise AssertionError(f"def {name} not found")
    indent = m.group(1)
    start = m.start()
    rest = src[m.end() :]
    nxt = re.search(rf"\\n{re.escape(indent)}(?:def |class |@)", rest)
    end = m.end() + nxt.start() if nxt else len(src)
    return src[start:end]
