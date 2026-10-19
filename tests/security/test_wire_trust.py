"""Cap-verified wire calls stay trusted. A call Channel did not accept does not.

ux-behavior #20 grants trust for one call via ``dispatch_verified``.
A bool does not. The wire calls that helper only after Channel accepts
the Cap. A task started during the call does not inherit the trust.
This test fails while the handler still passes a bool.
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


def test_cap_verified_wire_call_runs_and_unverified_does_not():
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


def test_payload_keys_named_action_and_self_reach_the_action():
    """A valid Cap carries payload keys that share names with the entry point.

    ``action`` and ``self`` are caller data. The wire passes them through
    ``dispatch_verified(name, payload)`` and they arrive on the action.
    """
    got: dict[str, object] = {}

    class Box(Component):
        id = "box"

        def render(self):
            return '<div id="box"></div>'

        @action(caps=("box.save",))
        def save(self, /, action: str = "", **extra):
            got["action"] = action
            got["self"] = extra.get("self")
            return []

    app = App.boot("Box", strict_caps=True)
    app.add(Box)
    app.use_channel()
    payload = {"action": "keep", "self": "me"}
    cap = app.mint_cap("box.save", payload)
    accepted = app.submit_intent("box.save", cap=cap, args=payload)
    assert getattr(accepted, "ok", None) is True, repr(accepted)
    assert got == {"action": "keep", "self": "me"}, repr(accepted)


def test_payload_self_on_a_normal_method_is_not_a_500():
    """A normal method already binds self. The payload key must not 500.

    It reaches the action only when self is positional-only. Otherwise the
    wire returns the validation message and the action does not run.
    """
    from fastapi import FastAPI

    from tests.asgi_http import asgi_post_json

    ran = {"n": 0}

    class Box(Component):
        id = "box"

        def render(self):
            return '<div id="box"></div>'

        @action(caps=("box.save",))
        def save(self, action: str = ""):
            ran["n"] += 1
            return []

    app = App.boot("Box", strict_caps=True)
    app.add(Box)
    asgi = FastAPI()
    app.use_channel(asgi_app=asgi)
    payload = {"action": "keep", "self": "me"}
    cap = app.mint_cap("box.save", payload)
    response = asgi_post_json(
        asgi,
        "/ux-channel/action",
        {"v": "1", "action": "box.save", "args": payload, "cap": cap},
    )
    assert response.status_code != 500, response.text
    assert response.status_code < 500, response.text
    body = response.json()
    error = body.get("error") or {}
    assert error.get("code") != "internal"
    assert "unexpected keyword argument 'self'" in response.text
    assert "Traceback" not in response.text
    assert ran["n"] == 0
