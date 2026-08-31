"""Doctor — protective coach for ux-compose.

Residuals (kit import, leftover aliases) are teaching, not kill.
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
    "ux_channel", "cek", "cek_host", "cek_surface", "MotionChannel",
}
_KIT_IMPORT_SKIP = ("/tests/", "/src/ux_compose/", "/examples/")
_LEFTOVER_TOKENS = (
    'host="batteries"', "host='batteries'",
    'use_host("batteries")', "use_host('batteries')",
    "DirectoryRouter", 'serve="webassets"', "serve='webassets'",
)


def _norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _is_forbidden(name: str) -> bool:
    if not name:
        return False
    return any(name == f or name.startswith(f + ".") for f in FORBIDDEN_IMPORTS)


def scan_isolation(paths: Iterable[str | Path]) -> list[str]:
    diagnostics: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists() or p.suffix != ".py":
            continue
        if "ux_compose/wire" in _norm(p):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except Exception as e:
            diagnostics.append(f"Could not parse {p}: {e}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden(alias.name):
                        diagnostics.append(
                            f"Isolation violation in {p}: importing `{alias.name}`. Move behind wire/."
                        )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if _is_forbidden(mod):
                    diagnostics.append(
                        f"Isolation violation in {p}: `from {mod} import ...`. Move behind wire/."
                    )
                for alias in node.names:
                    full = f"{mod}.{alias.name}" if mod else alias.name
                    if _is_forbidden(full) or _is_forbidden(alias.name):
                        diagnostics.append(
                            f"Isolation violation in {p}: from {mod} import {alias.name}."
                        )
    return diagnostics


def scan_dual_document(paths: Iterable[str | Path]) -> list[str]:
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
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "id", None) or getattr(func, "attr", None)
                if name == "Document":
                    doc_calls.append(f"{p}:{getattr(node, 'lineno', '?')}")
    if len(doc_calls) > 1:
        diagnostics.append(
            f"Possible dual-Document risk: Document() appears {len(doc_calls)} times "
            f"({', '.join(doc_calls[:3])}...)."
        )
    return diagnostics


def _skip_kit_scan(path: Path) -> bool:
    sp = _norm(path)
    return "site-packages" in sp or any(token in sp for token in _KIT_IMPORT_SKIP)


def scan_kit_product_imports(paths: Iterable[str | Path]) -> list[str]:
    diagnostics: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists() or p.suffix != ".py" or _skip_kit_scan(p):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            mod = node.module or ""
            if mod == "ux_compose.kit" or mod.startswith("ux_compose.kit."):
                names = ", ".join(a.name for a in node.names)
                diagnostics.append(
                    f"residual in {p}: `from {mod} import {names}`. Use `uxcompose add`."
                )
    return diagnostics


def scan_leftover_aliases(paths: Iterable[str | Path]) -> list[str]:
    diagnostics: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists() or p.suffix != ".py":
            continue
        sp = _norm(p)
        if "/tests/" in sp or "/src/ux_compose/" in sp or "site-packages" in sp:
            continue
        try:
            src = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for token in _LEFTOVER_TOKENS:
            if token in src:
                diagnostics.append(
                    f"residual in {p}: leftover `{token}`. Clock A host is FastAPI."
                )
                break
    return diagnostics


@dataclass
class DoctorResult:
    ok: bool = True
    level_available: int = 0
    diagnostics: List[str] = field(default_factory=list)
    capabilities: dict = field(default_factory=dict)
    teaching: List[str] = field(default_factory=list)
    surfaces: List[str] = field(default_factory=list)
    routes: List[str] = field(default_factory=list)

    def raise_if_failed(self):
        if not self.ok:
            raise IsolationViolation("\n".join(self.diagnostics))


def _detect_capabilities() -> dict:
    from ux_compose.dx.probe import probe
    pr = probe()
    return {
        "ux_dom": pr.has_dom,
        "ux_behavior": pr.has_behavior,
        "ux_motion": pr.has_motion,
        "ux_channel": pr.has_channel,
        "directory_routes": True,
    }


def _teaching_for_level(level: int, caps: dict) -> list[str]:
    lines = []
    if level < 1:
        lines.append("Level 0. Unlock L1: pip install ux-behavior then App.boot(...).use_behavior()")
    if level < 2 and caps.get("ux_behavior"):
        lines.append("Level 1. Unlock L2: pip install ux-channel then app.use_channel(asgi_app=...)")
    if level < 3 and caps.get("ux_channel"):
        lines.append("Level 2. Unlock L3: pip install ux-motion then app.use_motion()")
    if level >= 3:
        lines.append("Full progressive stack available (L3).")
    if caps.get("directory_routes"):
        lines.append(
            "Product path: uxcompose create-app + serve dev + build() "
            "(routes/ + stem match via DirectoryRoutes). "
            "App.mount is the page-unit scan step, not a second product."
        )
    lines.append("One catalog: uxcompose add copies a kit widget. Do not import kit in product apps.")
    try:
        from ux_compose.attach_notes import format_report
        lines.extend(format_report())
    except Exception:
        pass
    return lines


def doctor(
    paths: Optional[Iterable[str | Path]] = None,
    *,
    fail: bool = True,
    bundle: Any = None,
) -> DoctorResult:
    caps = _detect_capabilities()
    if caps.get("ux_motion"):
        level = 3
    elif caps.get("ux_channel"):
        level = 2
    elif caps.get("ux_behavior"):
        level = 1
    else:
        level = 0
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
        diagnostics.extend(scan_kit_product_imports(expanded))
        diagnostics.extend(scan_leftover_aliases(expanded))
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
        for e in getattr(bundle, "errors", None) or []:
            diagnostics.append(f"surface bundle: {e}")
        if not getattr(bundle, "sealed", True):
            diagnostics.append("surface bundle is not sealed — mount may be incomplete")
    hard = [d for d in diagnostics if "violation" in d.lower() or "dual-document risk" in d.lower()]
    result = DoctorResult(
        ok=len(hard) == 0,
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
    parser = argparse.ArgumentParser(description="ux-compose doctor")
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--no-fail", action="store_true")
    args = parser.parse_args(argv)
    res = doctor(args.paths or ["."], fail=False)
    print("ux-compose doctor — protective coach")
    print(f"  Progressive level available: L{res.level_available}")
    if res.diagnostics:
        hard = any("violation" in d.lower() or "dual-document risk" in d.lower() for d in res.diagnostics)
        for d in res.diagnostics:
            print(f"    - {d}")
        return 0 if args.no_fail or not hard else 1
    print("  Isolation: OK — product autonomy and offline progressive path protected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
