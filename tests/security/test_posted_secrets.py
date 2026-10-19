"""A posted secret is never painted into a page, for any visitor.

A password, an OTP code, and any ``type=password`` input stay out of the
HTML. The other visitor is a second GET of the same process: kit state is
not per visitor, so that page is the one they receive.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from tests.asgi_http import asgi_get, asgi_post_json
from tests.security.test_kit_wire_fields import _KITS, _Tree, _controls
from ux_compose import App
from ux_compose.components.login import Login
from ux_compose.components.otp import Otp
from ux_compose.components.passwordfield import PasswordField

_CHANNEL = "application/ux-channel+json"
_PASSWORD = "pw-SECRET-99"
_CODE = "482916"
_CLIENT_A = ("10.1.0.1", 4101)
_CLIENT_B = ("10.2.0.2", 4102)


def _serve(component):
    app = App.boot("Secrets", strict_caps=True)
    app.add(component)
    asgi = FastAPI()
    app.use_channel(asgi_app=asgi)
    inst = app.behavior.get(component.id)

    @asgi.get("/")
    def page():
        return HTMLResponse(str(inst.render()))

    return asgi, inst


def _post(asgi, ctrl, form, client=_CLIENT_A):
    return asgi_post_json(
        asgi,
        "/ux-channel/action",
        {
            "v": "1",
            "action": ctrl["action"],
            "args": ctrl["sealed"],
            "cap": ctrl["cap"],
            "form": form,
        },
        headers={
            "content-type": _CHANNEL,
            "accept": _CHANNEL,
            "x-channel-session": f"visitor-{client[0]}",
        },
        client=client,
    )


def _control(inst, action, **sealed):
    controls = _controls(str(inst.render()))
    for ctrl in controls:
        if ctrl["action"] != action:
            continue
        if all(ctrl["sealed"].get(key) == value for key, value in sealed.items()):
            return ctrl
    raise AssertionError(f"no {action} {sealed}")


def _pages(asgi, _inst):
    """Two clients. The route renders the shared component for each."""
    pages = []
    for client in (_CLIENT_A, _CLIENT_B):
        pages.append(
            asgi_get(
                asgi,
                "/",
                client=client,
                headers={"x-channel-session": f"visitor-{client[0]}"},
            ).text
        )
    return pages


def test_posted_password_is_absent_from_every_visitors_page():
    asgi, inst = _serve(Login)
    ctrl = _control(inst, "login.set_field", field="password")
    posted = _post(asgi, ctrl, {"email": "ada-a@x.test", "password": _PASSWORD})
    assert posted.status_code == 200, posted.text
    for html in _pages(asgi, inst):
        assert _PASSWORD not in html
        password = _input(html, "login-password")
        assert password.get("value", "") == ""
    reveal = _control(inst, "login.toggle_password")
    revealed = _post(asgi, reveal, {"email": "ada-a@x.test", "password": _PASSWORD})
    assert revealed.status_code == 200, revealed.text
    for html in _pages(asgi, inst):
        assert _PASSWORD not in html
        assert _input(html, "login-password").get("value", "") == ""


def test_posted_otp_code_is_absent_from_every_visitors_page():
    asgi, inst = _serve(Otp)
    ctrl = _control(inst, "otp.set_field", field="code")
    posted = _post(asgi, ctrl, {"code": _CODE})
    assert posted.status_code == 200, posted.text
    for html in _pages(asgi, inst):
        assert _CODE not in html
        assert _input(html, "otp-code").get("value", "") == ""


def test_every_password_type_input_renders_empty():
    """Login is the kit with ``type=password``. A posted value is not its ``value``."""
    found = []
    for kit, component, prelude in (*_KITS, ("passwordfield", PasswordField, None)):
        app = App.boot(kit, strict_caps=False)
        app.add(component)
        inst = app.behavior.get(component.id)
        if prelude:
            with app.trust():
                app.dispatch(prelude)
        for node in _controls(str(inst.render())):
            for name, typ in node["types"].items():
                if typ == "password":
                    found.append((kit, name, node["form"].get(name, "")))
    assert {kit for kit, _name, _value in found} == {"login"}
    asgi, inst = _serve(Login)
    ctrl = _control(inst, "login.set_field", field="password")
    _post(asgi, ctrl, {"password": _PASSWORD})
    for html in _pages(asgi, inst):
        typed = [
            node
            for node in _nodes(html)
            if node.get("type") == "password" or node.get("name") == "password"
        ]
        assert typed, html
        assert all(node.get("value", "") == "" for node in typed)


def _nodes(html):
    return [
        node.attrs
        for node in _tree(html).all
        if node.tag == "input"
    ]


def _input(html, element_id):
    for attrs in _nodes(html):
        if attrs.get("id") == element_id:
            return attrs
    raise AssertionError(f"no input {element_id}")


def _tree(html):
    tree = _Tree()
    tree.feed(html)
    return tree
