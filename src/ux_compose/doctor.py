"""
Doctor — protective coach for ux-compose.

Enforces Isolation Law, dual-Document risks, and reports progressive capabilities.
Messages teach the laws and frame failures as protection of product autonomy.
Residuals (kit import in product trees, leftover aliases) are teaching, not kill.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional

__all__ = [
    "doctor",
    "DoctorResult",
    "IsolationViolation",
    "scan_isolation",
    "scan_kit_product_imports",
    "scan_leftover_aliases",
]


class IsolationViolation(Exception):
    """Raised when product code imports the wire or violates a hard law."""


FORBIDDEN_IMPORTS = {
    "ux_channel",
    "cek",
    "cek_host",
    "cek_surface",
    "MotionChannel",
}

# Paths where `from ux_compose.kit import` is legitimate.
_KIT_IMPORT_SKIP = (
    "/tests/",
    "/src/ux_compose/",
    "/examples/",
)

# Leftover names that still exist so old tests do not break — teach, do not delete.
# host="batteries" is the keyword form; use_host("batteries") is the call form.
# They are different substrings. Scan both.
_LEFTOVER_TOKENS = (
    'host="batteries"',
    "host='batteries'",
    'use_host("batteries")',
    "use_host('batteries')",
    "DirectoryRouter",
    'serve="webassets"',
    "serve='webassets'",
)


def _norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _is_forbidden(name: str) -> bool:
    if not name:
        return False
    for f in FORBIDDEN_IMPORTS:
        if name == f or name.startswith(f + "."):
            return True
    return False


def scan_isolation(paths: Iterable[str | Path]) -> list[str]:
    """AST-scan for Isolation Law violations. Returns teaching diagnostics."""
    diagnostics: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists() or p.suffix != ".py":
            continue
        sp = _norm(p)
        if "ux_compose/wire" in sp:
            continue  # legitimate door
        try:
            src = p.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(p))
        except Exception as e:
            diagnostics.append(f"Could not parse {p}: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden(alias.name):
                        diagnostics.append(
                            f"Isolation violation in {p}: importing `{alias.name}` "
                            f"pulls the live wire into domain logic and destroys the "
                            f"offline progressive guarantee. Move the import behind "
                            f"the framework `wire/` door. Isolation exists to protect "
                            f"your product autonomy."
                        )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if _is_forbidden(mod):
                    diagnostics.append(
                        f"Isolation violation in {p}: `from {mod} import ...` "
                        f"pulls the live wire into domain logic and destroys the "
                        f"offline progressive guarantee. Move the import behind "
                        f"the framework `wire/` door. Isolation exists to protect "
                        f"your product autonomy."
                    )
                for alias in node.names:
                    full = f"{mod}.{alias.name}" if mod else alias.name
                    if _is_forbidden(full) or _is_forbidden(alias.name):
                        diagnostics.append(
                            f"Isolation violation in {p}: from {mod} import {alias.name}. "
                            f"Same protection rationale — keep product code pure and offline-capable."
                        )
    return diagnostics


def scan_dual_document(paths: Iterable[str | Path]) -> list[str]:
    """Heuristic: flag multiple Document(...) constructions in the same *product* module tree.

    Document SSoT Law: exactly one Document owns the HTML shell.
    Skips tests/ and site-packages so framework self-tests do not raise false product alarms.
    """
    diagnostics: list[str] = []
    doc_calls: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists() or p.suffix != ".py":
            continue
        sp = _norm(p)
        if "/tests/" in sp or sp.endswith("/tests") or "site-packages" in sp:
            continue
        try:
            src = p.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(p))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name == "Document":
                    doc_calls.append(f"{p}:{getattr(node, 'lineno', '?')}")
    if len(doc_calls) > 1:
        diagnostics.append(
            f"Possible dual-Document risk: Document() appears {len(doc_calls)} times "
            f"({', '.join(doc_calls[:3])}...). Document SSoT Law requires exactly one "
            f"Document that owns the HTML shell and runtime placement. Prefer a single "
            f"Document constructed at boot and passed/used throughout. "
            f"(examples/ may legitimately show multiple patterns — scan product packages only.)"
        )
    return diagnostics


def _skip_kit_scan(path: Path) -> bool:
    sp = _norm(p) if False else _norm(path)
    if "site-packages" in sp:
        return True
    for token in _KIT_IMPORT_SKIP:
        if token in sp:
            return True
    return False
