"""Cap-verified wire calls stay trusted. A call Channel did not accept does not.

ux-behavior #20 (674a575) grants trust only for the private wire sentinel.
A bool does not. The wire may pass that sentinel only after Channel
accepts the Cap. This test is the live contract for ``bridge_actions``:
it fails while the handler still passes a bool.
"""
from __future__ import annotations

import importlib.util

import pytest

from ux_behavior import AuthorityError
from ux_compose import App, Component, action

HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None

pytestmark = pytest.mark.skipif(
    not HAS_CHANNEL,
    reason="ux-channel required for the Cap-verified wire path",
)


def test_cap_verified_wire_call_is_trusted_and_unverified_is_not():
    """A minted Cap runs the action. A direct dispatch, and an Intent with no Cap, do not."""
    ran = {"n": 0}

    class Vault(Component):
        id = "vault"

        def render(self):
            return '<div id="vault"></div>'

        @action(caps=("vault.wipe",))
        def wipe(self):
            ran["n"] += 1
            return []

    app = App.boot("Vault", strict_caps=True)
    app.add(Vault)
    app.use_channel()
    assert app._channel is not None

    with pytest.raises(AuthorityError):
        app.dispatch("vault.wipe")
    assert ran["n"] == 0

    refused = app.submit_intent("vault.wipe", args={})
    assert getattr(refused, "ok", None) is False
    assert ran["n"] == 0

    cap = app.mint_cap("vault.wipe", {})
    assert isinstance(cap, str) and len(cap) > 8
    accepted = app.submit_intent("vault.wipe", cap=cap, args={})
    assert getattr(accepted, "ok", None) is True, repr(accepted)
    assert ran["n"] == 1, repr(accepted)
