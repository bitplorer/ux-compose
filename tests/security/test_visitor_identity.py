"""Every visitor gets a server-minted subject, and page Caps are bound to it.

An anonymous visitor is ``anon:<random>`` in a signed, HttpOnly,
SameSite=Lax cookie (Secure over HTTPS). A missing or forged cookie means a
new visitor. A logged-in user (``scope["user"]``) replaces the anonymous
one. A Cap minted on one visitor's page does not run for another visitor.
"""
from __future__ import annotations

import asyncio
import re
from html.parser import HTMLParser

import pytest
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from tests.asgi_http import asgi_get, asgi_post_json
from ux_compose import App
from ux_compose.components.counter import Counter
from ux_compose.visitor import COOKIE, VisitorMiddleware, new_visitor, verify

KEY = b"k" * 32
_CHANNEL = "application/ux-channel+json"


class _Controls(HTMLParser):
    def __init__(self):
        super().__init__()
        self.caps: dict[str, str] = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("data-channel-action") and a.get("data-channel-cap"):
            self.caps[a["data-channel-action"]] = a["data-channel-cap"]


def _boot():
    app = App.boot("Visitors", strict_caps=True)
    app.add(Counter)
    asgi = FastAPI()
    app.use_channel(asgi_app=asgi)
    inst = app.behavior.get(Counter.id)

    @asgi.get("/")
    def page():
        return HTMLResponse(str(inst.render()))

    return asgi


def _visit(asgi, cookie: str | None = None):
    """GET the page. Returns (cookie to send next, caps by action, Set-Cookie)."""
    r = asgi_get(asgi, "/", headers={"cookie": cookie} if cookie else None)
    assert r.status_code == 200
    parser = _Controls()
    parser.feed(r.text)
    set_cookie = r.headers.get("set-cookie")
    if set_cookie:
        cookie = set_cookie.split(";", 1)[0]
    return cookie, parser.caps, set_cookie


def _click(asgi, cap: str, cookie: str | None):
    headers = {"content-type": _CHANNEL, "accept": _CHANNEL}
    if cookie:
        headers["cookie"] = cookie
    r = asgi_post_json(
        asgi,
        "/ux-channel/action",
        {"v": "1", "action": "counter.inc", "args": {"sku": "tick"}, "cap": cap},
        headers=headers,
    )
    return r.status_code, r.json()


# --- signing ---------------------------------------------------------------


def test_visitor_cookie_round_trips_and_rejects_tampering():
    visitor, value = new_visitor(KEY)
    assert visitor.startswith("anon:")
    assert verify(KEY, value) == visitor
    assert verify(b"x" * 32, value) is None  # another key
    name, _, mac = value.rpartition(".")
    assert verify(KEY, f"anon:chosen.{mac}") is None  # chosen id, copied mac
    assert verify(KEY, f"user:1.{mac}") is None
    for bad in (None, "", "anon:x", ".", "anon:x.", value + "x"):
        assert verify(KEY, bad) is None


# --- page GET ----------------------------------------------------------------


def test_first_visit_sets_a_signed_http_only_lax_cookie():
    _cookie, caps, set_cookie = _visit(_boot())
    assert set_cookie is not None
    assert re.fullmatch(
        rf"{COOKIE}=anon:[\w-]+\.[\w-]+; Path=/; HttpOnly; SameSite=Lax", set_cookie
    ), set_cookie
    assert "counter.inc" in caps


def test_returning_visitor_keeps_the_cookie():
    asgi = _boot()
    cookie, _caps, _ = _visit(asgi)
    again, _caps2, set_cookie = _visit(asgi, cookie)
    assert set_cookie is None
    assert again == cookie


@pytest.mark.parametrize(
    "forged",
    [
        f"{COOKIE}=anon:attacker.AAAA",
        f"{COOKIE}=garbage",
        f"{COOKIE}=",
        f'{COOKIE}="unterminated',
    ],
)
def test_forged_cookie_gets_a_fresh_visitor(forged):
    asgi = _boot()
    cookie, _caps, set_cookie = _visit(asgi, forged)
    assert set_cookie is not None
    assert cookie != forged
    assert "anon:attacker" not in cookie


def test_https_cookie_is_secure():
    seen = {}

    async def inner(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def send(message):
        if message["type"] == "http.response.start":
            seen.update(dict(message["headers"]))

    scope = {"type": "http", "scheme": "https", "headers": []}
    asyncio.run(VisitorMiddleware(inner, key=KEY)(scope, None, send))
    assert seen[b"set-cookie"].endswith(b"; HttpOnly; SameSite=Lax; Secure")


def test_logged_in_user_replaces_the_anonymous_visitor():
    from ux_compose.visitor import current_subject

    class User:
        is_authenticated = True
        identity = "user:42"

    seen = {}

    async def inner(scope, receive, send):
        seen["subject"] = current_subject()
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def send(message):
        seen["headers"] = dict(message["headers"])

    anon_cookie = f"{COOKIE}={new_visitor(KEY)[1]}".encode()
    scope = {"type": "http", "scheme": "http", "user": User(), "headers": [(b"cookie", anon_cookie)]}
    asyncio.run(VisitorMiddleware(inner, key=KEY)(scope, None, send))
    assert seen["subject"] == "user:42"
    assert b"set-cookie" not in seen["headers"]


# --- Cap bound to the visitor ------------------------------------------------


def test_cap_runs_only_for_the_visitor_it_was_minted_for():
    asgi = _boot()
    alice, alice_caps, _ = _visit(asgi)
    bob, _bob_caps, _ = _visit(asgi)
    assert alice != bob
    cap = alice_caps["counter.inc"]

    status, body = _click(asgi, cap, bob)
    assert body["ok"] is False, body
    assert body["error"]["code"] == "unauthorized", body

    status, body = _click(asgi, cap, None)
    assert body["ok"] is False, body

    status, body = _click(asgi, cap, alice)
    assert status == 200 and body["ok"] is True, body
