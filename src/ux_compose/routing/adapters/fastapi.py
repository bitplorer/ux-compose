"""Compat shim — product FastAPI host lives in ``ux_compose.routing.fastapi``."""
from __future__ import annotations

from ux_compose.routing.fastapi import bind, create, materialize, mount, page_endpoint

__all__ = ["bind", "create", "materialize", "mount", "page_endpoint"]
