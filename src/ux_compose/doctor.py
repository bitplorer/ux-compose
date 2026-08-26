"""
Doctor — protective coach for ux-compose.

Enforces Isolation Law, dual-Document risks, and reports progressive capabilities.
Messages teach the laws and frame failures as protection of product autonomy.
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional

__all__ = ["doctor", "DoctorResult", "IsolationViolation", "scan_isolation"]


class IsolationViolation(Exception):
    """Raised when product code imports the wire or violates a hard law."""


FORBIDDEN_IMPORTS = {
    "ux_channel",
    "cek",
    "cek_host",
    "cek_surface",
    "MotionChannel",
}


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
        sp = str(p).replace("\\\\", "/")
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
        sp = str(p).replace("\\", "/")
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
    # Group by parent directory — only warn when *same product package* has multiple
    if len(doc_calls) > 1:
        diagnostics.append(
            f"Possible dual-Document risk: Document() appears {len(doc_calls)} times "
            f"({', '.join(doc_calls[:3])}...). Document SSoT Law requires exactly one "
            f"Document that owns the HTML shell and runtime placement. Prefer a single "
            f"Document constructed at boot and passed/used throughout. "
            f"(examples/ may legitimately show multiple patterns — scan product packages only.)"
        )
    return diagnostics


@dataclass
class DoctorResult:
    ok: bool = True
    level_available: int = 0
    diagnostics: List[str] = field(default_factory=list)
    capabilities: dict = field(default_factory=dict)
    teaching: List[str] = field(default_factory=list)
    # Optional evidence from a sealed SurfaceBundle (additive)
    surfaces: List[str] = field(default_factory=list)
    routes: List[str] = field(default_factory=list)

    def raise_if_failed(self):
        if not self.ok:
            raise IsolationViolation("\n".join(self.diagnostics))


def _detect_capabilities() -> dict:
    from ux_compose.dx.probe import probe

    pr = probe()
    caps = {
        "ux_dom": pr.has_dom,
        "ux_behavior": pr.has_behavior,
        "ux_motion": pr.has_motion,
        "ux_channel": pr.has_channel,
        "directory_routes": True,
    }
    return caps


def _teaching_for_level(level: int, caps: dict) -> list[str]:
    """Progressive unlock teaching messages."""
    lines = []
    if level < 1:
        lines.append(
            "You are at Level 0 (static). To unlock offline interactive Components + MorphState + @action: "
            "pip install ux-behavior  then  App.boot(...).use_behavior()"
        )
    if level < 2 and caps.get("ux_behavior"):
        lines.append(
            "You are at Level 1 (offline interactive). To unlock live Caps + morph over the wire: "
            "pip install ux-channel  then  app.use_channel(asgi_app=...)"
        )
    if level < 3 and caps.get("ux_channel"):
        lines.append(
            "You are at Level 2 (live). To unlock choreographed presence + Scenes: "
            "pip install ux-motion  then  app.use_motion()"
        )
    if level >= 3:
        lines.append("Full progressive stack available (L3). Isolation + Caps + Motion are all first-class.")
    if caps.get("directory_routes"):
        lines.append(
            "Page-unit path available: uxcompose create-app + build() "
            "(routes/ + stem match via DirectoryRoutes). "
            "App.mount / mount_surfaces is a secondary door for tests and surfaces."
        )
    lines.append(
        "Progressive Superpower Contract: code written at Level 1 remains correct and unchanged "
        "when you unlock higher levels. Zero rewrite."
    )
    return lines


def doctor(
    paths: Optional[Iterable[str | Path]] = None,
    *,
    fail: bool = True,
    bundle: Any = None,
) -> DoctorResult:
    """
    Run the protective coach.

    - Scans for Isolation violations and dual-Document heuristics
    - Reports progressive specialists + DirectoryRoutes (page-unit path)
    - Emits teaching messages for the next unlock and create-app / build() guidance
    - Optionally records evidence from a sealed SurfaceBundle (surfaces, routes)
    - Fails closed (raises) when fail=True and hard violations found

    ``bundle`` is optional and additive — pass the return value of build() /
    App.mount / mount_surfaces for route-table evidence without changing scan behaviour.
    """
    caps = _detect_capabilities()
    level = 0
    if caps.get("ux_behavior"):
        level = 1
    if caps.get("ux_channel"):
        level = 2
    if caps.get("ux_motion"):
        level = 3

    diagnostics: list[str] = []
    expanded: list[Path] = []
    if paths:
        for p in paths:
            pp = Path(p)
            if pp.is_dir():
                expanded.extend(pp.rglob("*.py"))
            elif pp.suffix == ".py":
                expanded.append(pp)
        diagnostics.extend(scan_isolation(expanded))
        diagnostics.extend(scan_dual_document(expanded))

    teaching = _teaching_for_level(level, caps)

    surface_ids: list[str] = []
    route_paths: list[str] = []
    if bundle is not None:
        surfaces_map = getattr(bundle, "surfaces", None) or {}
        if isinstance(surfaces_map, dict):
            surface_ids = sorted(str(k) for k in surfaces_map.keys())
        table = getattr(bundle, "route_table", None) or []
        if isinstance(table, list):
            for rec in table:
                if isinstance(rec, dict) and rec.get("path"):
                    route_paths.append(str(rec["path"]))
        errs = getattr(bundle, "errors", None) or []
        if errs:
            for e in errs:
                diagnostics.append(f"surface bundle: {e}")
        if not getattr(bundle, "sealed", True):
            diagnostics.append("surface bundle is not sealed — mount may be incomplete")

    result = DoctorResult(
        ok=len([d for d in diagnostics if "violation" in d.lower() or "risk" in d.lower()]) == 0,
        level_available=level,
        diagnostics=diagnostics,
        capabilities=caps,
        teaching=teaching,
        surfaces=surface_ids,
        routes=route_paths,
    )
    if fail and not result.ok:
        result.raise_if_failed()
    return result


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="ux-compose doctor — protective coach for Isolation, Document SSoT, and progressive unlock"
    )
    parser.add_argument("paths", nargs="*", help="Python files or dirs to scan (default: .)")
    parser.add_argument("--no-fail", action="store_true", help="Report only, do not raise on violations")
    args = parser.parse_args(argv)
    paths = args.paths or ["."]
    # Never raise from the CLI — print the report, then exit 1.
    res = doctor(paths, fail=False)

    print("ux-compose doctor — protective coach")
    print(f"  Progressive level available: L{res.level_available}")
    print("  Capabilities:")
    for k, v in res.capabilities.items():
        print(f"    {'✓' if v else '·'} {k}")
    if res.teaching:
        print("  Next unlock guidance:")
        for t in res.teaching:
            print(f"    → {t}")
    if res.surfaces:
        print(f"  Surfaces: {', '.join(res.surfaces)}")
    if res.routes:
        print(f"  Routes: {', '.join(res.routes)}")
    if res.diagnostics:
        print("  Diagnostics:")
        for d in res.diagnostics:
            print(f"    - {d}")
        return 0 if args.no_fail else 1
    if not res.ok:
        return 0 if args.no_fail else 1
    print("  Isolation: OK — product autonomy and offline progressive path protected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
