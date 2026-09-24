"""Uvicorn target — Pulseboard live desk + action door.

Serve:
  PYTHONPATH=src:. uxcompose serve apps.pulseboard.server:app --host 0.0.0.0 --port 8080
  make pulseboard
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from ux_compose import doctor, p
from ux_compose.helpers import _serialize_tree
from ux_compose.routing.core import apply_html_document

from apps.pulseboard.app import BUNDLE, UX, asgi as _asgi
from apps.pulseboard.surround import compose, document_wrap
from apps.pulseboard.document import document
from apps.pulseboard.registry import live

try:
    from fastapi import Request
    from fastapi.responses import HTMLResponse, JSONResponse
    HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    HAS_FASTAPI = False
    Request = None  # type: ignore
    HTMLResponse = None  # type: ignore
    JSONResponse = None  # type: ignore

app = _asgi
WRAP = document_wrap(document)

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MINT = {"desk_close.close_quarter"}
REFUSE = {"desk_close.wipe"}


def _clean_args(args: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for k, v in (args or {}).items():
        if not isinstance(k, str) or not _IDENT.match(k):
            continue
        if k in {"action", "submit", "slug", "target"}:
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


def _room_for_path(path: str) -> str:
    pth = (path or "/").rstrip("/") or "/"
    if pth.startswith("/pipeline"):
        return "pipeline"
    if pth.startswith("/signals"):
        return "signals"
    return "overview"


def _render_unit(sid: str):
    inst = live(sid)
    if inst is None:
        return p(f"Surface {sid!r} not mounted.", className="text-slate-500")
    try:
        return inst.render(shell=False)
    except TypeError:
        return inst.render()


def attach_doors(asgi, ux=UX):
    if asgi is None or not hasattr(asgi, "get"):
        return asgi

    @asgi.get("/api/health")
    def health():
        return {
            "app": "Pulseboard",
            "ok": True,
            "level": int(ux.level),
            "label": getattr(ux.level, "label", ""),
            "surfaces": sorted((BUNDLE.unit_registry or {}).keys()),
            "board": sorted(
                k for k in (BUNDLE.unit_registry or {}) if str(k).startswith("desk_")
            ),
        }

    @asgi.get("/api/doctor")
    def api_doctor():
        report = doctor([], fail=False, bundle=BUNDLE, app=ux)
        return {
            "ok": report.ok,
            "level": report.level_available,
            "capabilities": report.capabilities,
            "surfaces": report.surfaces,
            "routes": report.routes,
            "diagnostics": report.diagnostics,
        }

    async def _run_action(name: str, request: Request):
        args = await _parse_action_args(request)
        action_name = name
        if "." not in action_name:
            action_name = f"index.{name}"
        sealed = dict(args)
        cap = sealed.pop("cap", None)
        flash = ""
        try:
            if action_name in MINT or action_name.endswith("close_quarter"):
                if not cap:
                    cap = ux.mint_cap(action_name, sealed, once=True)
                await ux.submit_intent_async(action_name, cap=cap, args=sealed)
            elif action_name in REFUSE or action_name.endswith(".wipe"):
                result = await ux.submit_intent_async(action_name, mint=False, args=sealed)
                ok = bool(getattr(result, "ok", False))
                if not ok:
                    flash = "Refused — no Cap."
                    ux.dispatch("desk_close.mark_refused", reason="no Cap")
            else:
                ux.dispatch(action_name, **sealed)
        except Exception as exc:
            flash = str(exc)

        ref_path = "/"
        try:
            ref_path = urlparse(request.headers.get("referer") or "/").path or "/"
        except Exception:
            pass
        room = _room_for_path(ref_path)
        sid = action_name.split(".", 1)[0]
        hx = str(request.headers.get("hx-request") or "").lower() in {"1", "true", "yes"}
        if hx and sid.startswith("desk_") and sid not in {"desk_theme"}:
            return _html_response(_render_unit(sid))
        inner = compose(room=room)
        if hx:
            return _html_response(inner)
        _ = flash
        return _html_response(apply_html_document(WRAP, inner))

    @asgi.post("/action/{name:path}")
    async def action_door(name: str, request: Request):
        return await _run_action(name, request)

    @asgi.post("/act/{name:path}")
    async def act_door(name: str, request: Request):
        return await _run_action(name, request)

    return asgi


if HAS_FASTAPI and app is not None:
    attach_doors(app)


if __name__ == "__main__":
    print("Pulseboard · Atelier Pulse")
    print("  Level:", int(UX.level), getattr(UX.level, "label", ""))
    print("  Board:", sorted(k for k in (BUNDLE.unit_registry or {}) if str(k).startswith("desk_")))
    print("  Serve: PYTHONPATH=src:. uxcompose serve apps.pulseboard.server:app --host 0.0.0.0 --port 8080")
