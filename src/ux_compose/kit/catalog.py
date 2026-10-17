"""Deprecated: moved to ``ux_compose.cli.registry`` (one release of warnings, then removed)."""

from __future__ import annotations

import warnings as _warnings

_warnings.warn(
    "ux_compose.kit.catalog is deprecated; import from ux_compose.cli.registry.",
    DeprecationWarning,
    stacklevel=2,
)

from ux_compose.cli.registry import *  # noqa: F401,F403,E402
from ux_compose.cli.registry import CATALOG, ALIASES, KitEntry, list_components, resolve  # noqa: E402,F401

# Same module object, so monkeypatching ux_compose.kit.<x>.ATTR still reaches the code.
import sys as _sys  # noqa: E402

_sys.modules[__name__] = _sys.modules["ux_compose.cli.registry"]
