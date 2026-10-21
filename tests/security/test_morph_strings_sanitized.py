"""A plain ``str`` sent as morph HTML is untrusted, like a route body.

``update_with(html=str)``, ``ux_behavior.update(target, str)``, a motion
``enter`` ``html`` and a wire-shape ``morph`` / ``swap`` dict all reach the
client through ``wire.caps.ops_to_wire``, which sends a plain ``str``
through ux-dom ``sanitize_html``. ``Markup`` stays explicit trust, and HTML
compose renders from a tree is trusted, so ``hx-*`` / ``x-*`` survive.

End to end: a live App, the real ``ux-channel.js`` (and ``ux-motion``
player) in Chromium, a click on each control, then every handler in the
morphed region is fired.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from markupsafe import Markup
from ux_behavior import update
from ux_dom.dom import button, div, section

from tests.security.test_route_strings_sanitized import _FIRE, _Chrome, _serve
from ux_compose import (
    App,
    Component,
    MorphState,
    action,
    control,
    fade,
    scene,
    update_with,
)
from ux_compose.wire.caps import ops_to_wire, register_live_channel

ATTACK = (
    '<div id="xss"><b id="hov" onmouseover="alert(1)">hover</b>'
    '<img src=x onerror=alert(2)><a id="js" href="javascript:alert(3)">y</a>'
    "<script>alert(4)</script><svg onload=alert(5)></svg></div>"
)
INERT = '<div id="xss"><b id="hov">hover</b><img src="x"><a id="js">y</a><svg></svg></div>'
STAGE = '<b id="hov" onmouseover="alert(6)">hover</b><img src=x onerror=alert(7)>'
TREE_ATTRS = {
    "hx-post": "/x",
    "hx-target": "#xss",
    "x-on:click": "open = true",
    "x-data": "{open: false}",
}


class Xss(Component):
    id = "xss"
    n = MorphState(0)

    def render(self):
        label = f"tree {int(self.n or 0)}"
        return div(button(label, id="tree-btn", **TREE_ATTRS), id="xss")

    def _bump(self) -> None:
        self.n = int(self.n or 0) + 1

    @action(caps=())
    def html_kw(self):
        return update_with(self, html=ATTACK)

    @action(caps=())
    def behavior_update(self):
        return [update("#xss", ATTACK)]

    @action(caps=())
    def motion_enter(self):
        self._bump()
        return update_with(self, scene("s").enter("#stage", fade(), html=STAGE))

    @action(caps=())
    def html_kw_bytes(self):
        return update_with(self, html=ATTACK.encode())

    @action(caps=())
    def behavior_update_bytes(self):
        return [update("#xss", ATTACK.encode())]

    @action(caps=())
    def markup(self):
        return update_with(self, html=Markup(ATTACK))

    @action(caps=())
    def motion_markup(self):
        self._bump()
        return update_with(self, scene("s").enter("#stage", fade(), html=Markup(STAGE)))

    @action(caps=())
    def tree(self):
        self._bump()
        return update_with(self)


UNTRUSTED = (
    "html_kw",
    "behavior_update",
    "motion_enter",
    "html_kw_bytes",
    "behavior_update_bytes",
)  # ux-motion's own IR refuses bytes html in enter(); the wire contract test covers it
TRUSTED = ("markup", "motion_markup")


def _html_ops(ops) -> list[str]:
    return [op["html"] for op in ops_to_wire(ops) if op["op"] in ("morph", "swap")]


def _stage_html(ops) -> str:
    play = next(op for op in ops_to_wire(ops) if op["op"] == "transition.play")
    return play["plan"]["root"]["children"][0]["html"]


def test_update_with_html_and_behavior_update_strings_are_sanitized():
    inst = Xss()
    assert _html_ops(inst.html_kw()) == [INERT]
    assert _html_ops(inst.behavior_update()) == [INERT]


def test_wire_shape_morph_and_swap_dicts_are_sanitized():
    ops = [
        {"op": "morph", "target": "#xss", "html": ATTACK},
        {"op": "swap", "target": "#xss", "html": ATTACK.encode(), "swap": "outerHTML"},
    ]
    assert _html_ops(ops) == [INERT, INERT]


def test_motion_enter_html_string_is_sanitized_and_markup_kept():
    inst = Xss()
    assert _stage_html(inst.motion_enter()) == '<b id="hov">hover</b><img src="x">'
    assert _stage_html(inst.motion_markup()) == STAGE
    plan = {"op": "transition.play", "plan": {"tracks": [{"target": "#a", "html": ATTACK}]}}
    assert ops_to_wire([plan])[0]["plan"]["tracks"][0]["html"] == INERT
    assert plan["plan"]["tracks"][0]["html"] == ATTACK  # the author's plan is not mutated


def test_markup_and_tree_output_go_as_written():
    inst = Xss()
    assert _html_ops(inst.markup()) == [ATTACK]
    (html,) = _html_ops(inst.tree())
    for key, value in TREE_ATTRS.items():
        assert f'{key}="{value}"' in html


# --- live client in Chromium -------------------------------------------------

_PLAYER = Path(__import__("ux_motion").__file__).parent / "scripts" / "ux-motion-player.js"
# Fire every handler inside #zone only: the control buttons stay unclicked.
_FIRE_ZONE = _FIRE.replace(
    "document.querySelectorAll(", "document.getElementById('zone').querySelectorAll("
)
_TREE_TEXT = "(document.getElementById('tree-btn') || {}).textContent || ''"


def _page(inst) -> str:
    buttons = "".join(
        str(button(name, id=f"do-{name}", **control(f"xss.{name}")))
        for name in (*UNTRUSTED, *TRUSTED, "tree")
    )
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        '<body data-channel-endpoint="/ux-channel/action">'
        f'<main>{buttons}</main><div id="zone">{inst.__render__()}{section(id="stage")}</div>'
        '<script src="/ux-channel/static/ux-channel.js"></script>'
        '<script src="/motion.js"></script>'
        "<script>uxChannel.registerOp('transition.play',"
        " function (op) { return UxMotion.applyOp(op); });</script>"
        "</body></html>"
    )


@pytest.fixture(scope="module")
def live():
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, Response

    app = App.boot("MorphSanitize")
    app.add(Xss)
    asgi = FastAPI()
    app.use_channel(asgi_app=asgi)
    inst = app.behavior.get("xss")
    channel = app._channel

    @asgi.get("/")
    def home():
        return HTMLResponse(_page(inst))

    @asgi.get("/motion.js")
    def motion():
        return Response(_PLAYER.read_text(encoding="utf-8"), media_type="text/javascript")

    async def with_channel(scope, receive, send):
        register_live_channel(channel)
        await asgi(scope, receive, send)

    server, thread, origin = _serve(with_channel)
    browser = _Chrome()
    try:
        yield browser, origin
    finally:
        browser.close()
        server.should_exit = True
        thread.join(timeout=5)


def _eval(browser: _Chrome, expression: str):
    result = browser.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
        browser.session,
    )
    return result.get("result", {}).get("result", {}).get("value")


def _click(browser: _Chrome, origin: str, name: str) -> tuple[int, str]:
    """Click ``xss.<name>``, wait for the morph, fire every handler in #zone."""
    browser.call("Page.navigate", {"url": origin + "/"}, browser.session)
    deadline = time.time() + 10
    ready = "document.readyState === 'complete' && typeof window.UxMotion === 'object'"
    while not _eval(browser, ready):
        assert time.time() < deadline, "ux-channel.js / ux-motion did not load"
        time.sleep(0.05)
    tree_text = _eval(browser, _TREE_TEXT)
    before = browser.hits
    _eval(browser, f"document.getElementById({json.dumps('do-' + name)}).click()")
    while _eval(browser, _TREE_TEXT) == tree_text:
        assert time.time() < deadline, f"{name}: no morph"
        time.sleep(0.05)
    if name.startswith("motion"):
        while not _eval(browser, "!!document.querySelector('#stage #hov')"):
            assert time.time() < deadline, f"{name}: no enter html"
            time.sleep(0.05)
    _eval(browser, _FIRE_ZONE)
    time.sleep(0.2)
    html = _eval(browser, "document.getElementById('zone').innerHTML")
    return browser.hits - before, html


@pytest.mark.parametrize("name", UNTRUSTED)
def test_chromium_untrusted_morph_string_runs_no_script(live, name):
    browser, origin = live
    hits, html = _click(browser, origin, name)
    assert hits == 0, html
    assert 'id="hov"' in html
    assert "onmouseover" not in html and "onerror" not in html


@pytest.mark.parametrize("name", TRUSTED)
def test_chromium_markup_morph_runs_script_so_the_oracle_is_live(live, name):
    browser, origin = live
    hits, html = _click(browser, origin, name)
    assert hits > 0, html


def test_chromium_tree_morph_keeps_hx_and_alpine_attributes(live):
    browser, origin = live
    _hits, html = _click(browser, origin, "tree")
    for key, value in TREE_ATTRS.items():
        assert f'{key}="{value}"' in html, html
