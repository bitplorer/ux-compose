"""Every rendered control, posted the way ux-channel.js fireControl does.

``args`` is ``data-channel-args``, ``cap`` is ``data-channel-cap``, and
``form`` is every named field of the enclosing form plus the control's own
name and value. Each field carries a marker. After ``POST /ux-channel/action``
the marker has to be in the component's public state.

FormLayout, and login ``set_field`` / ``submit``, name their fields from the
form. They stay ``xfail(strict=True)`` until ux-behavior grows ``fields=``.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser

import pytest
from fastapi import FastAPI

from tests.asgi_http import asgi_post_json
from ux_compose import App
from ux_compose.components.chat import Chat
from ux_compose.components.colorpicker import ColorPicker
from ux_compose.components.combobox import Combobox
from ux_compose.components.command import Command
from ux_compose.components.filterbar import FilterBar
from ux_compose.components.formlayout import FormLayout
from ux_compose.components.login import Login
from ux_compose.components.newsletter import Newsletter
from ux_compose.components.otp import Otp
from ux_compose.components.searchbar import SearchBar
from ux_compose.components.spinbutton import SpinButton
from ux_compose.components.tagsinput import TagsInput
from ux_compose.components.typeahead import Typeahead

_VOID = {
    "input", "br", "img", "meta", "link", "hr", "area", "base",
    "col", "embed", "source", "track", "wbr",
}
_KITS = (
    ("formlayout", FormLayout, None),
    ("login", Login, None),
    ("newsletter", Newsletter, None),
    ("otp", Otp, None),
    ("combobox", Combobox, None),
    ("command", Command, "command.open_pal"),
    ("chat", Chat, None),
    ("tagsinput", TagsInput, None),
    ("searchbar", SearchBar, None),
    ("filterbar", FilterBar, None),
    ("spinbutton", SpinButton, None),
    ("colorpicker", ColorPicker, None),
    ("typeahead", Typeahead, None),
)
# These rows name fields from the form. The allowlist is a later behavior change.
_ALLOWLIST = {
    ("formlayout", "set_field"),
    ("formlayout", "submit"),
    ("login", "set_field"),
    ("login", "submit"),
}
_CHANNEL = "application/ux-channel+json"


class _Node:
    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.kids = []


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = _Node("#root", {}, None)
        self.cur = self.root
        self.all = []

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs, self.cur)
        self.cur.kids.append(node)
        self.all.append(node)
        if tag not in _VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        node = _Node(tag, attrs, self.cur)
        self.cur.kids.append(node)
        self.all.append(node)

    def handle_endtag(self, tag):
        cur = self.cur
        while cur is not self.root and cur.tag != tag:
            cur = cur.parent
        if cur is not self.root:
            self.cur = cur.parent


def _walk(node):
    for kid in node.kids:
        yield kid
        yield from _walk(kid)


def _closest_form(node):
    while node is not None and node.tag != "form":
        node = node.parent
    return node


def _marker(name, typ, kit, nth):
    kind = (typ or "").lower()
    key = (name or "").lower()
    if key == "email" or kind == "email":
        return f"ada.{kit}.{nth}@x.test"
    if key in {"code", "otp"}:
        return f"{100000 + (nth % 900000):06d}"
    if kind == "number" or key == "value":
        return "6"
    if key in {"hex", "color"} or kind == "color":
        return "#a1b2c3"
    return f"marker-{kit}-{key}-{nth}"


def _public_state(inst):
    out = {}
    for cls in type(inst).mro():
        for name, attr in vars(cls).items():
            if name.startswith("_"):
                continue
            if type(attr).__name__ in {"RefState", "MorphState"}:
                out[name] = getattr(inst, name)
    for name, val in vars(inst).items():
        if name.startswith("_") or callable(val):
            continue
        if isinstance(val, (str, int, float, bool, dict, list, tuple)) or val is None:
            out[name] = val
    return out


def _holds(state, marker):
    if _has(state, marker):
        return True
    if isinstance(marker, str) and marker.isdigit():
        return _has(state, int(marker))
    return False


def _has(node, needle):
    if node == needle:
        return True
    if isinstance(needle, str) and isinstance(node, str):
        return needle in node
    if isinstance(node, dict):
        return any(_has(val, needle) for val in node.values())
    if isinstance(node, (list, tuple)):
        return any(_has(val, needle) for val in node)
    return False


def _controls(html):
    tree = _Tree()
    tree.feed(html)
    found = []
    for node in tree.all:
        action = node.attrs.get("data-channel-action")
        if not action:
            continue
        form = {}
        types = {}
        host = _closest_form(node)
        if host is not None:
            for kid in _walk(host):
                if kid.tag not in {"input", "textarea", "select"}:
                    continue
                name = kid.attrs.get("name")
                if not name or kid.attrs.get("type") in {"button", "submit"}:
                    continue
                form[name] = kid.attrs.get("value", "")
                types[name] = kid.attrs.get("type", "")
        if node.tag in {"input", "textarea", "select"} and node.attrs.get("name"):
            form.setdefault(node.attrs["name"], node.attrs.get("value", ""))
            types.setdefault(node.attrs["name"], node.attrs.get("type", ""))
        found.append(
            {
                "action": action,
                "sealed": json.loads(node.attrs.get("data-channel-args") or "{}"),
                "cap": node.attrs.get("data-channel-cap"),
                "form": form,
                "types": types,
            }
        )
    return found


def _boot(component, prelude):
    app = App.boot("WireFields", strict_caps=True)
    app.add(component)
    asgi = FastAPI()
    app.use_channel(asgi_app=asgi)
    inst = app.behavior.get(component.id)
    if prelude:
        with app.trust():
            app.dispatch(prelude)
    return asgi, inst


def _post_row(kit, component, prelude):
    # One instance per control. A later click must not inherit an earlier marker.
    _asgi, listing = _boot(component, prelude)
    controls = _controls(str(listing.render()))
    rows = []
    for nth, _listed in enumerate(controls):
        asgi, inst = _boot(component, prelude)
        ctrl = _controls(str(inst.render()))[nth]
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
        state = _public_state(inst)
        missing = [name for name, marker in markers.items() if not _holds(state, marker)]
        method = ctrl["action"].split(".", 1)[1]
        chip = ""
        if ctrl["action"] == "filterbar.choose":
            key = str(ctrl["sealed"].get("key", ""))
            if str(inst.which) != key:
                chip = key
        rows.append(
            {
                "kit": kit,
                "method": method,
                "action": ctrl["action"],
                "sealed": ctrl["sealed"],
                "status": response.status_code,
                "missing": missing,
                "chip": chip,
                "body": response.text[:240],
            }
        )
    return rows


def _all_rows():
    out = []
    for kit, component, prelude in _KITS:
        out.extend(_post_row(kit, component, prelude))
    return out


def _line(row):
    lost = ",".join(row["missing"]) or "-"
    chip = f" chip={row['chip']}" if row["chip"] else ""
    return f"{row['action']} {row['sealed']} lost={lost}{chip} status={row['status']}"


def test_rendered_control_keeps_every_posted_field():
    lost = [
        _line(row)
        for row in _all_rows()
        if (row["kit"], row["method"]) not in _ALLOWLIST
        and (row["missing"] or row["chip"] or row["status"] != 200)
    ]
    assert lost == [], "\n".join(lost)


@pytest.mark.xfail(strict=True, reason="needs ux-behavior fields= allowlist")
def test_formlayout_and_login_rows_wait_on_fields_allowlist():
    lost = [
        _line(row)
        for row in _all_rows()
        if (row["kit"], row["method"]) in _ALLOWLIST
        and (row["missing"] or row["status"] != 200)
    ]
    assert lost == []
