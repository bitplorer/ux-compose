"""Isolate the live-channel registry so tests do not leak Caps across cases.

Outside dev, ux-behavior refuses to attach Channel without a secret.
When the environment has none, this session generates one. A test that
must observe a refusal builds a child process with the variable removed.
"""
from __future__ import annotations

import os
import secrets

import pytest

if not os.environ.get("UX_CHANNEL_SECRET"):
    os.environ["UX_CHANNEL_SECRET"] = secrets.token_urlsafe(32)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Keep import-isolation tests in source order even if randomly is on."""
    del config
    indexes = {id(item): index for index, item in enumerate(items)}
    yield
    slots = [
        index
        for index, item in enumerate(items)
        if item.get_closest_marker("import_isolation")
    ]
    pinned = sorted((items[index] for index in slots), key=lambda item: indexes[id(item)])
    for slot, item in zip(slots, pinned):
        items[slot] = item


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
