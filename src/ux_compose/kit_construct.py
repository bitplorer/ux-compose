"""Shim: old names for ``ux_compose.arrange`` helpers, kept for copied kit files.

Not under ``kit/``. Copy rewrites ``from ux_compose.kit.X import`` to a
relative sibling and drops ``X.py`` into the app. This module must stay a
library import, same as ``Component``::

    from ux_compose.kit_construct import apply_slots, kit_shell

Isolation Law: this module never pulls the wire.

Host seam = ``render(*, shell=None, **slots)`` OR subclass class consts.
Passed slots write through to instance attrs so later morph / ``update_with``
keeps them. Omitted slots leave the class const / current instance.
Unknown slots fail closed per file (``_SEAMS``). ``shell=False`` (kwarg
or ``self.shell``) renders only the interactive unit — no Atelier
kicker / title / lede card.
"""

from __future__ import annotations

from ux_compose.arrange import arrange_slots as apply_slots
from ux_compose.arrange import wrap_in_card as kit_shell

__all__ = ["apply_slots", "kit_shell"]
