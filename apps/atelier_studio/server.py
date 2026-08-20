"""Atelier of Patterns host.

Isolation Law: never imports ux_channel or CEK.
Channel attaches only through App.use_channel(asgi_app=...).
One Document owns the HTML shell.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

from ux_compose import (
    App,
    HAS_DOM as COMPOSE_HAS_DOM,
    body,
    doctor,
    head,
    html,
    link,
    meta,
    raw,
    script,
    style,
    title,
    div,
)
from ux_compose.helpers import _serialize_tree

from apps.atelier_studio.chrome import (
    CSS,
    ENHANCE_JS,
    catalog_page,
    foot,
    html_of,
    nav,
    pattern_page,
    toast_host,
)
from examples.catalog import PATTERNS, all_components, by_slug
from apps.atelier_shop.shop import Cart, ConfirmModal, catalog_grid

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
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
_STATIC = Path(__file__).resolve().parent / "static"
_IDIOMORPH = _STATIC / "idiomorph.min.js"

# Live Cap: these names go through submit_intent, not Host-internal dispatch.
MINT = {"liveorder.place_minted", "cart.checkout", "checkout.place"}
REFUSE = {
    "liveorder.place",
    "confirm.confirm",
    "demomodal.confirm",
    "signup.create_account",
    "wizard.place",
    "table.bulk_archive",
    "counter.reset",
    "otpgate.verify",
    "coupon.redeem",
    "comments.moderate",
    "calendar.book",
    "settings.wipe",
}
# Host routing keys — never forwarded into @action kwargs.
HOST_KEYS = {"action", "submit", "slug", "target"}


def _clean_args(args: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for k, v in (args or {}).items():
        if not isinstance(k, str) or not _IDENT.match(k):
            continue
        if k in HOST_KEYS:
            continue
        if isinstance(v, (list, tuple)):
            v = v[0] if v else ""
        clean[k] = v
    return clean


def _slug_for_action(name: str) -> Optional[str]:
    """Map ``component.verb`` to a catalog slug without relying on Referer."""
    cid = (name or "").split(".", 1)[0]
    if cid in {"cart", "confirm-modal"}:
        return "shop"
    for row in PATTERNS:
        if getattr(row["component"], "id", "") == cid:
            return row["slug"]
        for cls in row.get("companions") or ():
            if getattr(cls, "id", "") == cid:
                return row["slug"]
    return None


def _parse_multipart(ctype: str, raw: bytes) -> dict[str, Any]:
    m = re.search(r"boundary=([^;]+)", ctype or "", re.I)
    if not m:
        return {}
    boundary = m.group(1).strip().strip('"')
    if not boundary:
        return {}
    sep = b"--" + boundary.encode("ascii", "replace")
    out: dict[str, Any] = {}
    for part in raw.split(sep):
        part = part.lstrip(b"\r\n")
        if not part or part == b"--" or part.startswith(b"--"):
            continue
        header, sep2, body_p = part.partition(b"\r\n\r\n")
        if not sep2:
            header, sep2, body_p = part.partition(b"\n\n")
        if not sep2:
            continue
        hm = re.search(br'name="([^"]+)"', header)
        if not hm:
            continue
        name = hm.group(1).decode("utf-8", "replace")
        if body_p.endswith(b"--"):
            body_p = body_p[:-2]
        body_p = body_p.rstrip(b"\r\n")
        out[name] = body_p.decode("utf-8", "replace")
    return out


def _sniff_multipart(raw: bytes) -> dict[str, Any]:
    if not raw.startswith(b"--"):
        return {}
    first = raw.split(b"\r\n", 1)[0].split(b"\n", 1)[0]
    if first.endswith(b"--") or len(first) < 4:
        return {}
    boundary = first[2:].decode("ascii", "replace")
    return _parse_multipart(f"multipart/form-data; boundary={boundary}", raw)


def _parse_action_args(ctype: str, raw: bytes) -> dict[str, Any]:
    original = ctype or ""
    kind = original.lower()
    raw = raw or b""
    args: dict[str, Any] = {}
    if "application/json" in kind:
        try:
            body_j = json.loads(raw.decode("utf-8") or "{}")
            if isinstance(body_j, dict):
                args = dict(body_j)
        except Exception:
            args = {}
    elif "multipart/form-data" in kind:
        args = _parse_multipart(original, raw)
    else:
        parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
        args = {k: (v[0] if v else "") for k, v in parsed.items()}
        if args and not any(_IDENT.match(k) for k in args):
            args = _sniff_multipart(raw) or args
    return _clean_args(args)


def _document():
    if not HAS_DOM:
        return None
    return Document(head=[], body=[], ensure_csrf_token=False).use(
        XElement(),
        Htmx(),
    )


DOCUMENT = _document()
UX = App.boot("AtelierStudio", strict_caps=True)
if DOCUMENT is not None:
    UX.use_dom(DOCUMENT)
UX.use_behavior()
UX.add(*all_components())


def _inst(cid: str):
    b = UX.behavior
    get = getattr(b, "get", None)
    if callable(get):
        try:
            return get(cid)
        except Exception:
            pass
    return None


def _shell(*main_kids: Any, flash: str = "") -> str:
    flash_nodes = []
    if flash:
        from ux_compose import p as p_tag

        flash_nodes = [p_tag(flash, className="status status-ok", role="status")]
    if COMPOSE_HAS_DOM and html is not None:
        tree = html(
            head(
                meta(charset="utf-8"),
                meta(name="viewport", content="width=device-width, initial-scale=1"),
                meta(name="color-scheme", content="light only"),
                title("Atelier of Patterns"),
                meta(name="theme-color", content="#f3efe6"),
                link(rel="icon", type="image/svg+xml", href="/favicon.svg"),
                link(rel="preconnect", href="https://fonts.googleapis.com"),
                link(
                    rel="preconnect",
                    href="https://fonts.gstatic.com",
                    crossorigin="anonymous",
                ),
                link(
                    rel="stylesheet",
                    href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Sans+3:wght@400;500;600&display=swap",
                ),
                style(raw(CSS) if raw is not None else CSS),
                script(src="/static/idiomorph.min.js"),
                script(src="/ux-pkg/ux-motion/static/ux-motion-player.js"),
            ),
            body(
                nav(level=int(UX.level), label=UX.level.label),
                *flash_nodes,
                *main_kids,
                foot(),
                toast_host(),
                script(raw(ENHANCE_JS) if raw is not None else ENHANCE_JS),
            ),
            lang="en",
            style="color-scheme: light only",
        )
        return "<!doctype html>\n" + html_of(tree)
    return "<!doctype html><html lang='en'><body>ux-dom required</body></html>"


def _index(*, flash: str = "") -> str:
    inner = catalog_page()
    return _shell(div(*inner, className="wrap"), flash=flash)


def _pattern_widget(slug: str):
    row = by_slug(slug)
    if row is None:
        return None, None
    inst = _inst(getattr(row["component"], "id", ""))
    extras = []
    for cls in row.get("companions") or ():
        extra = _inst(getattr(cls, "id", ""))
        if extra is not None:
            extras.append(extra.render())
    widget = inst.render() if inst is not None else div("missing", id="stage")
    if extras:
        widget = div(widget, *extras, id=getattr(row["component"], "id", "x"))
    return row, widget


def _pattern(slug: str, *, flash: str = "") -> str:
    row, widget = _pattern_widget(slug)
    if row is None or widget is None:
        return _index(flash="Unknown pattern")
    parts = pattern_page(row, widget)
    return _shell(div(*parts, className="wrap"), flash=flash)


def _shop(*, flash: str = "") -> str:
    from ux_compose import aside, h1, p, section, span as sp, main as main_tag, header as hdr

    cart = _inst("cart")
    modal = _inst("confirm-modal")
    cart_tree = cart.render() if cart is not None else aside(id="cart")
    modal_tree = modal.render() if modal is not None else div(id="confirm-modal", hidden=True)
    flash_nodes = [p(flash, className="status status-ok", role="status")] if flash else []
    stage = div(catalog_grid(), cart_tree, id="stage", className="layout")
    inner = (
        section(
            p("Product app", className="kicker"),
            h1("Quiet pieces for a working house."),
            p(
                "The same Cart class as examples/cart.py, live-safe: lines in RefState, "
                "stamp as MorphState, checkout under a Cap.",
                className="lede",
            ),
            className="hero",
        ),
        *flash_nodes,
        stage,
    )
    return _shell(div(*inner, className="wrap"), modal_tree, flash="")


def _wants_fragment(request: Optional[Any]) -> bool:
    if request is None:
        return False
    hx = request.headers.get("hx-request") or request.headers.get("HX-Request")
    return str(hx).lower() in {"1", "true", "yes"}


def _wants_ops(request: Optional[Any]) -> bool:
    if request is None:
        return False
    if str(request.headers.get("x-ux-ops") or "").lower() in {"1", "true", "yes"}:
        return True
    accept = (request.headers.get("accept") or "").lower()
    return "application/json" in accept and "text/html" not in accept


def _collect_ops(bucket: list, result: Any) -> None:
    if result is None:
        return
    if isinstance(result, (list, tuple)):
        bucket.extend(result)
        return
    extra = getattr(result, "ops", None)
    if extra:
        bucket.extend(extra)


def _fragment(slug: Optional[str], *, flash: str = "") -> str:
    """Stage-only HTML for JSON fallback / HTMX. Never the full document."""
    if slug == "shop":
        cart = _inst("cart")
        modal = _inst("confirm-modal")
        stage = div(
            catalog_grid(),
            cart.render() if cart is not None else "",
            id="stage",
            className="layout",
        )
        return html_of(stage) + html_of(modal.render() if modal is not None else "")
    if slug:
        row, widget = _pattern_widget(slug)
        if widget is None:
            return ""
        return html_of(div(widget, id="stage", className="stage"))
    return ""


def build_asgi():
    if not HAS_FASTAPI:
        return None
    asgi = FastAPI(title="Atelier of Patterns")
    UX.use_channel(asgi_app=asgi)
    UX.use_motion()
    try:
        UX.use_cek(mode="adapt")
    except Exception:
        pass
    if DOCUMENT is not None and hasattr(DOCUMENT, "mount"):
        try:
            DOCUMENT.mount(asgi)
        except Exception:
            pass

    @asgi.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(_index())

    @asgi.get("/p/{slug}", response_class=HTMLResponse)
    def pattern(slug: str):
        row = by_slug(slug)
        if row is None:
            return HTMLResponse(_index(flash="Unknown pattern"), status_code=404)
        return HTMLResponse(_pattern(slug))

    @asgi.get("/shop", response_class=HTMLResponse)
    def shop():
        return HTMLResponse(_shop())

    @asgi.get("/health")
    def health():
        return {
            "ok": True,
            "app": "AtelierStudio",
            "level": int(UX.level),
            "label": UX.level.label,
            "patterns": len(PATTERNS),
            "document": DOCUMENT is not None,
            "channel": UX._channel is not None,
            "motion": bool(UX._motion),
            "player": "/ux-pkg/ux-motion/static/ux-motion-player.js",
            "idiomorph": _IDIOMORPH.is_file(),
        }

    @asgi.get("/favicon.svg")
    def favicon():
        svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="20" fill="#161513"/>
<text x="50" y="58" font-size="56" text-anchor="middle"
  font-family="Georgia, serif" fill="#f3efe6">A</text>
</svg>"""
        return Response(content=svg, media_type="image/svg+xml")

    @asgi.get("/static/idiomorph.min.js")
    def idiomorph_js():
        if not _IDIOMORPH.is_file():
            return Response(status_code=404)
        return FileResponse(_IDIOMORPH, media_type="application/javascript")

    @asgi.post("/act/{action}")
    async def act(action: str, request: Request):
        raw_b = await request.body()
        ctype = request.headers.get("content-type") or ""
        args = _parse_action_args(ctype, raw_b)
        referer = request.headers.get("referer") or ""
        slug = None
        if "/shop" in referer:
            slug = "shop"
        else:
            m = re.search(r"/p/([A-Za-z0-9_-]+)", referer)
            if m:
                slug = m.group(1)
        if not slug:
            slug = _slug_for_action(action)
        flash = ""
        name = action
        last_ops: list[Any] = []
        try:
            if name == "cart.open_checkout":
                _collect_ops(last_ops, UX.dispatch("cart.open_checkout"))
                cart = _inst("cart")
                total = cart.subtotal() if cart is not None else 0
                n = sum(q for _, q in cart._rows()) if cart is not None else 0
                _collect_ops(
                    last_ops,
                    UX.dispatch(
                        "confirm-modal.open_modal",
                        title="Place this order",
                        body=f"{n} piece(s) · {total}. The host will mint a Cap for checkout.",
                    ),
                )
                slug = "shop"
            elif name in MINT:
                intent_name = "liveorder.place" if name == "liveorder.place_minted" else name
                result = await UX.submit_intent_async(intent_name, mint=True, args=args)
                _collect_ops(last_ops, result)
                ok = bool(getattr(result, "ok", False))
                if not ok:
                    flash = "Refused — no Cap."
                    if intent_name == "liveorder.place":
                        _collect_ops(last_ops, UX.dispatch("liveorder.mark_refused", reason="no Cap"))
                else:
                    if name == "cart.checkout":
                        _collect_ops(last_ops, UX.dispatch("confirm-modal.close"))
                        flash = "Order placed."
                        slug = "shop"
            elif name in REFUSE:
                result = await UX.submit_intent_async(name, mint=False, args=args)
                _collect_ops(last_ops, result)
                ok = bool(getattr(result, "ok", False))
                flash = "Placed." if ok else "Refused — no Cap."
                if not ok and name == "liveorder.place":
                    _collect_ops(last_ops, UX.dispatch("liveorder.mark_refused", reason="no Cap"))
            else:
                _collect_ops(last_ops, UX.dispatch(name, **args))
        except Exception as exc:
            flash = str(exc)
        if _wants_ops(request):
            from ux_compose.wire.caps import ops_to_wire

            return JSONResponse(
                {
                    "ok": True,
                    "ops": ops_to_wire(last_ops),
                    "flash": flash,
                    "slug": slug,
                    "html": _fragment(slug, flash=flash),
                }
            )
        if _wants_fragment(request):
            return HTMLResponse(_fragment(slug, flash=flash))
        if slug == "shop":
            return HTMLResponse(_shop(flash=flash))
        if slug:
            return HTMLResponse(_pattern(slug, flash=flash))
        return HTMLResponse(_index(flash=flash))

    @asgi.get("/doctor")
    def doctor_endpoint():
        report = doctor([], fail=False)
        return {
            "ok": report.ok,
            "level": report.level_available,
            "capabilities": report.capabilities,
            "diagnostics": report.diagnostics,
        }

    return asgi


asgi = build_asgi()
app = asgi
