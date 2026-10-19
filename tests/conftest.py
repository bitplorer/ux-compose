"""Isolate the live-channel registry so tests do not leak Caps across cases.

Outside dev, ux-behavior refuses to attach Channel without a secret.
The suite sets one here. A test that must observe the refusal builds a
child process with the variable removed.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("UX_CHANNEL_SECRET", "ux-compose-ci-channel-secret")


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
