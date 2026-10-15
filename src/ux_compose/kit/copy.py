"""Deprecated: moved to ``ux_compose.cli.copy_component`` (one release of warnings, then removed)."""

from __future__ import annotations

import warnings as _warnings

_warnings.warn(
    "ux_compose.kit.copy is deprecated; import from ux_compose.cli.copy_component.",
    DeprecationWarning,
    stacklevel=2,
)

from ux_compose.cli.copy_component import *  # noqa: F401,F403,E402
from ux_compose.cli.copy_component import KitCopyError, copy_component, find_app_root, list_components  # noqa: E402,F401

# Same module object, so monkeypatching ux_compose.kit.<x>.ATTR still reaches the code.
import sys as _sys  # noqa: E402

_sys.modules[__name__] = _sys.modules["ux_compose.cli.copy_component"]
