"""Compat shims for DirectoryRoutes host modules.

Product code: ``ux_compose.routing.fastapi`` and ``ux_compose.routing.asgi``.
"""
from __future__ import annotations

from ux_compose.routing.asgi import DirectoryASGI, match_record
from ux_compose.routing.fastapi import materialize, mount

__all__ = ["materialize", "mount", "DirectoryASGI", "match_record"]
