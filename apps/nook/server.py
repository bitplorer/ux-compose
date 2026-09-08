"""Uvicorn target — same Document-path ASGI as apps.nook.app."""

from apps.nook.app import BUNDLE, UX, asgi

app = asgi

__all__ = ["UX", "asgi", "app", "BUNDLE"]
