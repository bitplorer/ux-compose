"""ux-dom's ``runtime/`` alias module is going away (ux-dom F-18 follow-up).

ux-compose imports the Document plugins from top-level ``ux_dom`` instead, so
it keeps working on both the pinned ux-dom and a ux-dom without ``runtime/``.

Scanned: Python under ``src/``, ``apps/``, ``examples/``; Python code blocks in
every ``*.md``; and the files ``create-app`` generates.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from ux_compose.scaffold import create_app

ROOT = Path(__file__).resolve().parents[2]
PY_DIRS = ("src", "apps", "examples")
SKIP_PARTS = {"__pycache__", "node_modules", "site-packages"}
FENCE = re.compile(r"^```(?:python|py|python3)\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)
TEXT_FORMS = re.compile(
    r"\bimport\s+ux_dom\.runtime\b"
    r"|\bfrom\s+ux_dom\.runtime\b"
    r"|\bfrom\s+ux_dom\s+import\s+\(?[^)\n]*\bruntime\b"
)


def _is_runtime(module: str) -> bool:
    return module == "ux_dom.runtime" or module.startswith("ux_dom.runtime.")


def _source_hits(source: str, where: str, *, fragment: bool = False) -> list[str]:
    """Every ``ux_dom.runtime`` import in *source*, in any form."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        if not fragment:
            raise
        # Doc snippets may be fragments; fall back to the textual forms.
        return [where] if TEXT_FORMS.search(source) else []
    hits: list[str] = []
    for node in ast.walk(tree):
        bad = False
        if isinstance(node, ast.Import):
            bad = any(_is_runtime(a.name) for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            bad = _is_runtime(node.module) or (
                node.module == "ux_dom" and any(a.name == "runtime" for a in node.names)
            )
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # Generated sources (scaffold templates) and import_module("…").
            bad = _is_runtime(node.value) or bool(TEXT_FORMS.search(node.value))
        if bad:
            hits.append(f"{where}:{node.lineno}")
    return hits


def _files(pattern: str, tops: tuple[Path, ...]) -> list[Path]:
    out: list[Path] = []
    for top in tops:
        for path in sorted(top.rglob(pattern)):
            rel = path.relative_to(ROOT).parts
            if SKIP_PARTS.intersection(rel) or any(p.startswith(".") for p in rel):
                continue
            out.append(path)
    return out


def test_no_ux_dom_runtime_imports_in_python():
    hits: list[str] = []
    for py in _files("*.py", tuple(ROOT / d for d in PY_DIRS)):
        hits += _source_hits(py.read_text(encoding="utf-8"), str(py.relative_to(ROOT)))
    assert hits == []


def test_no_ux_dom_runtime_imports_in_markdown_code_blocks():
    hits: list[str] = []
    for md in _files("*.md", (ROOT,)):
        for block in FENCE.findall(md.read_text(encoding="utf-8")):
            hits += _source_hits(block, str(md.relative_to(ROOT)), fragment=True)
    assert hits == []


def test_no_ux_dom_runtime_imports_in_create_app_output(tmp_path):
    root = create_app(tmp_path / "demo", name="demo", level="auto", host="auto")
    hits: list[str] = []
    for py in sorted(root.rglob("*.py")):
        hits += _source_hits(py.read_text(encoding="utf-8"), py.name)
    assert hits == []


def test_top_level_ux_dom_exports_document_plugins():
    from ux_dom import Channel, Csp, Document, Htmx, XElement

    doc = Document(head=[], body=[], ensure_csrf_token=False)
    assert doc.use(XElement(), Htmx(), Csp.auto(), Channel.optional()) is doc
