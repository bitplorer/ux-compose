"""Live unit lookup after ``build()`` + ``app.add``. Isolation: no ux_channel."""

from __future__ import annotations

from typing import Any

_app = None


def bind_app(app) -> None:
    global _app
    _app = app


def unit(cid: str):
    if _app is None or getattr(_app, "behavior", None) is None:
        return None
    try:
        return _app.behavior.get(cid)
    except Exception:
        return None


def card(cid: str) -> Any:
    inst = unit(cid)
    if inst is None:
        return None
    if hasattr(inst, "render"):
        return inst.render()
    return inst


def cards(*cids: str) -> list:
    out = []
    for cid in cids:
        tree = card(cid)
        if tree is not None:
            out.append(tree)
    return out
