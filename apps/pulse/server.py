"""Pulse host — live showcase of the locked ux-compose product path.

- Page units under routes/ via App.mount + DirectoryRouter (RouterHooks)
- Document SSoT when ux-dom present (XElement default; HTMX opt-in)
- Progressive Behavior → Channel → Motion (level=auto)
- Isolation Law: never imports ux_channel directly
- Style: Tailwind utility className (CDN stand-in for TailwindStyle/WebAssets)

Serve:
  PYTHONPATH=src:. uvicorn apps.pulse.server:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

from ux_compose import (
    App,
    doctor,
    html,
    head,
    body,
    title,
    meta,
    link,
    script,
    HAS_DOM as COMPOSE_HAS_DOM,
)
from ux_compose.helpers import _serialize_tree

PACKAGE = Path(__file__).resolve().parent
STATIC = PACKAGE / "static"

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    HAS_FASTAPI = False
    FastAPI = None  # type: ignore

try:
    from ux_dom import Document
    from ux_dom.runtime import XElement, Htmx
    HAS_DOM = True
except ImportError:
    HAS_DOM = False
    Document = None  # type: ignore


_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

NAV = (
    ("/", "Home"),
    ("/shop", "Shop"),
    ("/lab", "Lab"),
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
        header, sep2, body_b = part.partition(b"\r\n\r\n")
        if not sep2:
            header, sep2, body_b = part.partition(b"\n\n")
        if not sep2:
            continue
        hm = re.search(br'name="([^"]+)"', header)
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


def _document(*, use_htmx: bool = False):
    if not HAS_DOM or Document is None:
        return None
    runtimes = [XElement()]
    if use_htmx:
        runtimes.append(Htmx())
    return Document(head=[], body=[], ensure_csrf_token=False).use(*runtimes)


def _shell(main_html: str, *, path: str = "/") -> str:
    nav = []
    for href, label in NAV:
        cur = ' aria-current="page"' if path.rstrip("/") == href.rstrip("/") or (
            href != "/" and path.startswith(href)
        ) else ""
        if href == "/" and path in ("/", "/home"):
            cur = ' aria-current="page"'
        nav.append(f'<a href="{href}"{cur}>{label}</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pulse · ux-compose</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Sans+3:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <!-- Style: Tailwind utilities (stand-in for TailwindStyle/WebAssets) -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Control: stack-native data-ux-action. HTMX is opt-in via Document.use(Htmx()). -->
</head>
<body class="bg-stone-50 text-stone-900 antialiased dark:bg-stone-950 dark:text-stone-100">
  <div class="mx-auto max-w-5xl">
    <header class="sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-stone-200/80 bg-stone-50/90 px-4 py-4 backdrop-blur dark:border-stone-800 dark:bg-stone-950/90">
      <a class="font-serif text-lg tracking-tight" href="/">Pulse <span class="text-amber-700 dark:text-amber-400">compose</span></a>
      <nav class="flex flex-wrap gap-1">{''.join(nav)}</nav>
    </header>
    <main id="main">{main_html}</main>
    <footer class="border-t border-stone-200 px-4 py-6 text-sm text-stone-500 dark:border-stone-800">
      ux-compose · page units · RouterHooks · progressive L0–L3 · Isolation Law · HTMX opt-in
    </footer>
  </div>
</body>
</html>"""


def _render_surface(app: App, surface_id: str) -> str:
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
        return f'<p class="text-stone-500">Surface {surface_id!r} not mounted.</p>'
    tree = inst.render()
    if hasattr(tree, "__iter__") and not isinstance(tree, (str, bytes)):
        try:
            return _serialize_tree(tree)
        except Exception:
            return str(tree)
    return str(tree)


def _page_for_path(path: str) -> str:
    p = (path or "/").rstrip("/") or "/"
    if p in ("/", "/home"):
        return "home"
    if p.startswith("/shop"):
        return "shop"
    if p.startswith("/lab"):
        return "lab"
    if p.startswith("/settings"):
        return "settings"
    return "home"


def build():
    document = _document(use_htmx=False)
    asgi = FastAPI(title="Pulse") if HAS_FASTAPI else None

    app = App.boot("Pulse", level="auto")
    if document is not None:
        app.use_dom(document)
    try:
        app.use_channel(asgi_app=asgi) if asgi is not None else app.use_channel()
    except Exception:
        pass
    try:
        app.use_motion()
    except Exception:
        pass

    bundle = app.mount(
        PACKAGE,
        asgi_app=asgi,
        base="routes",
        fail_closed=False,
        include_directory_router=bool(asgi is not None),
    )
    app._pulse_registry = dict(bundle.unit_registry or {})
    app._pulse_bundle = bundle

    if asgi is None:
        return app, None, bundle

    if STATIC.exists():
        asgi.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

    @asgi.get("/")
    @asgi.get("/home")
    @asgi.get("/shop")
    @asgi.get("/lab")
    @asgi.get("/settings")
    async def pages(request: Request):
        path = request.url.path
        sid = _page_for_path(path)
        inner = _render_surface(app, sid)
        return HTMLResponse(_shell(inner, path=path))

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
        try:
            if action_name.endswith("checkout") and hasattr(app, "submit_intent_async"):
                result = await app.submit_intent_async(action_name, mint=True, args=args)
                if not getattr(result, "ok", True):
                    app.dispatch(action_name, **args)
            else:
                app.dispatch(action_name, **args)
        except Exception as exc:
            return HTMLResponse(f'<p class="text-stone-500">Action error: {exc}</p>', status_code=400)

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
            return HTMLResponse(inner)
        return HTMLResponse(_shell(inner, path=ref_path))

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
            "dom": HAS_DOM,
        }

    return app, asgi, bundle


UX, asgi, BUNDLE = build()
app = asgi  # uvicorn apps.pulse.server:app


if __name__ == "__main__":
    print("Pulse · ux-compose showcase")
    print("  Level:", int(UX.level), getattr(UX.level, "label", ""))
    print("  Surfaces:", list(getattr(UX, "_pulse_registry", {}).keys()))
    print("  Routes:", [r.get("path") for r in (BUNDLE.route_table or [])])
    print("  Document:", HAS_DOM)
    print("  FastAPI:", asgi is not None)
    report = doctor([], fail=False, bundle=BUNDLE)
    print("  Doctor surfaces:", report.surfaces)
    print("  Doctor routes:", report.routes)
    if asgi is not None:
        print("  Serve: PYTHONPATH=src:. uvicorn apps.pulse.server:app --host 0.0.0.0 --port 8080")
    else:
        print("  Offline dispatch home.beat →", UX.dispatch("home.beat"))
