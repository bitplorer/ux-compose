"""Doctor — protective coach for ux-compose.

Residuals (kit import, leftover aliases) are teaching, not kill.
"""
from __future__ import annotations

import ast
import os
import posixpath
import re
import socket
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from importlib.util import find_spec
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
    "scan_store_precedence",
    "secret_readiness",
    "scan_product_readiness",
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


# Not app source: tool caches, environments, installed packages, build output
# (``uxcompose build --package`` writes dist/<name>/, a second copy of the app).
SKIP_DIRS = frozenset(
    {"__pycache__", ".venv", "venv", ".git", ".pytest_cache", "node_modules", ".mypy_cache", "dist"}
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
    """Teach: the brand bar belongs on ``wrap=``, not inside ``routes/*.py`` render().

    Residual (not fail-closed). Flags ``stunning-root`` and ``class="nav"``
    + brand patterns that nest the brand bar into morph payloads.
    """
    diagnostics: list[str] = []
    teach = (
        "The brand bar belongs on Document / build(wrap=brand_wrap(document, brand=...)), "
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
                f"residual in {p}: render() contains the brand bar ({', '.join(hits)}). {teach}"
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


def scan_store_precedence() -> list[str]:
    """Fail-loud when both store envs are set.

    Channel prefers ``REDIS_URL`` and ignores ``UXCOMPOSE_STATE_STORE``.
    Exporting both is a lie (sqlite looks like the session; it is not).
    """
    file_path = (os.environ.get("UXCOMPOSE_STATE_STORE") or "").strip()
    redis = (os.environ.get("REDIS_URL") or "").strip()
    if not file_path or not redis:
        return []
    return [
        "Store precedence violation: both UXCOMPOSE_STATE_STORE and REDIS_URL "
        "are set; Channel prefers Redis and ignores the sqlite path. Unset one."
    ]


def secret_readiness(env: Mapping[str, str] | None = None) -> str | None:
    """One line when Channel attach would refuse the secret config, else None.

    The rule is ux-behavior's ``attach_secret_problem``, the check ``attach()``
    itself runs (length from ux-channel). Nothing is decided here.
    """
    from ux_behavior.wire import attach_secret_problem

    problem = attach_secret_problem(env)
    return f"Channel secret refused: {problem}" if problem else None


def _row(mark: str, name: str, detail: str) -> str:
    return f"[{mark:4}] {name}: {detail}"


def _lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]


def _port_row(host: str, port: int) -> str:
    """The bind uvicorn makes: SO_REUSEADDR, so TIME_WAIT does not count."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except socket.gaierror:
            return _row("WARN", f"port:{port}", f"cannot resolve host {host}")
        except OSError:
            return _row("WARN", f"port:{port}", f"in use on {host}:{port}")
    return _row("OK", f"port:{port}", f"free on {host}:{port}")


def _docker_regex(pattern: str) -> re.Pattern[str]:
    """moby/patternmatcher: ``**`` spans directories; ``*``/``?`` stay in one."""
    out, i = "", 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**", i):
            i += 2
            if pattern.startswith("/", i):
                i += 1
            out += ".*" if i == len(pattern) else "(.*/)?"
            continue
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c == "\\" and i + 1 < len(pattern):
            i += 1
            if pattern[i].isalnum():
                # Docker hands "\\d" etc. to Go regexp: a class or a syntax error.
                raise ValueError(pattern)
            out += re.escape(pattern[i])
        elif c == "[" and "]" in pattern[i + 1 :]:
            end = pattern.index("]", i + 1)
            out += "[" + pattern[i + 1 : end] + "]"
            i = end
        else:
            out += re.escape(c)
        i += 1
    return re.compile(out)


def _dockerignored(dockerignore: Path, path: str) -> bool:
    """Docker's ``.dockerignore`` reading: last matching line wins, ``!`` re-includes."""
    if not dockerignore.is_file():
        return False
    ignored = False
    for raw in dockerignore.read_text(encoding="utf-8").splitlines():
        if raw.startswith("#"):
            continue
        pattern = raw.strip()
        if not pattern:
            continue
        include = pattern.startswith("!")
        if include:
            pattern = pattern[1:].strip()
        pattern = posixpath.normpath(pattern).lstrip("/") or "/"
        parts = path.split("/")
        parents = ("/".join(parts[:n]) for n in range(len(parts), 0, -1))
        if any(_docker_regex(pattern).fullmatch(p) for p in parents):
            ignored = not include
    return ignored


def _dotenv_row(root: Path) -> str:
    if not (root / ".env").exists():
        return _row("OK", ".env", "absent")
    if (root / "Dockerfile").is_file():
        try:
            ignored = _dockerignored(root / ".dockerignore", ".env")
        except ValueError as exc:
            return _row(
                "FAIL",
                ".env",
                f"present; .dockerignore pattern {str(exc)!r} cannot be checked "
                "(backslash before a letter or digit)",
            )
        if not ignored:
            return _row("FAIL", ".env", "present and not in .dockerignore — docker build would copy it")
    return _row("WARN", ".env", "present — do not ship; set secrets on the host")


def scan_product_readiness(
    root: str | Path,
    *,
    env: Mapping[str, str] | None = None,
    port: int | None = None,
    host: str = "0.0.0.0",
) -> list[str]:
    """``doctor --prod`` rows: ``[OK  |WARN|FAIL] name: detail``.

    Static: reads files under ``root`` and ``env``; never imports the app.
    Separate from the ``scan_*`` laws, which stay the same with or without it.
    """
    from ux_behavior.wire import debug_requests_dev

    from ux_compose.scaffold import scan_requirements

    root = Path(root)
    source = os.environ if env is None else env
    if not (root / "app.py").is_file():
        return [
            _row(
                "FAIL",
                "product",
                f"no app.py in {root.resolve()} — run uxcompose create-app, or pass the app root",
            )
        ]
    rows = [_row("OK", "product", "app.py")]
    for module in ("uvicorn", "fastapi"):
        if find_spec(module) is None:
            rows.append(
                _row(
                    "FAIL",
                    f"dep:{module}",
                    f"not importable in {sys.executable} — pip install -r requirements.txt",
                )
            )
        else:
            rows.append(_row("OK", f"dep:{module}", "importable"))
    req = root / "requirements.txt"
    if not req.is_file():
        rows.append(_row("FAIL", "requirements", "requirements.txt missing — deploys install from it"))
    elif (scan := scan_requirements(req)).problem:
        rows.append(_row("FAIL", "requirements", scan.problem))
    elif scan.unchecked:
        rows.append(_row("WARN", "requirements", "not checked: " + "; ".join(scan.unchecked)))
    else:
        rows.append(_row("OK", "requirements", "one line per distribution; names ux-compose"))
    if refused := secret_readiness(source):
        rows.append(_row("FAIL", "secret", f"{refused} — set UX_CHANNEL_SECRET on the host"))
    else:
        rows.append(_row("OK", "secret", "Channel attach can boot"))
    if debug_requests_dev(source):
        rows.append(
            _row("FAIL", "DEBUG", f"DEBUG={source.get('DEBUG')!r} is dev mode — unset it for prod")
        )
    else:
        rows.append(_row("OK", "DEBUG", "prod mode"))
    rows.append(_dotenv_row(root))
    render = root / "render.yaml"
    if render.is_file():
        if "UX_CHANNEL_SECRET" in render.read_text(encoding="utf-8"):
            rows.append(_row("OK", "deploy:render", "render.yaml declares UX_CHANNEL_SECRET"))
        else:
            rows.append(_row("FAIL", "deploy:render", "render.yaml does not declare UX_CHANNEL_SECRET"))
    for unit in sorted((root / "deploy").glob("*.service")):
        rel = unit.relative_to(root).as_posix()
        ok = any(
            ln.startswith(("EnvironmentFile=", "Environment=UX_CHANNEL_SECRET="))
            for ln in _lines(unit)
        )
        if ok:
            detail = f"{rel} sets EnvironmentFile or Environment=UX_CHANNEL_SECRET"
        else:
            detail = f"{rel} sets neither EnvironmentFile nor Environment=UX_CHANNEL_SECRET"
        rows.append(_row("OK" if ok else "FAIL", "deploy:vps", detail))
    if port is not None:
        rows.append(_port_row(host, port))
    return rows


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
        "Install ux-channel @ 0ffe8e9 (floor 985e58a) and cek-host>=0.2.0."
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
                expanded.extend(
                    f for f in pp.rglob("*.py") if SKIP_DIRS.isdisjoint(f.relative_to(pp).parts)
                )
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
    diagnostics.extend(scan_store_precedence())
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
    parser.add_argument(
        "--prod", action="store_true", help="also check product readiness (first path is the app root)"
    )
    parser.add_argument("--port", type=int, help="with --prod: warn when HOST:PORT cannot be bound")
    parser.add_argument("--host", help="with --port: the address the app binds (default 0.0.0.0)")
    args = parser.parse_args(argv)
    if args.port is not None and not args.prod:
        parser.error("--port needs --prod")
    if args.host is not None and args.port is None:
        parser.error("--host needs --port")
    res = doctor(args.paths or ["."], fail=False)
    print("ux-compose doctor — protective coach")
    print(f"  Progressive level available: L{res.level_available}")
    failed = False
    if res.diagnostics:
        failed = any(
            "violation" in d.lower()
            or "dual-document risk" in d.lower()
            or "incomplete stack" in d.lower()
            for d in res.diagnostics
        )
        for d in res.diagnostics:
            print(f"    - {d}")
    else:
        print("  Isolation: OK — product autonomy and additive levels on a complete install.")
    if args.prod:
        rows = scan_product_readiness(
            (args.paths or ["."])[0], port=args.port, host=args.host or "0.0.0.0"
        )
        print("  Product readiness:")
        for row in rows:
            print(f"  {row}")
        failed = failed or any(row.startswith("[FAIL]") for row in rows)
    return 0 if args.no_fail or not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
