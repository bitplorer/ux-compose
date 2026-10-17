"""Examples stay direct: no thin tag-wrapper helpers, no kit-named helpers, and
every module states its purpose in one line (spec §5c)."""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

import ux_compose.dom as dom

ROOT = Path(__file__).resolve().parents[2]
DIRS = ("examples",)
TAGS = {n for n in dir(dom) if not n.startswith("_")}
FILES = sorted(p for d in DIRS for p in (ROOT / d).rglob("*.py"))


def _single_return_call(fn: ast.FunctionDef) -> str | None:
    body = [b for b in fn.body if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant))]
    if len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, ast.Call):
        f = body[0].value.func
        return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
    return None


def test_every_example_module_has_one_line_purpose():
    bad = [
        str(p.relative_to(ROOT))
        for p in FILES
        if not (ast.get_docstring(ast.parse(p.read_text(encoding="utf-8"))) or "").strip()
    ]
    assert bad == [], bad


def test_no_kit_named_helpers_in_examples():
    bad = []
    for p in FILES:
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and "kit" in n.name.lower():
                bad.append(f"{p.name}:{n.lineno} {n.name}")
    assert bad == [], bad


def test_no_thin_tag_wrappers_used_once():
    """A helper whose whole body is ``return <tag>(...)`` and is used at most
    once must be inlined into its caller. Reused helpers may stay."""
    bad = []
    for p in FILES:
        tree = ast.parse(p.read_text(encoding="utf-8"))
        calls = Counter(
            (c.func.attr if isinstance(c.func, ast.Attribute) else getattr(c.func, "id", None))
            for c in ast.walk(tree)
            if isinstance(c, ast.Call)
        )
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name not in {"render", "demo", "main"}:
                if _single_return_call(n) in TAGS and calls[n.name] <= 1:
                    bad.append(f"{p.name}:{n.lineno} {n.name}")
    assert bad == [], bad
