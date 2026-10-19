"""A typed Login password survives Show and Hide in that visitor's browser.

The server still paints ``value=""``. ``data-ux-keep-value`` asks
``ux-channel.js`` ``applyMorph`` to copy the live value back after
``replaceWith`` and after Idiomorph. Sign-in posts that value.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from websockets.sync.client import connect

from ux_compose import App
from ux_compose.components.login import Login
from ux_compose.wire.caps import register_live_channel

_EMAIL = "you@atelier.test"
_PASSWORD = "password12"
_STORED = "stored-secret-99"


def _chrome_bin() -> str:
    """Real Chrome. A missing browser fails the test.

    ``UX_KEEP_VALUE_REQUIRE_BROWSER=1`` only changes the failure message.
    The tests fail either way. They do not skip.
    """
    found = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if found:
        return found
    required = os.environ.get("UX_KEEP_VALUE_REQUIRE_BROWSER") == "1"
    prefix = "UX_KEEP_VALUE_REQUIRE_BROWSER=1 and " if required else ""
    pytest.fail(f"{prefix}Chrome is not on PATH")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _page(inst) -> str:
    body = str(inst.render())
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head>"
        "<body data-channel-endpoint=\"/ux-channel/action\">"
        f"{body}"
        "<script src=\"/ux-channel/static/ux-channel.js\"></script>"
        "</body></html>"
    )


@pytest.fixture(scope="module", params=(False, True), ids=("strict-caps-off", "strict-caps-on"))
def login_origin(request):
    app = App.boot(f"LoginTyped{int(request.param)}", strict_caps=request.param)
    app.add(Login)
    asgi = FastAPI()
    app.use_channel(asgi_app=asgi)
    inst = app.behavior.get("login")
    channel = app._channel

    @asgi.get("/")
    def home():
        return HTMLResponse(_page(inst))

    async def _with_channel(scope, receive, send):
        # use_channel sets the live channel on this context. The request
        # task is a different one, and bind() mints caps from that context.
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
        raise RuntimeError("login server did not start")
    try:
        yield {"origin": f"http://127.0.0.1:{port}/", "inst": inst}
    finally:
        server.should_exit = True
        thread.join(timeout=5)


class _Chrome:
    def __init__(self):
        self.profile = tempfile.mkdtemp(prefix="ux-login-")
        self.proc = subprocess.Popen(
            [
                _chrome_bin(),
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--remote-debugging-port=0",
                f"--user-data-dir={self.profile}",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.browser_ws = self._devtools_ws()
        self.ws = connect(self.browser_ws, max_size=8_000_000)
        self._n = 0
        self.session = self._attach()

    def _devtools_ws(self) -> str:
        assert self.proc.stderr is not None
        deadline = time.time() + 15
        while time.time() < deadline:
            line = self.proc.stderr.readline()
            if not line:
                if self.proc.poll() is not None:
                    raise RuntimeError("chrome exited before DevTools came up")
                continue
            if "DevTools listening on" in line:
                return line.split("DevTools listening on", 1)[1].strip()
        raise RuntimeError("chrome did not open a DevTools port")

    def _attach(self) -> str:
        created = self.call("Target.createTarget", {"url": "about:blank"})
        attached = self.call(
            "Target.attachToTarget",
            {"targetId": created["result"]["targetId"], "flatten": True},
        )
        return attached["result"]["sessionId"]

    def call(self, method: str, params: dict | None = None, session: str | None = None):
        self._n += 1
        message = {"id": self._n, "method": method, "params": params or {}}
        if session:
            message["sessionId"] = session
        self.ws.send(json.dumps(message))
        while True:
            raw = json.loads(self.ws.recv())
            if raw.get("id") == self._n:
                if "error" in raw:
                    raise RuntimeError(raw["error"])
                return raw

    def evaluate(self, expression: str):
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            self.session,
        )
        payload = result["result"]["result"]
        if payload.get("subtype") == "error" or result["result"].get("exceptionDetails"):
            raise RuntimeError(payload.get("description") or payload)
        return payload.get("value")

    def goto(self, url: str):
        self.call("Page.enable", session=self.session)
        self.call("Page.navigate", {"url": url}, self.session)
        deadline = time.time() + 10
        while time.time() < deadline:
            ready = self.evaluate("document.readyState")
            wired = self.evaluate("typeof window.uxChannel === 'object'")
            if ready == "complete" and wired:
                return
            time.sleep(0.05)
        raise RuntimeError("page did not load ux-channel.js")

    def close(self):
        self.ws.close()
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)


@pytest.fixture(scope="module")
def chrome():
    browser = _Chrome()
    try:
        yield browser
    finally:
        browser.close()


def _reset(inst) -> None:
    inst.authed = False
    inst.show_password = False
    inst.submitting = False
    inst.mode = "login"
    inst.password = _STORED
    inst.email = ""
    inst.name = ""
    inst.err_password = inst.err_email = inst.err_name = inst.err_form = ""
    inst.signed_in_with = []


def _watch_authenticate(inst) -> None:
    if getattr(inst, "_auth_watched", False):
        return
    real = inst.authenticate

    def spy(*, email: str, password: str, name: str, signup: bool):
        inst.signed_in_with.append(password)
        return real(email=email, password=password, name=name, signup=signup)

    inst.authenticate = spy
    inst._auth_watched = True


def _sign_in_after(chrome: _Chrome, page: dict, steps: list[str]) -> str:
    inst = page["inst"]
    _watch_authenticate(inst)
    _reset(inst)
    chrome.goto(page["origin"])
    chrome.evaluate(
        f"""
        document.querySelector('#login-email').value = {json.dumps(_EMAIL)};
        const pw = document.querySelector('#login-password');
        pw.focus();
        pw.value = {json.dumps(_PASSWORD)};
        """
    )
    for step in steps:
        if step == "show":
            _click_until(
                chrome,
                '[data-channel-action="login.toggle_password"]',
                "document.querySelector('[data-channel-action=\"login.toggle_password\"]').textContent.includes('Hide')",
            )
        elif step == "hide":
            _click_until(
                chrome,
                '[data-channel-action="login.toggle_password"]',
                "document.querySelector('[data-channel-action=\"login.toggle_password\"]').textContent.includes('Show')",
            )
        elif step == "sign":
            chrome.evaluate(
                "document.querySelector('[data-channel-action=\"login.submit\"]').click()"
            )
        else:
            raise AssertionError(step)
    _wait(
        chrome,
        "document.body.innerText.includes(\"You're in\") || document.body.innerText.includes('Enter your password') || document.body.innerText.includes('at least 8')",
    )
    return str(chrome.evaluate("document.body.innerText"))


def _wait(chrome: _Chrome, predicate: str, timeout: float = 8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if chrome.evaluate(predicate):
            return
        time.sleep(0.05)
    text = chrome.evaluate("document.body.innerText")
    value = chrome.evaluate(
        "document.querySelector('#login-password') && document.querySelector('#login-password').value"
    )
    raise AssertionError(f"timed out. password={value!r}\n{text}")


def _click_until(chrome: _Chrome, selector: str, predicate: str):
    """Click until the page changes.

    ux-channel.js drops a second click on the same control for 280ms.
    Show then Hide is that pair, so one click can be ignored.
    """
    deadline = time.time() + 8
    quoted = json.dumps(selector)
    while time.time() < deadline:
        chrome.evaluate(f"document.querySelector({quoted}).click()")
        try:
            _wait(chrome, predicate, timeout=0.4)
            return
        except AssertionError:
            continue
    _wait(chrome, predicate)


def _assert_typed_password(page: dict, text: str) -> None:
    assert "You're in" in text
    signed = list(page["inst"].signed_in_with)
    assert signed == [_PASSWORD]
    assert _STORED not in signed


def test_typed_password_survives_show_then_sign_in(chrome, login_origin):
    text = _sign_in_after(chrome, login_origin, ["show", "sign"])
    _assert_typed_password(login_origin, text)


def test_typed_password_survives_show_hide_then_sign_in(chrome, login_origin):
    text = _sign_in_after(chrome, login_origin, ["show", "hide", "sign"])
    _assert_typed_password(login_origin, text)
