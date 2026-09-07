"""Isolate the live-channel registry so tests do not leak Caps across cases."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_compose_live_channel():
    try:
        from ux_compose.wire.caps import register_live_channel
    except Exception:
        yield
        return
    register_live_channel(None)
    try:
        yield
    finally:
        register_live_channel(None)
