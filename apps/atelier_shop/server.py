"""Atelier shop host — FastAPI + Document SSoT + Channel via wire/.

Isolation Law: this module never imports ux_channel or CEK.
Channel attaches only through App.use_channel(asgi_app=...).
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional
from urllib.parse import parse_qs

from pathlib import Path

from ux_compose import (
    App,
    doctor,
    HAS_DOM as COMPOSE_HAS_DOM,
    html,
    head,
    body,
    title,
    meta,
    link,
    script,
    header,
    main,
    footer,
    section,
    a,
    h1,
    p,
    span,
    div,
    aside,
)
from ux_compose.helpers import _serialize_tree

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


def _clean_args(args: dict[str, Any]) -> dict[str, Any]:
    """Drop multipart garbage keys so Behavior dispatch cannot see them."""
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
    if not boundary:
        return {}
    sep = b"--" + boundary.encode("ascii", "replace")
    out: dict[str, Any] = {}
    for part in raw.split(sep):
        part = part.lstrip(b"\r\n")
        if not part or part == b"--" or part.startswith(b"--"):
            continue
        header, sep2, body = part.partition(b"\r\n\r\n")
        if not sep2:
            header, sep2, body = part.partition(b"\n\n")
        if not sep2:
            continue
        hm = re.search(br'name="([^"]+)"', header)
        if not hm:
            continue
        name = hm.group(1).decode("utf-8", "replace")
        if body.endswith(b"--"):
            body = body[:-2]
        body = body.rstrip(b"\r\n")
        out[name] = body.decode("utf-8", "replace")
    return out


def _parse_action_args(ctype: str, raw: bytes) -> dict[str, Any]:
    """Parse JSON, multipart, or urlencoded bodies. Browsers send FormData as multipart."""
    original = ctype or ""
    kind = original.lower()
    raw = raw or b""
    args: dict[str, Any] = {}
    if "application/json" in kind:
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
            if isinstance(body, dict):
                args = dict(body)
        except Exception:
            args = {}
    elif "multipart/form-data" in kind:
        args = _parse_multipart(original, raw)
    else:
        parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
        args = {k: (v[0] if v else "") for k, v in parsed.items()}
        # urlencoded parse on a multipart body yields one illegal key — sniff.
        if args and not any(_IDENT.match(k) for k in args):
            args = _sniff_multipart(raw) or args
    return _clean_args(args)


def _sniff_multipart(raw: bytes) -> dict[str, Any]:
    if not raw.startswith(b"--"):
        return {}
    first = raw.split(b"\r\n", 1)[0].split(b"\n", 1)[0]
    if first.endswith(b"--") or len(first) < 4:
        return {}
    boundary = first[2:].decode("ascii", "replace")
    return _parse_multipart(f"multipart/form-data; boundary={boundary}", raw)



def _document():
    if not HAS_DOM:
        return None
    return Document(head=[], body=[], ensure_csrf_token=False).use(
        XElement(),
        Htmx(),
    )


DOCUMENT = _document()


_STATIC = Path(__file__).resolve().parent / "static"
_IDIOMORPH = _STATIC / "idiomorph.min.js"
UX = App.boot("Atelier", strict_caps=True)
if DOCUMENT is not None:
    UX.use_dom(DOCUMENT)
UX.use_behavior()
UX.add(Cart, ConfirmModal)


def _inst(cid: str):
    b = UX.behavior
    get = getattr(b, "get", None)
    if callable(get):
        try:
            return get(cid)
        except Exception:
            pass
    return None


def _html(tree: Any) -> str:
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    return _serialize_tree(tree)


def _page(*, flash: str = "") -> str:
    cart = _inst("cart")
    modal = _inst("confirm-modal")
    level = int(UX.level)
    label = UX.level.label
    cart_tree = cart.render() if cart is not None else aside(id="cart", className="bag")
    modal_tree = (
        modal.render() if modal is not None else div(id="confirm-modal", hidden=True)
    )
    flash_nodes = [p(flash, className="bag-notice", role="status")] if flash else []
    if COMPOSE_HAS_DOM and html is not None:
        tree = html(
            head(
                meta(charset="utf-8"),
                meta(name="viewport", content="width=device-width, initial-scale=1"),
                meta(name="color-scheme", content="light only"),
                title("Atelier — Linen & Object"),
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
                link(rel="stylesheet", href="/static/css/atelier.css"),
                script(src="/static/idiomorph.min.js"),
                script(src="/ux-pkg/ux-motion/static/ux-motion-player.js"),
            ),
            body(
                header(
                    a("Atelier", span("Linen & Object"), href="/", className="brand"),
                    div(
                        "Studio table · ",
                        span(f"L{level} {label}", className="level-chip"),
                        className="nav-meta",
                    ),
                    className="top wrap",
                ),
                main(
                    section(
                        p("Table of the week", className="kicker"),
                        h1("Quiet pieces for a working house."),
                        p(
                            "Four objects. Linen, oak, wool, clay. The bag lives on this page; placing an order is a capability, not a click.",
                            className="lede",
                        ),
                        className="hero",
                    ),
                    *flash_nodes,
                    div(
                        catalog_grid(),
                        cart_tree,
                        id="stage",
                        className="stage",
                    ),
                    className="wrap",
                ),
                footer(
                    span("Atelier · capability-secured checkout"),
                    span("No account. Host mints the Cap."),
                    className="foot wrap",
                ),
                modal_tree,
            ),
            lang="en",
            style="color-scheme: light only",
        )
        return "<!doctype html>\n" + _html(tree)
    cart_html = _html(cart_tree)
    modal_html = _html(modal_tree)
    flash_html = f'<p class="bag-notice" role="status">{flash}</p>' if flash else ""
    return (
        "<!doctype html><html lang='en' style='color-scheme:light only'><head><meta charset='utf-8'/>"
        "<meta name='color-scheme' content='light only'/>"
        "<title>Atelier — Linen & Object</title>"
        '<link rel="stylesheet" href="/static/css/atelier.css"/>'
        "</head><body>"
        + flash_html
        + f'<div id="stage" class="stage">{_html(catalog_grid())}{cart_html}</div>'
        + modal_html
        + "</body></html>"
    )


def _wants_fragment(request: Optional[Any]) -> bool:
    if request is None:
        return False
    hx = request.headers.get("hx-request") or request.headers.get("HX-Request")
    return str(hx).lower() in {"1", "true", "yes"}


def _fragment_or_page(request, *, flash: str = "") -> str:
    if _wants_fragment(request):
        cart = _inst("cart")
        modal = _inst("confirm-modal")
        if COMPOSE_HAS_DOM and div is not None:
            stage = div(
                catalog_grid(),
                cart.render() if cart is not None else "",
                id="stage",
                className="stage",
            )
            return _html(stage) + _html(modal.render() if modal is not None else "")
        cart_html = _html(cart.render()) if cart is not None else ""
        modal_html = _html(modal.render()) if modal is not None else ""
        return (
            f'<div id="stage" class="stage">{_html(catalog_grid())}{cart_html}</div>'
            f"{modal_html}"
        )
    return _page(flash=flash)


def build_asgi():
    if not HAS_FASTAPI:
        return None
    asgi = FastAPI(title="Atelier")
    # Channel via wire door — Isolation held. Behavior.attach owns Channel.boot.
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
        return HTMLResponse(_page())

    @asgi.get("/health")
    def health():
        paths = [getattr(r, "path", "") for r in asgi.routes]
        return {
            "ok": True,
            "app": "Atelier",
            "level": int(UX.level),
            "label": UX.level.label,
            "document": DOCUMENT is not None,
            "channel": UX._channel is not None,
            "motion": bool(getattr(UX, "_motion", False)),
            "player": "/ux-pkg/ux-motion/static/ux-motion-player.js",
            "idiomorph": _IDIOMORPH.is_file(),
            "css": (_STATIC / "css" / "atelier.css").is_file(),
            "routes": [p for p in paths if p],
        }

    @asgi.get("/favicon.svg")
    def favicon():
        svg = """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\">
