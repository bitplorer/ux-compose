"""One process, two clients. A's posted field must not be on B's page.

Each visitor is a separate ASGI client. Actions that already paint a
posted field on main ``c22e419`` are listed in ``_MAIN_PAINTS``. That
list is only the baseline. Isolating those fields waits on the pending
per-visitor state decision. Every other posted value, including
PasswordField and Typeahead, stays out of B's HTML.
"""
from __future__ import annotations

from fastapi.responses import HTMLResponse

from tests.asgi_http import asgi_get, asgi_post_json
from tests.security.test_kit_wire_fields import _KITS, _Tree, _boot, _controls
from ux_compose.components.login import Login
from ux_compose.components.otp import Otp
from ux_compose.components.passwordfield import PasswordField

_CHANNEL = "application/ux-channel+json"
_CLIENT_A = ("10.1.0.1", 4101)
_CLIENT_B = ("10.2.0.2", 4102)
# Baseline only: fields main c22e419 already paints. Isolating them waits
# on the pending per-visitor state decision. Do not add to this list.
_MAIN_PAINTS = {
    ("login.toggle_password", "email"),
    ("login.submit", "email"),
    ("chat.send", "text"),
    ("tagsinput.add", "tag"),
    ("searchbar.search", "q"),
    ("combobox.type_query", "q"),
    ("command.type_query", "q"),
    ("spinbutton.set_value", "value"),
    ("typeahead.query_hits", "q"),
}


def _marker(name, typ, kit, nth):
    key = (name or "").lower()
    kind = (typ or "").lower()
    if key == "email" or kind == "email":
        return f"zzvis.{kit}.{nth}@x.test"
    if key in {"code", "otp"}:
        return f"{310000 + (nth % 100000):06d}"
    if key in {"hex", "color"} or kind == "color":
        return f"#b{nth % 100000:05d}"
    if kind == "number" or key == "value":
        return "8"
    if key == "password" or key == "secret":
        return f"zzvis-secret-{kit}-{nth}"
    return f"zzvis-{kit}-{nth}-{key}"


def _page(asgi, inst):
    @asgi.get("/")
    def home():
        return HTMLResponse(str(inst.render()))

    return asgi


def _session(client):
    return {"x-channel-session": f"visitor-{client[0]}"}


def _post(asgi, ctrl, form, client):
    headers = {"content-type": _CHANNEL, "accept": _CHANNEL, **_session(client)}
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
        headers=headers,
        client=client,
    )


def _get(asgi, client):
    return asgi_get(asgi, "/", client=client, headers=_session(client))


def test_other_visitor_does_not_see_posted_kit_fields():
    leaks = []
    kits = (*_KITS, ("passwordfield", PasswordField, None))
    for kit, component, prelude in kits:
        _listing_asgi, listing = _boot(component, prelude)
        controls = _controls(str(listing.render()))
        for nth, _listed in enumerate(controls):
            asgi, inst = _boot(component, prelude)
            _page(asgi, inst)
            ctrl = _controls(str(inst.render()))[nth]
            if not ctrl["form"]:
                continue
            markers = {
                name: _marker(name, ctrl["types"].get(name, ""), kit, nth)
                for name in ctrl["form"]
            }
            response = _post(asgi, ctrl, markers, _CLIENT_A)
            if response.status_code != 200:
                leaks.append(f"{ctrl['action']} status={response.status_code}")
                continue
            if ctrl["action"] == "password.set":
                revealed = _controls(_get(asgi, _CLIENT_A).text)
                toggle = next(item for item in revealed if item["action"] == "password.toggle")
                toggled = _post(asgi, toggle, {}, _CLIENT_A)
                if toggled.status_code != 200:
                    leaks.append(f"password.toggle status={toggled.status_code}")
            html = _get(asgi, _CLIENT_B).text
            for name, marker in markers.items():
                if (ctrl["action"], name) in _MAIN_PAINTS:
                    continue
                if marker in html:
                    leaks.append(f"{ctrl['action']} {name}={marker}")
    assert leaks == [], "\n".join(leaks)


def test_passwordfield_revealed_secret_is_not_painted():
    """Main paints the secret in the lede and the type=text input after Reveal."""
    asgi, inst = _boot(PasswordField, None)
    _page(asgi, inst)
    ctrl = _controls(_get(asgi, _CLIENT_A).text)
    setter = next(item for item in ctrl if item["action"] == "password.set")
    secret = "zzvis-secret-revealed"
    posted = _post(asgi, setter, {"secret": secret}, _CLIENT_A)
    assert posted.status_code == 200, posted.text
    toggle = next(item for item in _controls(_get(asgi, _CLIENT_A).text) if item["action"] == "password.toggle")
    revealed = _post(asgi, toggle, {}, _CLIENT_A)
    assert revealed.status_code == 200, revealed.text
    for html in (_get(asgi, _CLIENT_A).text, _get(asgi, _CLIENT_B).text):
        assert secret not in html
        tree = _Tree()
        tree.feed(html)
        inputs = [
            node.attrs
            for node in tree.all
            if node.tag == "input" and node.attrs.get("name") == "secret"
        ]
        assert inputs
        assert all(node.get("type") == "text" for node in inputs)
        assert all(node.get("value", "") == "" for node in inputs)


