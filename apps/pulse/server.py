"""Pulse host — live showcase of the locked ux-compose product path.

- Page units under routes/ via build(document=, wrap=, cek=require)
- Document SSoT (ux-dom hard dep; XElement default; HTMX opt-in)
- Additive attach: Behavior → Channel → Motion → Cap Host on a complete install
- Isolation Law: never imports ux_channel directly
- Style: Tailwind utility className (CDN stand-in for TailwindStyle/WebAssets)
- GET chrome via Document wrap; HX / morph stays fragment-only
- Feature matrix room: GET /matrix (see MATRIX.md)

Serve:
  PYTHONPATH=src:. uxcompose serve dev apps.pulse.server:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

from ux_compose import (
    App,
    a,
    div,
    doctor,
    footer,
    header,
    link,
    main,
    meta,
    nav,
    p,
    script,
    span,
    title,
)
from ux_compose.build import build as compose_build
from ux_compose.chrome import GET_CHROME_ATTR
from ux_compose.helpers import _serialize_tree
from ux_compose.routing.core import apply_html_document
from ux_dom import Document
from ux_dom.runtime import Channel, Csp, XElement

PACKAGE = Path(__file__).resolve().parent
STATIC = PACKAGE / "static"

try:
    from fastapi import Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    HAS_FASTAPI = False
    Request = None  # type: ignore
    HTMLResponse = None  # type: ignore
    JSONResponse = None  # type: ignore
    StaticFiles = None  # type: ignore


_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

NAV = (
    ("/", "Home"),
    ("/shop", "Shop"),
    ("/lab", "Lab"),
    ("/matrix", "Matrix"),
    ("/settings", "Settings"),
)


def _clean_args(args: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for k, v in (args or {}).items():
        if not isinstance(k, str) or not _IDENT.match(k):
            continue
        if k in {"action", "submit"}:
            continue
        if isinstance(v, (list, tuple)):
            v = v[0] if v else ""
        clean[k] = v
    return clean


def _parse_multipart(ctype: str, raw: bytes) -> dict[str, Any]:
    m = re.search(r"boundary=([^;]+)", ctype or "", re.I)
    if not m:
        return {}
    boundary = m.group(1).strip().strip('"')
    sep = b"--" + boundary.encode("ascii", "replace")
    out: dict[str, Any] = {}
    for part in raw.split(sep):
        part = part.lstrip(b"\r\n")
        if not part or part.startswith(b"--"):
            continue
        header_b, sep2, body_b = part.partition(b"\r\n\r\n")
        if not sep2:
            header_b, sep2, body_b = part.partition(b"\n\n")
        if not sep2:
            continue
        hm = re.search(br'name="([^"]+)"', header_b)
        if not hm:
            continue
        name = hm.group(1).decode("utf-8", "replace")
        val = body_b.rstrip(b"\r\n-")
        out[name] = val.decode("utf-8", "replace")
    return out


async def _parse_action_args(request: Any) -> dict[str, Any]:
    ctype = (request.headers.get("content-type") or "").lower()
    raw = await request.body()
    if "application/json" in ctype:
        try:
            body = await request.json()
            return _clean_args(body if isinstance(body, dict) else {})
        except Exception:
            return {}
    if "multipart/form-data" in ctype:
        return _clean_args(_parse_multipart(ctype, raw))
    parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
    return _clean_args({k: v[0] if v else "" for k, v in parsed.items()})


def _document():
    plugins = (XElement(), Csp.auto(), Channel.optional())
    return Document(
        head=[
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Pulse · ux-compose"),
            link(rel="preconnect", href="https://fonts.googleapis.com"),
            link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin="anonymous"),
            link(
                rel="stylesheet",
                href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Sans+3:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap",
            ),
            script(src="https://cdn.tailwindcss.com"),
        ],
        body=[],
        ensure_csrf_token=False,
    ).use(*[p for p in plugins if p is not None])


def _pulse_wrap(document: Any):
    """GET chrome (nav + foot) outside Component.render(). Morph stays a fragment."""
    if document is None or not callable(document):
        raise TypeError(
            "Pulse wrap requires a callable Document. "
            "Product path is build(document=, wrap=_pulse_wrap(document))."
        )

    def wrap(child: Any = None):
        links = [a(label, href=href) for href, label in NAV]
        chrome = header(
            a(
                "Pulse ",
                span("compose", className="text-amber-700 dark:text-amber-400"),
                href="/",
                className="font-serif text-lg tracking-tight",
            ),
            nav(*links, className="flex flex-wrap gap-1"),
            className=(
                "sticky top-0 z-20 flex items-center justify-between gap-4 "
                "border-b border-stone-200/80 bg-stone-50/90 px-4 py-4 backdrop-blur "
                "dark:border-stone-800 dark:bg-stone-950/90"
            ),
            **{GET_CHROME_ATTR: True},
        )
        foot = footer(
            "ux-compose · page units · additive L0–L3 attach · Isolation Law · HTMX opt-in",
            className="border-t border-stone-200 px-4 py-6 text-sm text-stone-500 dark:border-stone-800",
        )
        inner = main(child, id="main") if child is not None else main(id="main")
        return document(
            div(
                chrome,
                inner,
                foot,
                className=(
                    "mx-auto max-w-5xl bg-stone-50 text-stone-900 antialiased "
                    "dark:bg-stone-950 dark:text-stone-100"
                ),
            )
        )

    return wrap


def _html(tree: Any) -> str:
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    return _serialize_tree(tree)


def _html_response(tree: Any, *, status_code: int = 200):
    if not HAS_FASTAPI:
        return _html(tree)
    return HTMLResponse(_html(tree), status_code=status_code)


def _render_surface(app: App, surface_id: str):
    behavior = getattr(app, "_behavior", None) or getattr(app, "behavior", None)
    inst = None
    if behavior is not None and hasattr(behavior, "components"):
        try:
            inst = dict(behavior.components()).get(surface_id)
        except Exception:
            inst = None
    if inst is None:
        reg = getattr(app, "_pulse_registry", {}) or {}
        inst = reg.get(surface_id)
    if inst is None:
        return p(f"Surface {surface_id!r} not mounted.", className="text-stone-500")
    return inst.render()


def _page_for_path(path: str) -> str:
    pth = (path or "/").rstrip("/") or "/"
    if pth in ("/", "/home"):
        return "home"
    if pth.startswith("/shop"):
        return "shop"
    if pth.startswith("/lab"):
        return "lab"
    if pth.startswith("/matrix"):
        return "matrix"
    if pth.startswith("/settings"):
        return "settings"
    return "home"


def build():
    document = _document()
    wrap = _pulse_wrap(document)
    app, asgi, bundle = compose_build(
        PACKAGE,
        name="Pulse",
        host="auto",
        live="auto",
        level="auto",
        base="routes",
        fail_closed=False,
        document=document,
        wrap=wrap,
        cek="require",
    )
    app._pulse_registry = dict(bundle.unit_registry or {})
    app._pulse_bundle = bundle
    app._pulse_wrap = wrap

    if asgi is None or not hasattr(asgi, "get"):
        return app, asgi, bundle

    if STATIC.exists() and StaticFiles is not None:
        asgi.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

    @asgi.get("/")
    async def root():
        # /home is the DirectoryRoutes page; / aliases the live Home fragment.
        tree = _render_surface(app, "home")
        return _html_response(apply_html_document(wrap, tree))

    @asgi.post("/action/{name:path}")
    async def action_door(name: str, request: Request):
        args = await _parse_action_args(request)
        action_name = name
        if "." not in action_name:
            try:
                from urllib.parse import urlparse
                ref_path = urlparse(request.headers.get("referer") or "/").path
                sid = _page_for_path(ref_path)
            except Exception:
                sid = "home"
            action_name = f"{sid}.{name}"
        sealed = dict(args)
        cap = sealed.pop("cap", None)
        try:
            if action_name.endswith("checkout"):
                if not cap:
                    cap = app.mint_cap(action_name, sealed, once=True)
                await app.submit_intent_async(action_name, cap=cap, args=sealed)
                # Cap refuse must not fall through to dispatch.
            else:
                app.dispatch(action_name, **sealed)
        except Exception as exc:
            return _html_response(
                p(f"Action error: {exc}", className="text-stone-500"),
                status_code=400,
            )

        ref_path = "/"
        try:
            from urllib.parse import urlparse
            ref_path = urlparse(request.headers.get("referer") or "/").path or "/"
        except Exception:
            pass
        sid = _page_for_path(ref_path)
        if "." in action_name:
            sid = action_name.split(".", 1)[0]
        inner = _render_surface(app, sid)
        if request.headers.get("hx-request"):
            return _html_response(inner)
        return _html_response(apply_html_document(wrap, inner))

    @asgi.get("/api/doctor")
    def api_doctor():
        report = doctor([], fail=False, bundle=getattr(app, "_pulse_bundle", None))
        return {
            "ok": report.ok,
            "level": report.level_available,
            "capabilities": report.capabilities,
            "surfaces": report.surfaces,
            "routes": report.routes,
            "teaching": report.teaching,
            "diagnostics": report.diagnostics,
        }

    @asgi.get("/api/health")
    def health():
        return {
            "app": "Pulse",
            "level": int(app.level),
            "label": getattr(app.level, "label", ""),
            "surfaces": list(getattr(app, "_pulse_registry", {}).keys()),
            "fastapi": True,
            "dom": True,
        }

    return app, asgi, bundle


UX, asgi, BUNDLE = build()
app = asgi  # uvicorn apps.pulse.server:app


if __name__ == "__main__":
    print("Pulse · ux-compose showcase")
    print("  Level:", int(UX.level), getattr(UX.level, "label", ""))
    print("  Surfaces:", list(getattr(UX, "_pulse_registry", {}).keys()))
    print("  Routes:", [r.get("path") for r in (BUNDLE.route_table or [])])
    print("  Document:", True)
    print("  FastAPI:", asgi is not None)
    report = doctor([], fail=False, bundle=BUNDLE)
    print("  Doctor surfaces:", report.surfaces)
    print("  Doctor routes:", report.routes)
    if asgi is not None:
        print("  Serve: PYTHONPATH=src:. uxcompose serve apps.pulse.server:app --host 0.0.0.0 --port 8080")
    else:
        print("  Offline dispatch home.beat →", UX.dispatch("home.beat"))
