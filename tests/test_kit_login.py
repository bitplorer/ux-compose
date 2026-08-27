"""Drop-in login card: attach-on-morph, Caps, isolation."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.kit import Login


def _boot(**kwargs):
    app = App.boot("KitLogin", **kwargs)
    app.add(Login)
    return app


def _html(app) -> str:
    inst = app.behavior.get("login")
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def test_toggle_attaches_password_on_morph():
    app = _boot(strict_caps=False)
    ops = app.dispatch(
        "login.toggle_password",
        email="you@atelier.test",
        password="password12",
    )
    assert isinstance(ops, list)
    html = _html(app)
    assert 'id="login"' in html
    assert "password12" in html
    assert 'type="text"' in html
    assert "Hide" in html


def test_toggle_hide_keeps_value():
    app = _boot(strict_caps=False)
    app.dispatch("login.toggle_password", password="password12", email="a@b.co")
    app.dispatch("login.toggle_password", password="password12", email="a@b.co")
    html = _html(app)
    assert "password12" in html
    assert 'type="password"' in html
    assert "Show" in html


def test_set_mode_keeps_typed_values():
    app = _boot(strict_caps=False)
    app.dispatch(
        "login.set_mode",
        mode="signup",
        email="you@atelier.test",
        password="password12",
        name="Ada",
    )
    html = _html(app)
    assert "Create account" in html
    assert "you@atelier.test" in html
    assert "password12" in html
    assert 'name="name"' in html


def test_submit_validates():
    app = _boot(strict_caps=False)
    app.dispatch("login.submit", email="bad", password="short")
    html = _html(app)
    assert "valid email" in html.lower() or "Email" in html
    inst = app.behavior.get("login")
    assert not bool(inst.authed)


def test_blocked_account_fail_closed():
    app = _boot(strict_caps=False)
    app.dispatch(
        "login.submit",
        email="you@blocked.test",
        password="password12",
    )
    inst = app.behavior.get("login")
    assert not bool(inst.authed)
    assert "not allowed" in str(inst.err_form)


def test_submit_accepts_and_clears_secret():
    app = _boot(strict_caps=False)
    app.dispatch(
        "login.submit",
        email="you@atelier.test",
        password="password12",
    )
    inst = app.behavior.get("login")
    assert bool(inst.authed)
    assert str(inst.password or "") == ""
    html = _html(app)
    assert "You're in" in html or "Signed in" in html


def test_subclass_authenticate_seam():
    class Gate(Login):
        id = "login"

        def authenticate(self, *, email, password, name, signup):
            if password != "let-ada-in":
                return self.Reject("Unknown")
            return self.Accept("Welcome Ada")

    app = App.boot("Gate", strict_caps=False)
    app.add(Gate)
    app.dispatch("login.submit", email="ada@atelier.test", password="password12")
    inst = app.behavior.get("login")
    assert not bool(inst.authed)
    app.dispatch("login.submit", email="ada@atelier.test", password="let-ada-in")
    inst = app.behavior.get("login")
    assert bool(inst.authed)


def test_submit_fail_closed_when_strict_caps():
    app = _boot(strict_caps=True)
    with pytest.raises(Exception):
        app.dispatch("login.submit", email="you@atelier.test", password="password12")


def test_kit_never_imports_channel():
    root = ROOT / "src" / "ux_compose" / "kit"
    forbidden = {"ux_channel", "cek", "cek_host"}
    violations = []
    for p in root.rglob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in forbidden:
                        violations.append(f"{p}: import {a.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.split(".")[0] in forbidden:
                    violations.append(f"{p}: from {mod}")
    assert violations == [], violations
