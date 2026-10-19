"""One process, two visitors. A's posted field must not be on B's page.

Kit state is one instance per component id. A field that is stored and
painted is the next visitor's page. Actions that already do that on main
``c22e419`` are listed in ``_MAIN_PAINTS`` and wait on a per-visitor state
decision. Every other posted value, including PasswordField and Typeahead,
stays out of B's HTML.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from tests.asgi_http import asgi_get, asgi_post_json
from tests.security.test_kit_wire_fields import _KITS, _Tree, _boot, _controls
from ux_compose.components.passwordfield import PasswordField

_CHANNEL = "application/ux-channel+json"
# (action, field) pairs whose render on main c22e419 already includes the
# posted value. Isolating these waits on per-visitor state.
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
            response = asgi_post_json(
                asgi,
                "/ux-channel/action",
                {
                    "v": "1",
                    "action": ctrl["action"],
                    "args": ctrl["sealed"],
                    "cap": ctrl["cap"],
                    "form": markers,
                },
                headers={"content-type": _CHANNEL, "accept": _CHANNEL},
            )
            if response.status_code != 200:
                leaks.append(f"{ctrl['action']} status={response.status_code}")
                continue
            if ctrl["action"] == "password.set":
                revealed = _controls(str(inst.render()))
                toggle = next(item for item in revealed if item["action"] == "password.toggle")
                toggled = asgi_post_json(
                    asgi,
                    "/ux-channel/action",
                    {
                        "v": "1",
                        "action": toggle["action"],
                        "args": toggle["sealed"],
                        "cap": toggle["cap"],
                        "form": {},
                    },
                    headers={"content-type": _CHANNEL, "accept": _CHANNEL},
                )
                if toggled.status_code != 200:
                    leaks.append(f"password.toggle status={toggled.status_code}")
            html = asgi_get(asgi, "/").text
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
    ctrl = _controls(str(inst.render()))
    setter = next(item for item in ctrl if item["action"] == "password.set")
    secret = "zzvis-secret-revealed"
    posted = asgi_post_json(
        asgi,
        "/ux-channel/action",
        {
            "v": "1",
            "action": setter["action"],
            "args": setter["sealed"],
            "cap": setter["cap"],
            "form": {"secret": secret},
        },
        headers={"content-type": _CHANNEL, "accept": _CHANNEL},
    )
    assert posted.status_code == 200, posted.text
    toggle = next(item for item in _controls(str(inst.render())) if item["action"] == "password.toggle")
    revealed = asgi_post_json(
        asgi,
        "/ux-channel/action",
        {
            "v": "1",
            "action": toggle["action"],
            "args": toggle["sealed"],
            "cap": toggle["cap"],
            "form": {},
        },
        headers={"content-type": _CHANNEL, "accept": _CHANNEL},
    )
    assert revealed.status_code == 200, revealed.text
    for html in (str(inst.render()), asgi_get(asgi, "/").text):
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
