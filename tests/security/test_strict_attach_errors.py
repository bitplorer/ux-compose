"""``strict_attach`` lets the original attach error out.

``wire/boot.py`` sets ``behavior.strict_attach = True`` before ``attach()``.
A missing secret and a 13-character secret are both ``RuntimeError`` from
attach itself (``ATTACH_SECRET_REQUIRED``): attach checks the secret with
ux-behavior's ``attach_secret_problem``, whose length rule is ux-channel's.
"""
from __future__ import annotations

import re

import pytest
from fastapi import FastAPI

from ux_compose import App

_MISSING = (
    "attach() requires UX_CHANNEL_SECRET or UX_BEHAVIOR_SECRET outside dev; "
    "the public dev secret is not accepted"
)
_SHORT = "capability secret must be at least 16 characters"
_SHORT_SECRET = "shortsecret13"


def _quiet_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UX_CHANNEL_SECRET", raising=False)
    monkeypatch.delenv("UX_BEHAVIOR_SECRET", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)


def test_missing_secret_is_runtimeerror(monkeypatch):
    _quiet_env(monkeypatch)
    app = App.boot("AttachMissing")
    with pytest.raises(RuntimeError, match=re.escape(_MISSING)):
        app.use_channel(asgi_app=FastAPI())
    assert app._channel is None


def test_short_secret_is_runtimeerror(monkeypatch):
    assert len(_SHORT_SECRET) == 13
    _quiet_env(monkeypatch)
    app = App.boot("AttachShort")
    with pytest.raises(RuntimeError, match=re.escape(_SHORT)):
        app.use_channel(asgi_app=FastAPI(), secret=_SHORT_SECRET)
    assert app._channel is None
