"""Reveal and Hide must not leave the secret in a plain-text input.

Hold stores the secret and paints ``value=""``. Reveal and Hide only
change the button. The typed secret must be gone from the DOM after
Hold and after Hide.
"""
from __future__ import annotations

import json
import threading
import time

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from tests.security.test_login_typed_password import (
    _Chrome,
    _click_until,
    _free_port,
    _wait,
)
from ux_compose import App
from ux_compose.components.passwordfield import PasswordField
from ux_compose.wire.caps import register_live_channel

_SECRET = "hunter2-long"


def _page(inst) -> str:
    body = str(inst.render())
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head>"
        "<body data-channel-endpoint=\"/ux-channel/action\">"
        f"{body}"
        "<script src=\"/ux-channel/static/ux-channel.js\"></script>"
        "</body></html>"
    )


@pytest.fixture(scope="module")
def password_origin():
    app = App.boot("PasswordTyped", strict_caps=False)
    app.add(PasswordField)
    asgi = FastAPI()
    app.use_channel(asgi_app=asgi)
    inst = app.behavior.get("password")
    channel = app._channel

    @asgi.get("/")
    def home():
        return HTMLResponse(_page(inst))

    async def _with_channel(scope, receive, send):
        register_live_channel(channel)
        await asgi(scope, receive, send)

    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(_with_channel, host="127.0.0.1", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while time.time() < deadline:
        if getattr(server, "started", False):
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("password server did not start")
    try:
        yield {"origin": f"http://127.0.0.1:{port}/", "inst": inst}
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@pytest.fixture(scope="module")
def chrome():
    browser = _Chrome()
    try:
        yield browser
    finally:
        browser.close()


def _plain_secret(chrome: _Chrome) -> str:
    """Live field values plus visible text. Attribute HTML can stay empty."""
    return str(
        chrome.evaluate(
            """
            (() => {
              const fields = [...document.querySelectorAll("input, textarea")]
                .map((el) => el.value || "");
              return fields.join("\\n") + "\\n" + (document.body.innerText || "");
            })()
            """
        )
    )


def _reset(inst) -> None:
    inst.secret = ""
    inst.shown = False
    inst.dirty = "idle"


def test_hold_and_hide_leave_no_plain_text_secret(chrome, password_origin):
    inst = password_origin["inst"]
    _reset(inst)
    chrome.goto(password_origin["origin"])
    chrome.evaluate(
        f"""
        const field = document.querySelector('input[name="secret"]');
        field.focus();
        field.value = {json.dumps(_SECRET)};
        """
    )
    chrome.evaluate('document.querySelector(\'[data-channel-action="password.set"]\').click()')
    _wait(chrome, "document.body.innerText.includes('••••••••')")
    after_hold = _plain_secret(chrome)
    assert _SECRET not in after_hold
    _click_until(
        chrome,
        '[data-channel-action="password.toggle"]',
        "document.querySelector('[data-channel-action=\"password.toggle\"]').textContent.includes('Hide')",
    )
    _click_until(
        chrome,
        '[data-channel-action="password.toggle"]',
        "document.querySelector('[data-channel-action=\"password.toggle\"]').textContent.includes('Reveal')",
    )
    after_hide = _plain_secret(chrome)
    assert _SECRET not in after_hide
