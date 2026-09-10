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
    "scan_render_chrome",
    "scan_cek_host",
    "scan_fastapi_docs_collision",
    "scan_store_clone",
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
    "ux_compose.routing.adapters",
    'host="starlette"', "host='starlette'",
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


_STORE_CLONE_CLASS_NAMES = frozenset(
    {
        "FileStateStore",
        "MemoryStateStore",
        "RedisStateStore",
        "StateConflict",
        "EditSlot",
    }
)


def scan_store_clone(paths: Iterable[str | Path]) -> list[str]:
    """Ownership Law: Channel owns StateStore. Compose must not clone it.

    ``serve_state.py`` is lifecycle (env / path / prepare / clear / drop).
    A second ``class FileStateStore`` in this tree is the PR #58 failure.
    """
    diagnostics: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists() or p.suffix != ".py":
            continue
        sp = _norm(p)
        if "ux_compose/wire" in sp:
            continue
        if "/tests/" in sp:
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in _STORE_CLONE_CLASS_NAMES:
                diagnostics.append(
                    f"Ownership violation in {p}: cloned StateStore class "
                    f"`{node.name}`. Channel owns stores; compose "
                    f"serve_state.py is lifecycle only (ADR 0006)."
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


_RENDER_CHROME_SKIP = ("/tests/", "/src/ux_compose/", "site-packages")
_STUNNING_ROOT = "stunning-root"
_NAV_CLASS = (
    'class="nav"',
    "class='nav'",
    'className="nav"',
    "className='nav'",
)
_BRAND_MARKS = (
    "class=\"brand\"",
    "class='brand'",
    "className=\"brand\"",
    "className='brand'",
    "StunningCek",
)


def _is_routes_file(path: Path) -> bool:
    parts = Path(_norm(path)).parts
    return "routes" in parts and path.suffix == ".py"


def _render_chunks(src: str) -> list[str]:
    try:
        tree = ast.parse(src)
    except Exception:
        return []
    chunks: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "render":
            chunk = ast.get_source_segment(src, node)
            if not chunk:
                lines = src.splitlines()
                start = max(0, (node.lineno or 1) - 1)
                end = node.end_lineno or start + 1
                chunk = "\n".join(lines[start:end])
            if chunk:
                chunks.append(chunk)
    return chunks


def scan_render_chrome(paths: Iterable[str | Path]) -> list[str]:
    """Teach: GET chrome belongs on ``wrap=``, not inside ``routes/*.py`` render().

    Residual (not fail-closed). Flags ``stunning-root`` and ``class="nav"``
    + brand patterns that nest chrome into morph payloads.
    """
    diagnostics: list[str] = []
    teach = (
        "GET chrome belongs on Document / build(wrap=brand_wrap(document, brand=...)), "
        "not in render(). Morph payloads stay fragments."
    )
    for raw in paths:
        p = Path(raw)
        if not p.exists() or not _is_routes_file(p):
            continue
        sp = _norm(p)
        if any(token in sp for token in _RENDER_CHROME_SKIP):
            continue
        try:
            src = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for chunk in _render_chunks(src):
            hits: list[str] = []
            if _STUNNING_ROOT in chunk:
                hits.append(_STUNNING_ROOT)
            nav = any(token in chunk for token in _NAV_CLASS)
            brand = any(token in chunk for token in _BRAND_MARKS)
            if nav and brand:
                hits.append('class="nav" brand')
            elif nav:
                hits.append('class="nav"')
            if not hits:
                continue
            diagnostics.append(
                f"residual in {p}: render() contains GET chrome ({', '.join(hits)}). {teach}"
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
    return diagnostics


_CEK_SKIP = ("off", "0", "false", "no", "adapt")

_FASTAPI_RESERVED_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})
_FASTAPI_DOCS_TEACH = (
    "FastAPI reserves /docs, /redoc, and /openapi.json for Swagger when "
    "build(openapi=True). Prefer a product path such as /about, or keep "
    "openapi off (the default)."
)


def scan_fastapi_docs_collision(
    paths: Iterable[str | Path],
    *,
    route_paths: Iterable[str] | None = None,
) -> list[str]:
    """Residual: surface URL collides with FastAPI OpenAPI defaults.

    Product hosts disable Swagger by default so ``routes/docs.py`` can own
    GET ``/docs``. The warn still teaches the collision and recommends
    ``/about`` when OpenAPI is opted in.
    """
    from ux_compose.routing.core import http_path

    found: set[str] = set()
    for raw in paths or []:
        p = Path(raw)
        if not p.exists() or not _is_routes_file(p):
            continue
        sp = _norm(p)
        if any(token in sp for token in _RENDER_CHROME_SKIP):
            continue
        parts = Path(sp).parts
        try:
            idx = parts.index("routes")
        except ValueError:
            continue
        segs = list(parts[idx + 1 :])
        if not segs:
            continue
        segs[-1] = Path(segs[-1]).stem
        url = http_path(*segs)
        if url in _FASTAPI_RESERVED_PATHS:
            found.add(url)
    for raw_path in route_paths or []:
        url = str(raw_path)
        if url in _FASTAPI_RESERVED_PATHS:
            found.add(url)
    return [
        f"residual: surface path {url} collides with FastAPI OpenAPI. {_FASTAPI_DOCS_TEACH}"
        for url in sorted(found)
    ]


