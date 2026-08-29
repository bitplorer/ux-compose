"""Floor composition root. Clock A ``build()``. Isolation: no ux_channel."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs

from ux_compose.build import build

from .document import document
from .host import HOUSE
from .runtime import bind_app
from .seams import ALL, hydrate

PACKAGE = Path(__file__).resolve().parent
STATIC = PACKAGE / "static"

app, asgi, bundle = build(
    PACKAGE,
    name="Floor",
    host="auto",
    live="auto",
    document=document,
)
app.add(*ALL)
hydrate(app)
bind_app(app)

if asgi is not None and callable(getattr(asgi, "post", None)):
    try:
        from fastapi.staticfiles import StaticFiles

        asgi.mount("/static", StaticFiles(directory=str(STATIC)), name="floor_static")
    except Exception:
        pass

    from fastapi import Request

    @asgi.post("/act/{name}")
    async def act(name: str, request: Request):
        raw = await request.body()
        parsed = parse_qs(raw.decode("utf-8", "replace"))
        args = {k: (v[0] if v else "") for k, v in parsed.items()}
        target = str(args.pop("_target", "") or "").lstrip("#")
        swap = str(args.pop("_swap", "") or "")
        app.dispatch(name, **args)
        cid = (name or "").split(".", 1)[0]
        inst = None
        try:
            inst = app.behavior.get(cid)
        except Exception:
            inst = None
        ledger_html = ""
        try:
            from ux_compose.helpers import _serialize_tree

            from apps.floor.chrome import ledger

            ledger_html = _serialize_tree(ledger())
        except Exception:
            ledger_html = ""
        if swap == "none":
            return {"id": cid, "html": "", "ledger": ledger_html, "swap": "none"}
        html = ""
        out_id = target or cid
        if inst is not None and target and hasattr(inst, "_listing"):
            tree = inst._listing()
            try:
                from ux_compose.helpers import _serialize_tree

                html = _serialize_tree(tree)
            except Exception:
                html = str(tree)
        elif inst is not None:
            try:
                html = inst.__render__(pretty=False)
            except Exception:
                html = str(inst.render())
        return {"id": out_id, "html": html, "ledger": ledger_html}

__all__ = ["app", "asgi", "bundle", "HOUSE"]
