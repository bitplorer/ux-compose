"""Arrange a widget's data and chrome: fill slots, build its heading, wrap it in a card.

Verb-named helpers shared by every ownable widget (spec §5b).
Isolation Law: this module never pulls the wire.
"""

from __future__ import annotations

from typing import Any, Mapping

from ux_compose.dom import div, h2, p, span

HEADING_KICKER = "text-xs font-medium uppercase tracking-widest text-stone-400"
HEADING_TITLE = "m-0 font-serif text-2xl font-semibold tracking-tight"
HEADING_LEDE = "m-0 text-sm leading-relaxed text-stone-500"


def build_heading(kicker: Any, title: Any, lede: Any, *, owner: Any = None) -> tuple[Any, ...]:
    """Build the kicker / title / lede nodes; ``owner.class_*`` overrides the tokens."""
    return (
        span(kicker, className=getattr(owner, "class_kicker", HEADING_KICKER)),
        h2(title, className=getattr(owner, "class_title", HEADING_TITLE)),
        p(lede, className=getattr(owner, "class_lede", HEADING_LEDE)),
    )


def arrange_slots(
    inst: Any,
    *,
    seams: Mapping[str, str] | None = None,
    shell: bool | None = None,
    **slots: Any,
) -> bool:
    """Write documented render slots onto ``inst``. Return effective ``shell``.

    ``seams`` maps slot name → attribute (``actions`` → ``ACTIONS``).
    ``shell=None`` leaves ``self.shell`` as-is (default True).
    """
    if shell is not None:
        inst.shell = bool(shell)
    allowed = dict(seams if seams is not None else getattr(type(inst), "_SEAMS", {}))
    unknown = sorted(k for k in slots if k not in allowed)
    if unknown:
        raise TypeError(
            f"{type(inst).__name__}.render() got unexpected slots: {', '.join(unknown)}"
        )
    for key, value in slots.items():
        setattr(inst, allowed[key], value)
    return bool(getattr(inst, "shell", True))


def wrap_in_card(
    inst: Any,
    *unit: Any,
    heading: tuple[Any, ...] | list[Any] = (),
    preface: tuple[Any, ...] | list[Any] = (),
    **attrs: Any,
):
    """When ``shell`` is on, the card is the preface nodes and then the unit.
    When ``shell`` is off, the preface is omitted and only the unit is returned.
    """
    if getattr(inst, "shell", True):
        return div(*heading, *preface, *unit, **attrs)
    attrs = dict(attrs)
    attrs.pop("className", None)
    unit_class = getattr(inst, "class_unit", "")
    if unit_class:
        attrs["className"] = unit_class
    return div(*unit, **attrs)


__all__ = [
    "HEADING_KICKER",
    "HEADING_LEDE",
    "HEADING_TITLE",
    "arrange_slots",
    "build_heading",
    "wrap_in_card",
]
