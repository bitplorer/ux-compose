"""Official author helpers — the public form of examples/_common.py.

Isolation Law: this module never imports ux_channel or CEK.

This module must not import ``ux_compose`` (package root) — ``__init__``
re-exports us.
"""
from __future__ import annotations

from typing import Any, Optional

from ux_compose.dom import HAS_DOM, button, form, input_, span
from ux_compose.helpers import control

try:
    from ux_motion import scene, rise, fade, slide  # type: ignore
except Exception:  # pragma: no cover
    scene = rise = fade = slide = None  # type: ignore


def tick(comp: Any, *, on: str = "tick", off: str = "tock") -> None:
    """Flip a qualitative MorphState stamp so RefState-only mutations morph."""
    cur = str(getattr(comp, "stamp", "") or "")
    setattr(comp, "stamp", off if cur == on else on)


def maybe_plan(name: str, target: str, *, ms: int = 140):
    if scene is None or rise is None:
        return None
    try:
        return scene(name).enter(target, rise.enter(ms=ms))
    except Exception:
        return None


def maybe_fade(name: str, target: str, *, ms: int = 120):
    if scene is None or fade is None:
        return None
    try:
        return scene(name).enter(target, fade.enter(ms=ms))
    except Exception:
        return None


def maybe_slide(name: str, target: str, *, direction: str = "next", ms: int = 180):
    if scene is None or slide is None:
        return None
    try:
        from ux_motion import tokens as _tok
        dist = float(_tok.dist("md"))
    except Exception:
        dist = 24.0
    x = -dist if direction == "prev" else dist
    try:
        return scene(name).enter(target, slide.enter(x=x, ms=ms))
    except Exception:
        return None


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
    if HAS_DOM and form is not None and button is not None:
        hidden = []
        if input_ is not None:
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
    attrs = control(action, **{k: str(v) for k, v in args.items()})
    extra = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    hiddens = "".join(
        f'<input type="hidden" name="{k}" value="{v}"/>' for k, v in args.items()
    )
    return (
        f'<form method="post" action="/act/{action}" data-ux="1" '
        f'data-target="{target}" class="inline"'
        + (f' data-channel-on="{on}"' if on else "")
        + ">"
        f"{hiddens}"
        f'<button type="submit" class="btn-{kind}" {extra}>{label}</button>'
        f"</form>"
    )


def field(name: str, value: str = "", *, placeholder: str = "", kind: str = "text"):
    if HAS_DOM and input_ is not None:
        return input_(
            type=kind,
            name=name,
            value=value,
            placeholder=placeholder,
            className="field",
            autocomplete="off",
        )
    return (
        f'<input class="field" type="{kind}" name="{name}" '
        f'value="{value}" placeholder="{placeholder}" autocomplete="off"/>'
    )


def status(text: Optional[str], *, kind: str = "note"):
    if not text:
        return span("", className="sr") if HAS_DOM else ""
    if HAS_DOM and span is not None:
        return span(str(text), className=f"status status-{kind}", role="status")
    return f'<span class="status status-{kind}" role="status">{text}</span>'


__all__ = [
    "tick",
    "maybe_plan",
    "maybe_fade",
    "maybe_slide",
    "act",
    "field",
    "status",
]
