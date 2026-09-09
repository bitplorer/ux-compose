"""Construct props + demo-shell wrap for ownable kit Components.

Isolation Law: this module never pulls the wire. Kits import this from
the library the same way they import ``Component`` — ``uxcompose add``
does not rewrite the path, so copied files stay self-contained.

Host seam = construct kwargs OR subclass class consts. Instance attrs
win. Unknown kwargs fail closed. ``shell=False`` renders only the
interactive unit (no Atelier kicker / title / lede card).
"""

from __future__ import annotations

from typing import Any, ClassVar, Mapping

from ux_compose.component import Component
from ux_compose.dom import div


def apply_kit_construct(
    inst: Any,
    *,
    seams: Mapping[str, str] | None = None,
    shell: bool = True,
    **content: Any,
) -> None:
    """Bind ``shell`` plus documented content kwargs onto ``inst``.

    ``seams`` maps construct kwarg → attribute name (``actions`` →
    ``ACTIONS``). Omitted kwargs leave the class const / RefState default.
    """
    allowed = dict(seams if seams is not None else getattr(type(inst), "_SEAMS", {}))
    unknown = sorted(k for k in content if k not in allowed)
    if unknown:
        raise TypeError(
            f"{type(inst).__name__}() got unexpected construct kwargs: {', '.join(unknown)}"
        )
    inst.shell = bool(shell)
    for key, value in content.items():
        setattr(inst, allowed[key], value)


class Kit(Component):
    """Zero-arg construct stays valid for Behavior.add(cls).

    Subclasses declare ``_SEAMS`` (kwarg → attr). ``shell`` is always
    accepted and is not a content seam.
    """

    _SEAMS: ClassVar[Mapping[str, str]] = {}

    def __init__(self, *, shell: bool = True, **content: Any) -> None:
        super().__init__()
        apply_kit_construct(self, seams=self._SEAMS, shell=shell, **content)

    def kit_shell(self, *unit: Any, chrome: tuple[Any, ...] | list[Any] = (), **attrs: Any):
        """Card + demo chrome when ``shell``; otherwise the unit only."""
        if getattr(self, "shell", True):
            return div(*chrome, *unit, **attrs)
        attrs = dict(attrs)
        attrs.pop("className", None)
        unit_class = getattr(self, "class_unit", "")
        if unit_class:
            attrs["className"] = unit_class
        return div(*unit, **attrs)
