"""Tiny helpers for ownable kit Components — not a base class.

Lives at package **root** on purpose. ``uxcompose add`` copies kit files
as-is; those copies must not ``import ux_compose.kit``. Do not move this
to ``kit/construct.py``.

Isolation Law: this module never pulls the wire. Kits import helpers from
the library the same way they import ``Component``.

Host seam = ``render(*, shell=None, **slots)`` OR subclass class consts.
Passed slots write through to instance attrs so later morph / ``update_with``
keeps them. Omitted slots leave the class const / current instance.
Unknown slots fail closed per file (``_SEAMS``). ``shell=False`` (kwarg
or ``self.shell``) renders only the interactive unit — no Atelier
kicker / title / lede card.
"""

from __future__ import annotations

from typing import Any, Mapping

from ux_compose.dom import div


def apply_slots(
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


def kit_shell(inst: Any, *unit: Any, chrome: tuple[Any, ...] | list[Any] = (), **attrs: Any):
    """Card + demo chrome when ``shell``; otherwise the unit only."""
    if getattr(inst, "shell", True):
        return div(*chrome, *unit, **attrs)
    attrs = dict(attrs)
    attrs.pop("className", None)
    unit_class = getattr(inst, "class_unit", "")
    if unit_class:
        attrs["className"] = unit_class
    return div(*unit, **attrs)