def test_password_mask_does_not_vary_with_secret_length():
    """Two secrets of different lengths must render the same HTML.

    A bullet per character tells the next visitor the length. ``empty``
    stays the face when there is no secret.
    """
    for shown in (False, True):
        pages = []
        for secret in ("ab", "abcdefghijkl"):
            inst = PasswordField()
            inst.secret = secret
            inst.shown = shown
            pages.append(str(inst.render()))
        assert pages[0] == pages[1]


def test_refused_otp_digits_are_absent_from_the_next_visitor():
    """A refused verify must not leave A's digits for B.

    Demo ``000000`` is refused. The input is already ``value=""``, so the
    page can hide the digits while ``Otp.code`` still holds them. B's HTML
    and that shared code both have to be clear.
    """
    digits = "000000"
    asgi, inst = _boot(Otp, None)
    _page(asgi, inst)
    verify = next(item for item in _controls(_get(asgi, _CLIENT_A).text) if item["action"] == "otp.verify")
    posted = _post(asgi, verify, {"code": digits}, _CLIENT_A)
    assert posted.status_code == 200, posted.text
    assert not bool(inst.ok)
    assert "not valid" in str(inst.err)
    html = _get(asgi, _CLIENT_B).text
    assert digits not in html
    assert str(inst.code or "") == ""
    tree = _Tree()
    tree.feed(html)
    inputs = [
        node.attrs
        for node in tree.all
        if node.tag == "input" and node.attrs.get("name") == "code"
    ]
    assert inputs
    assert all(node.get("value", "") == "" for node in inputs)


def test_short_otp_is_not_stored_for_either_visitor():
    """A code refused for its length must not stay stored.

    Client A posts a short code and sees ``Enter all six digits``. A's
    repaint and client B's page show none of those digits, and the shared
    code is empty.
    """
    digits = "83921"
    asgi, inst = _boot(Otp, None)
    _page(asgi, inst)
    verify = next(item for item in _controls(_get(asgi, _CLIENT_A).text) if item["action"] == "otp.verify")
    posted = _post(asgi, verify, {"code": digits}, _CLIENT_A)
    assert posted.status_code == 200, posted.text
    assert not bool(inst.ok)
    assert "Enter all six digits" in str(inst.err)
    for client in (_CLIENT_A, _CLIENT_B):
        html = _get(asgi, client).text
        assert digits not in html
        assert "Enter all six digits" in html
    assert str(inst.code or "") == ""


def _otp_page_for(code):
    asgi, inst = _boot(Otp, None)
    _page(asgi, inst)
    verify = next(item for item in _controls(_get(asgi, _CLIENT_A).text) if item["action"] == "otp.verify")
    posted = _post(asgi, verify, {"code": code}, _CLIENT_A)
    assert posted.status_code == 200, posted.text
    return inst, _get(asgi, _CLIENT_B).text


def test_otp_input_does_not_paint_another_clients_digits():
    """``otp.py`` paints ``value=""``. A second client must not see the digits.

    Covers a refused six-digit code and a short code. ``value=str(self.code)``
    would put the short code on B's page.
    """
    refused, refused_html = _otp_page_for("000000")
    assert not bool(refused.ok)
    assert "not valid" in str(refused.err)
    assert "000000" not in refused_html
    _short, short_html = _otp_page_for("83921")
    assert "83921" not in short_html
    for html in (refused_html, short_html):
        tree = _Tree()
        tree.feed(html)
        inputs = [
            node.attrs
            for node in tree.all
            if node.tag == "input" and node.attrs.get("name") == "code"
        ]
        assert inputs
        assert all(node.get("value", "") == "" for node in inputs)


def test_empty_password_does_not_sign_in_with_another_clients_secret():
    """A stores a password. B submits that form with an empty password.

    B must be refused. The empty post must not keep A's secret either.
    """
    secret = "password12"
    asgi, inst = _boot(Login, None)
    _page(asgi, inst)
    controls = _controls(_get(asgi, _CLIENT_A).text)
    toggle = next(item for item in controls if item["action"] == "login.toggle_password")
    typed = _post(
        asgi,
        toggle,
        {"email": "ada-a@x.test", "password": secret, "name": ""},
        _CLIENT_A,
    )
    assert typed.status_code == 200, typed.text
    assert str(inst.password or "") == secret
    submit = next(item for item in _controls(_get(asgi, _CLIENT_B).text) if item["action"] == "login.submit")
    posted = _post(
        asgi,
        submit,
        {"email": "bee-b@x.test", "password": "", "name": ""},
        _CLIENT_B,
    )
    assert posted.status_code == 200, posted.text
    html = _get(asgi, _CLIENT_B).text
    assert not bool(inst.authed)
    assert "You're in" not in html
    assert secret not in html
    assert str(inst.password or "") == ""
