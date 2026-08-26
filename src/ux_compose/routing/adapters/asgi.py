"""Compat shim — DirectoryASGI lives in ``ux_compose.routing.asgi``."""
from __future__ import annotations

from ux_compose.routing.asgi import DirectoryASGI, match_record

__all__ = ["DirectoryASGI", "match_record"]
