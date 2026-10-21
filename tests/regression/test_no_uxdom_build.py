"""ux-dom has no ``build`` verb and no ``dual_copy`` option: no compose source, doc or message names them.

Library JS has one source, package static ``/ux-dom/static/x_element.js``.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXT = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".html", ".cfg", ".ini", ".json", ".sh", ".js", ".css"}
SKIP = {".git", "tests", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
GONE = re.compile(r"ux[-_]?dom`?\s+`?build|dual[-_ ]copy", re.IGNORECASE)


def test_nothing_names_uxdom_build_or_dual_copy():
    hits = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if set(rel.parts) & SKIP or path.suffix not in TEXT or not path.is_file():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if GONE.search(line):
                hits.append(f"{rel}:{n}: {line.strip()}")
    assert hits == [], "\n".join(hits)
