"""Cap-verified wire calls stay trusted. A call Channel did not accept does not.

ux-behavior #20 grants trust for one call via ``dispatch_verified``.
A bool does not. The wire calls that helper only after Channel accepts
the Cap. A task started during the call does not inherit the trust.
This test fails while the handler still passes a bool.
"""
from __future__ import annotations

import importlib.util
import json

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


def test_payload_action_binds_and_self_is_not_passed_on():
    """A posted self stays absent. A declared field named action arrives.

    The component instance is bound positionally and stays the component.
    A payload key named ``self`` is not passed into ``**extra``.
    """
    got: dict[str, object] = {}

    class Box(Component):
        id = "box"

        def render(self):
            return '<div id="box"></div>'

        @action(caps=("box.save",))
        def save(self, /, action: str = "", **extra):
            got["id"] = self.id
            got["action"] = action
            got["self"] = extra.get("self", "absent")
            return []

    app = App.boot("Box", strict_caps=True)
    app.add(Box)
    app.use_channel()
    payload = {"action": "keep", "self": "me"}
    cap = app.mint_cap("box.save", payload)
    accepted = app.submit_intent("box.save", cap=cap, args=payload)
    assert getattr(accepted, "ok", None) is True, repr(accepted)
    assert got == {"id": "box", "action": "keep", "self": "absent"}, repr(accepted)


def test_payload_self_on_a_normal_method_is_not_a_500():
    """A normal method already binds self. A posted self is a validation error.

    The action does not run. The wire returns that the same way as any other
    unexpected keyword, and the result is never a 500.
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
    body = response.json()
    error = body.get("error") or {}
    assert error.get("code") != "internal"
    assert "unexpected keyword argument 'self'" in response.text
    assert "Traceback" not in response.text
    assert ran["n"] == 0


def _validation_shape(response, keyword: str) -> tuple[int, dict]:
    """Status plus body, with the keyword name and per-request meta removed."""
    body = response.json()
    meta = dict(body.get("meta") or {})
    meta.pop("request_id", None)
    meta.pop("duration_ms", None)
    body["meta"] = meta
    for op in body.get("ops") or []:
        html = op.get("html")
        if isinstance(html, str):
            op["html"] = html.replace(f"'{keyword}'", "'KEY'")
    return response.status_code, body


def test_payload_self_matches_any_other_validation_error():
    """A payload key named self uses the ordinary validation result.

    Same HTTP status and same result shape as another unexpected keyword.
    There is no separate status for this key, and neither response is a 500.
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

    def post(payload: dict):
        cap = app.mint_cap("box.save", payload)
        return asgi_post_json(
            asgi,
            "/ux-channel/action",
            {"v": "1", "action": "box.save", "args": payload, "cap": cap},
        )

    self_key = post({"action": "keep", "self": "me"})
    other = post({"action": "keep", "note": "x"})
    assert self_key.status_code == other.status_code
    assert self_key.status_code != 500, self_key.text
    assert _validation_shape(self_key, "self") == _validation_shape(other, "note")
    assert "unexpected keyword argument 'self'" in self_key.text


def test_control_and_mint_cap_take_the_action_name_positionally():
    """A payload key named action is caller data, same as App.dispatch.

    ``control('box.open', action='x')`` and ``mint_cap('box.save', action='x')``
    pass the key through. The action name itself stays the positional argument.
    """
    app = App.boot("Box", level=1, strict_caps=False)
    app.use_channel()
    attrs = app.control("box.open", action="x")
    assert json.loads(attrs["data-channel-args"])["action"] == "x"
    cap = app.mint_cap("box.save", action="x")
    assert isinstance(cap, str) and len(cap) > 8
    assert "unexpected keyword argument 'note'" in other.text
    assert ran["n"] == 0
