"""attach() must not boot when it produced no Channel."""
from __future__ import annotations

import pytest
from fastapi import FastAPI

from ux_behavior import Behavior
from ux_compose import App

_SECRET = "s" * 32


def test_use_channel_raises_when_attach_returns_no_channel(monkeypatch):
    """A None channel used to be stored and the boot continued."""

    def fake_attach(self, asgi, *args, **kwargs):
        self._wire = None
        return None

    monkeypatch.setattr(Behavior, "attach", fake_attach)
    app = App.boot("Demo")
    with pytest.raises(RuntimeError, match="no channel"):
        app.use_channel(asgi_app=FastAPI(), secret=_SECRET)
    assert app._channel is None
