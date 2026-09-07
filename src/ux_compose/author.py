"""Official author helpers — the public form of examples/_common.py.

Isolation Law: this module never imports ux_channel or CEK.

This module must not import ``ux_compose`` (package root) — ``__init__``
re-exports us.
"""
from __future__ import annotations

from typing import Any, Optional

from ux_compose.dom import button, form, input_, span
from ux_compose.helpers import control
from ux_motion import scene, rise, fade, slide, tokens  # type: ignore


def mark_dirty(comp: Any, *, on: str = "tick", off: str = "tock") -> None:
    """Flip a qualitative MorphState dirty flag so RefState-only mutations morph."""
    cur = str(getattr(comp, "dirty", "") or "")
    setattr(comp, "dirty", off if cur == on else on)


def optional_plan(name: str, target: str, *, ms: int = 140):
    """Motion IR via ux-motion. Public name kept; not an optional fork."""
    return scene(name).enter(target, rise.enter(ms=ms))


def optional_fade(name: str, target: str, *, ms: int = 120):
    """Motion IR via ux-motion. Public name kept; not an optional fork."""
    return scene(name).enter(target, fade.enter(ms=ms))


def optional_slide(name: str, target: str, *, direction: str = "next", ms: int = 180):
    """Motion IR via ux-motion. Public name kept; not an optional fork."""
    dist = float(tokens.dist("md"))
    x = -dist if direction == "prev" else dist
    return scene(name).enter(target, slide.enter(x=x, ms=ms))


def act(
    action: str,
    label: str,
    *,
    kind: str = "secondary",
    target: str = "#stage",
    on: str | None = None,
    **args: Any,
):
    """POST form bound to ``/act/{action}``."""
    hidden = []
    for k, v in args.items():
        hidden.append(input_(type="hidden", name=k, value=str(v)))
    form_attrs: dict = {
        "method": "post",
        "action": f"/act/{action}",
        "data_ux": "1",
        "data_target": target,
        "className": "inline",
    }
    if on:
        form_attrs["data_channel_on"] = on
    return form(
        *hidden,
        button(
            label,
            type="submit",
            className=f"btn-{kind}",
            **control(action, **{k: str(v) for k, v in args.items()}),
        ),
        **form_attrs,
    )


def field(name: str, value: str = "", *, placeholder: str = "", kind: str = "text"):
    return input_(
        type=kind,
        name=name,
        value=value,
        placeholder=placeholder,
        className="field",
        autocomplete="off",
    )


def status(text: Optional[str], *, kind: str = "note"):
    if not text:
        return span("", className="sr")
    return span(str(text), className=f"status status-{kind}", role="status")


__all__ = [
    "mark_dirty",
    "optional_plan",
    "optional_fade",
    "optional_slide",
    "act",
    "field",
    "status",
]