<rect width=\"100\" height=\"100\" rx=\"20\" fill=\"#161513\"/>
<text x=\"50\" y=\"58\" font-size=\"56\" text-anchor=\"middle\"
  font-family=\"Georgia, serif\" fill=\"#f3efe6\">A</text>
</svg>"""
        return Response(content=svg, media_type="image/svg+xml")

    @asgi.get("/og.jpg")
    def og_card():
        from pathlib import Path
        for p in (
            Path("/workspace/public/og.jpg"),
            Path(__file__).resolve().parents[3] / "public" / "og.jpg",
        ):
            if p.is_file():
                return Response(p.read_bytes(), media_type="image/jpeg")
        return Response(status_code=404)


    @asgi.get("/static/idiomorph.min.js")
    def idiomorph_js():
        if not _IDIOMORPH.is_file():
            return Response(status_code=404)
        return FileResponse(_IDIOMORPH, media_type="application/javascript")

    @asgi.get("/static/css/atelier.css")
    def atelier_css():
        css = _STATIC / "css" / "atelier.css"
        if not css.is_file():
            return Response(status_code=404)
        return FileResponse(css, media_type="text/css")

    @asgi.post("/act/{action}")
    async def act(action: str, request: Request):
        raw = await request.body()
        ctype = request.headers.get("content-type") or ""
        args = _parse_action_args(ctype, raw)
        name = action
        flash = ""
        try:
            if name == "cart.open_checkout":
                UX.dispatch("cart.open_checkout")
                cart = _inst("cart")
                total = cart.subtotal() if cart is not None else 0
                n = sum(q for _, q in cart._rows()) if cart is not None else 0
                UX.dispatch(
                    "confirm-modal.open_modal",
                    title="Place this order",
                    body=f"{n} piece(s) · {total}. The host will mint a Cap for checkout.",
                )
            elif name == "cart.checkout":
                # Live Cap path: Host mints a real Cap, then submits Intent.
                result = await UX.submit_intent_async("cart.checkout", mint=True, args={})
                ok = bool(getattr(result, "ok", False))
                if not ok:
                    flash = "Checkout refused — no Cap."
                else:
                    UX.dispatch("confirm-modal.close")
                    flash = "Order placed."
            elif name == "confirm-modal.close":
                UX.dispatch("confirm-modal.close")
            else:
                UX.dispatch(name, **args)
        except Exception as exc:
            flash = str(exc)
        html = _fragment_or_page(request, flash=flash)
        return HTMLResponse(html)

    @asgi.post("/intent/{action}")
    async def intent_api(action: str, request: Request):
        """JSON Intent door for tests: body {args, cap?, mint?}."""
        try:
            body = await request.json()
        except Exception:
            body = {}
        args = dict(body.get("args") or {})
        cap = body.get("cap")
        mint = bool(body.get("mint", False))
        result = await UX.submit_intent_async(action, cap=cap, mint=mint, args=args)
        payload = {
            "ok": bool(getattr(result, "ok", False)),
            "ops": list(getattr(result, "ops", None) or []),
            "error": None,
        }
        err = getattr(result, "error", None)
        if err is not None:
            payload["error"] = getattr(err, "code", None) or str(err)
        status = 200 if payload["ok"] else 401
        return JSONResponse(payload, status_code=status)

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
app = asgi  # uvicorn apps.atelier_shop.server:app


if __name__ == "__main__":
    print("Level:", int(UX.level), UX.level.label)
    print("Document SSoT:", DOCUMENT is not None)
    print("FastAPI:", asgi is not None)
    if asgi is not None:
        print("Routes:", [getattr(r, "path", None) for r in asgi.routes])
        print("Serve: uvicorn apps.atelier_shop.server:app --host 0.0.0.0 --port 8080")
