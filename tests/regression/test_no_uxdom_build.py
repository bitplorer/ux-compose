"""ux-dom has no ``build`` verb: no compose source, doc or message names one."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXT = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".html", ".cfg", ".ini", ".json", ".sh", ".js", ".css"}
SKIP = {".git", "tests", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
VERB = re.compile(r"uxdom`?\s+`?build", re.IGNORECASE)


def test_nothing_names_a_uxdom_build_verb():
    hits = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if set(rel.parts) & SKIP or path.suffix not in TEXT or not path.is_file():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if VERB.search(line):
                hits.append(f"{rel}:{n}: {line.strip()}")
    assert hits == [], "\n".join(hits)
