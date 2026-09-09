"""Leftover shims. Expire by teaching (ADR 0004).

Product path: ``ux_compose.routing.fastapi`` and ``ux_compose.routing.asgi``.
Do not add new symbols here.
"""
from __future__ import annotations

from ux_compose.routing.asgi import DirectoryASGI, match_record
from ux_compose.routing.fastapi import materialize, mount

__all__ = ["materialize", "mount", "DirectoryASGI", "match_record"]
