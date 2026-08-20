"""Atelier shop host — FastAPI + Document SSoT + Channel via wire/.

Isolation Law: this module never imports ux_channel or CEK.
Channel attaches only through App.use_channel(asgi_app=...).
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional
from urllib.parse import parse_qs

from ux_compose import (
    App,
    doctor,
    HAS_DOM as COMPOSE_HAS_DOM,
    html,
    head,
    body,
    title,
    style,
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
    raw,
)
from ux_compose.helpers import _serialize_tree

from apps.atelier_shop.shop import Cart, ConfirmModal, catalog_grid

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse, Response
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


CSS = """
:root {
  color-scheme: light only;
  --bg: #f3efe6;
  --bg-elevated: #faf7f1;
  --surface: #fffdf8;
  --fg: #161513;
  --fg-muted: #6b6560;
  --fg-subtle: #8a837b;
  --border: color-mix(in oklab, var(--fg) 12%, transparent);
  --border-strong: color-mix(in oklab, var(--fg) 22%, transparent);
  --accent: #2f3b38;
  --accent-fg: #f3efe6;
  --danger: #7a2e24;
  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --radius-xl: 28px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;
  --font-display: "Fraunces", "Iowan Old Style", "Palatino Linotype", serif;
  --font-body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1.0625rem;
  --text-lg: 1.25rem;
  --text-xl: clamp(1.75rem, 1.2rem + 2vw, 2.75rem);
  --text-2xl: clamp(2.4rem, 1.4rem + 4vw, 4.25rem);
  --leading-tight: 1.1;
  --leading-snug: 1.25;
  --leading-normal: 1.5;
  --tracking-display: -0.03em;
  --motion-quick: 150ms;
  --motion-fast: 250ms;
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
}
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
html {
  color-scheme: light only;
  background: #f3efe6;
  color: #161513;
}
body {
  color-scheme: light only;
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  min-height: 100dvh;
  background:
    radial-gradient(1200px 480px at 10% -10%, color-mix(in oklab, var(--fg) 4%, transparent), transparent 60%),
    #f3efe6;
  color: #161513;
}
button:not(:disabled), [role="button"]:not(:disabled) { cursor: pointer; }
button:disabled { opacity: 0.6; cursor: wait; }
a { color: inherit; }
img { max-width: 100%; }
.wrap {
  width: min(1120px, calc(100% - 32px));
  margin: 0 auto;
}
.top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5) 0 var(--space-4);
  border-bottom: 1px solid var(--border);
}
.brand {
  font-family: var(--font-display);
  font-weight: 550;
  letter-spacing: var(--tracking-display);
  font-size: 1.35rem;
  text-decoration: none;
}
.brand span { color: var(--fg-muted); font-weight: 450; margin-left: 0.4rem; font-size: 0.95rem; }
.nav-meta { color: var(--fg-subtle); font-size: var(--text-sm); letter-spacing: 0.08em; text-transform: uppercase; }
.hero {
  padding: var(--space-8) 0 var(--space-6);
  display: grid;
  gap: var(--space-4);
  max-width: 38rem;
}
.kicker {
  font-size: var(--text-xs);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--fg-subtle);
  margin: 0;
}
.hero h1 {
  font-family: var(--font-display);
  font-weight: 550;
  letter-spacing: var(--tracking-display);
  font-size: var(--text-2xl);
  line-height: var(--leading-tight);
  margin: 0;
}
.lede { margin: 0; color: var(--fg-muted); max-width: 36ch; }
.stage {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-6);
  padding-bottom: var(--space-8);
  align-items: start;
}
@media (min-width: 880px) {
  .stage { grid-template-columns: minmax(0, 1fr) 320px; }
}
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}
@media (min-width: 640px) {
  .grid { grid-template-columns: 1fr 1fr; }
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  display: grid;
  gap: var(--space-3);
  min-height: 220px;
}
.card-mark { color: var(--fg); opacity: 0.72; }
.card-head { display: flex; justify-content: space-between; gap: var(--space-3); align-items: baseline; }
.card h2 {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 550;
  margin: 0;
  letter-spacing: var(--tracking-display);
}
.price {
  font-variant-numeric: tabular-nums;
  margin: 0;
  font-weight: 550;
}
.card-line { margin: 0; color: var(--fg-muted); font-size: var(--text-sm); }
.bag {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  position: sticky;
  top: var(--space-4);
}
.bag-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: var(--space-4); }
.bag-head h2 {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  margin: 0;
  font-weight: 550;
}
.bag-count {
  font-variant-numeric: tabular-nums;
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  min-width: 1.8rem;
  height: 1.8rem;
  display: inline-grid;
  place-items: center;
  font-size: var(--text-sm);
  font-weight: 550;
}
.bag-empty-title { font-weight: 550; margin: 0 0 var(--space-2); }
.bag-empty-copy { margin: 0; color: var(--fg-muted); font-size: var(--text-sm); }
.bag-lines { list-style: none; padding: 0; margin: 0 0 var(--space-4); display: grid; gap: var(--space-3); }
.bag-line {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border);
}
.bag-line-name { font-weight: 550; }
.bag-line-meta { grid-column: 1; color: var(--fg-subtle); font-size: var(--text-sm); }
.bag-line-sum { font-variant-numeric: tabular-nums; }
.bag-line .inline { grid-column: 1 / -1; }
.bag-foot {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-4);
  font-weight: 550;
}
.bag-sum { font-variant-numeric: tabular-nums; font-size: var(--text-lg); }
.bag-notice { color: var(--accent); font-size: var(--text-sm); margin: 0 0 var(--space-3); }
.btn-primary, .btn-secondary, .btn-ghost, .text-btn {
  font: inherit;
  border-radius: var(--radius-sm);
  min-height: 44px;
  padding: 0 var(--space-4);
}
.btn-primary {
  background: var(--accent);
  color: var(--accent-fg);
  border: 1px solid var(--accent);
  width: 100%;
  font-weight: 550;
}
.btn-primary:hover { filter: brightness(1.08); }
.btn-primary:active { transform: scale(0.98); }
.btn-secondary {
  background: transparent;
  color: var(--fg);
  border: 1px solid var(--border-strong);
  width: 100%;
  font-weight: 550;
}
.btn-secondary:hover { background: color-mix(in oklab, var(--fg) 4%, transparent); }
.btn-ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--fg-muted);
  width: 100%;
}
.text-btn {
  background: none;
  border: 0;
  color: var(--fg-subtle);
  min-height: 36px;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 3px;
  font-size: var(--text-sm);
}
.foot {
  border-top: 1px solid var(--border);
  padding: var(--space-5) 0 var(--space-7);
  color: var(--fg-subtle);
  font-size: var(--text-sm);
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.modal[hidden], .modal[data-open="0"] { display: none; }
.modal[data-open="1"] {
  position: fixed; inset: 0; z-index: 40;
  display: grid; place-items: end center;
}
@media (min-width: 640px) {
  .modal[data-open="1"] { place-items: center; }
}
.modal-scrim { position: absolute; inset: 0; background: color-mix(in oklab, var(--fg) 38%, transparent); }
.modal-panel {
  position: relative;
  background: var(--surface);
  color: var(--fg);
  width: min(420px, 100%);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: var(--space-6);
  display: grid;
  gap: var(--space-3);
}
@media (min-width: 640px) {
  .modal-panel { border-radius: var(--radius-xl); }
}
.modal-panel h2 {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  margin: 0;
  letter-spacing: var(--tracking-display);
  line-height: var(--leading-snug);
}
.modal-copy { margin: 0; color: var(--fg-muted); }
.modal-actions { display: grid; gap: var(--space-2); margin-top: var(--space-3); }
.level-chip {
  font-size: var(--text-xs);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px 10px;
}
form.inline { margin: 0; }
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
"""

ENHANCE_JS = """
(() => {
  const swap = (html) => {
    const wrap = document.createElement('div');
    wrap.innerHTML = html.trim();
    const nextStage = wrap.querySelector('#stage');
    const nextModal = wrap.querySelector('#confirm-modal');
    const curStage = document.querySelector('#stage');
    const curModal = document.querySelector('#confirm-modal');
    if (nextStage && curStage) curStage.replaceWith(nextStage);
    if (nextModal && curModal) curModal.replaceWith(nextModal);
  };

  async function submit(form) {
    const btn = form.querySelector('[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      const body = new URLSearchParams(new FormData(form));
      const res = await fetch(form.action, {
        method: 'POST',
        body: body.toString(),
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'HX-Request': 'true',
          'Accept': 'text/html',
        },
      });
      if (!res.ok) throw new Error('act failed');
      swap(await res.text());
    } catch (err) {
      form.removeAttribute('data-ux');
      HTMLFormElement.prototype.submit.call(form);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  document.addEventListener('submit', (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.getAttribute('data-ux') !== '1') return;
    e.preventDefault();
    submit(form);
  });
})();
"""


def _document():
    if not HAS_DOM:
        return None
    return Document(head=[], body=[], ensure_csrf_token=False).use(
        XElement(),
        Htmx(),
    )


DOCUMENT = _document()
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
                style(raw(CSS) if raw is not None else CSS),
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
                script(raw(ENHANCE_JS) if raw is not None else ENHANCE_JS),
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
        "<title>Atelier — Linen & Object</title><style>"
        + CSS
        + "</style></head><body>"
        + flash_html
        + f'<div id="stage" class="stage">{_html(catalog_grid())}{cart_html}</div>'
        + modal_html
        + f"<script>{ENHANCE_JS}</script></body></html>"
    )


def _wants_fragment(request: Optional[Any]) -> bool:
    if request is None:
        return False
    hx = request.headers.get("hx-request") or request.headers.get("HX-Request")
    return str(hx).lower() in {"1", "true", "yes"}


def _fragment_or_page(request, *, flash: str = "") -> bool:
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
            "routes": [p for p in paths if p],
        }

    @asgi.get("/favicon.svg")
    def favicon():
        svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="20" fill="#161513"/>
<text x="50" y="58" font-size="56" text-anchor="middle"
  font-family="Georgia, serif" fill="#f3efe6">A</text>
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