def scan_cek_host(app: Any) -> list[str]:
    """Fail-loud when cek=require and Channel is live but Cap identity is not cek-runtime.

    Isolation: duck-type ``registry._caps`` (type name + ``kernel_ssot``).
    Product modules never import ``ux_channel``. ``_cek is None`` with a live
    Channel is treated as require (swallowed attach must not look healthy).
    """
    if app is None:
        return []
    channel = getattr(app, "_channel", None)
    if channel is None:
        return []
    mode = getattr(app, "_cek", None)
    mode_s = str(mode).strip().lower() if mode is not None else "require"
    if mode_s in _CEK_SKIP:
        return []
    caps = getattr(getattr(channel, "registry", None), "_caps", None)
    name = type(caps).__name__ if caps is not None else None
    ssot = getattr(caps, "kernel_ssot", None) if caps is not None else None
    if name == "CekHostCapService" or ssot == "cek-runtime":
        return []
    return [
        "Cap Host identity violation: cek=require with live Channel but "
        f"registry._caps is {name!r} (kernel_ssot={ssot!r}); "
        "expected CekHostCapService / kernel_ssot='cek-runtime'. "
        "Install ux-channel (pin ≥ d0fe716), cek-host>=0.1.3, cek-surface>=0.1.3."
    ]


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


def _stack_diagnostics(caps: dict) -> list[str]:
    """Hard diagnostics when a pinned specialist is missing."""
    labels = (
        ("ux_dom", "ux-dom"),
        ("ux_behavior", "ux-behavior"),
        ("ux_channel", "ux-channel"),
        ("ux_motion", "ux-motion"),
    )
    missing = [label for key, label in labels if not caps.get(key)]
    if not missing:
        return []
    return [
        "incomplete stack: missing "
        + ", ".join(missing)
        + ". ux-compose hard-depends on ux-dom + ux-channel + ux-behavior + ux-motion "
        "(Python ≥3.14). Install the pinned specialists."
    ]


def _teaching_for_level(level: int, caps: dict) -> list[str]:
    lines = []
    stack_ok = all(
        caps.get(key)
        for key in ("ux_dom", "ux_behavior", "ux_channel", "ux_motion")
    )
    if not stack_ok:
        lines.append(
            "Complete install first: pip install -e \".[dev]\" (clone) or "
            "pip install -r requirements.txt (create-app). Python ≥3.14. "
            "That pulls ux-dom, ux-channel, ux-behavior, and ux-motion. "
            "Levels are additive after the stack is present — not an unlock ladder."
        )
    else:
        lines.append(
            f"Full stack present (L{level}). Levels are additive: "
            "Level 1 page units stay correct at L2/L3."
        )
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
    app: Any = None,
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
    diagnostics.extend(_stack_diagnostics(caps))
    expanded: list[Path] = []
    if paths:
        for p in paths:
            pp = Path(p)
            if pp.is_dir():
                expanded.extend(pp.rglob("*.py"))
            elif pp.suffix == ".py":
                expanded.append(pp)
        diagnostics.extend(scan_isolation(expanded))
        diagnostics.extend(scan_store_clone(expanded))
        diagnostics.extend(scan_dual_document(expanded))
        diagnostics.extend(scan_kit_product_imports(expanded))
        diagnostics.extend(scan_leftover_aliases(expanded))
        diagnostics.extend(scan_render_chrome(expanded))
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
    diagnostics.extend(scan_fastapi_docs_collision(expanded, route_paths=route_paths))
    if app is None and bundle is not None:
        app = getattr(bundle, "compose_app", None) or getattr(bundle, "app", None)
    diagnostics.extend(scan_cek_host(app))
    hard = [
        d
        for d in diagnostics
        if "violation" in d.lower()
        or "dual-document risk" in d.lower()
        or "incomplete stack" in d.lower()
    ]
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
        hard = any(
            "violation" in d.lower()
            or "dual-document risk" in d.lower()
            or "incomplete stack" in d.lower()
            for d in res.diagnostics
        )
        for d in res.diagnostics:
            print(f"    - {d}")
        return 0 if args.no_fail or not hard else 1
    print("  Isolation: OK — product autonomy and additive levels on a complete install.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
