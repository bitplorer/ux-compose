"""Shared helpers for full-length examples.

Isolation Law: this module never imports ux_channel or CEK.

Two clocks, one helper set:
- Authority: ``control()`` attrs + ``@action(caps=...)``.
- Presence: optional Motion Plans when ux-motion is installed.

``tick`` flips a qualitative MorphState stamp so RefState-only mutations morph.

L1 offline still accepts MorphState(0). We teach the live-safe form so the
same class survives ``App.use_channel()`` with zero rewrite.

``act()`` emits a progressive form: hidden fields + submit. The studio host
posts ``application/x-www-form-urlencoded`` (not multipart FormData) so
Behavior never sees a WebKit boundary as a kwarg.
"""
from __future__ import annotations

from typing import Any, Optional

from ux_compose import (
    HAS_DOM,
    button,
    control,
    form,
    input_,
    span,
)

try:
    from ux_compose import scene, rise, fade
except Exception:  # pragma: no cover
    scene = rise = fade = None
try:
    from ux_motion import slide
except Exception:  # pragma: no cover
    slide = None


def tick(comp: Any, *, on: str = "tick", off: str = "tock") -> None:
    """Flip a qualitative MorphState stamp so RefState-only mutations morph."""
    cur = str(getattr(comp, "stamp", "") or "")
    setattr(comp, "stamp", off if cur == on else on)


def maybe_plan(name: str, target: str, *, ms: int = 140):
    """Build a rise-enter Plan when Motion is installed; else None.

    XOR: the Plan carries recipes only — never html=. Morph HTML comes from
    ``update_with(component)`` which serializes live ``render()``.
    """
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
    """POST form bound to ``/act/{action}``. Fully-qualified action names.

    ``kind``: primary | secondary | ghost | text
    ``on``: Channel ``data-channel-on`` grammar (e.g. ``\"click swipe.left\"``, ``\"input delay:200\"``).
    Extra kwargs become hidden fields *and* ``control()`` data-ux-arg-*.
    """
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
    """Labeled-enough input. Name is the action arg the host will parse."""
    if HAS_DOM and input_ is not None:
        return input_(
            type=kind,
            name=name,
            value=value,
            placeholder=placeholder,
            className="field",
        )
    return (
        f'<input type="{kind}" name="{name}" value="{value}" '
        f'placeholder="{placeholder}" class="field"/>'
    )


def status(text: str):
    if HAS_DOM and span is not None:
        return span(text, className="status")
    return f'<span class="status">{text}</span>'
