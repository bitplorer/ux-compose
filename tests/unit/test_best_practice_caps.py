"""Best-practice Cap defaults: fail closed unless the author opts out."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ux_behavior import AuthorityError
from ux_compose import App, Component, action

COMP = Path(__file__).resolve().parents[2] / "src" / "ux_compose" / "components"


class _Vault(Component):
    id = "vault"

    def render(self):
        return '<div id="vault"></div>'

    @action(caps=("vault.wipe",))
    def wipe(self):
        return []


def _caps(stem: str, fn: str) -> tuple[str, ...]:
    tree = ast.parse((COMP / f"{stem}.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn:
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    for kw in dec.keywords:
                        if kw.arg == "caps":
                            return tuple(ast.literal_eval(kw.value))
    raise AssertionError(f"{stem}.{fn} not found")


def test_app_default_is_strict():
    assert App().strict_caps is True
    assert App.boot("X").strict_caps is True


def test_default_app_refuses_capped_action_without_authority():
    app = App.boot("Strict")
    app.add(_Vault)
    with pytest.raises(AuthorityError):
        app.dispatch("vault.wipe")


def test_unchecked_mode_is_explicit_opt_out():
    app = App.boot("Open", strict_caps=False)
    app.add(_Vault)
    app.dispatch("vault.wipe")


def test_liveorder_place_minted_shares_place_cap():
    assert _caps("liveorder", "place_minted") == _caps("liveorder", "place") == ("orders.place",)


def test_login_logout_is_capped_like_other_sign_outs():
    assert _caps("login", "logout") == _caps("usermenu", "sign_out") == ("auth.logout",)


def test_build_product_app_is_strict(tmp_path, monkeypatch):
    import sys

    from ux_compose.scaffold import create_app

    dest = tmp_path / "web"
    create_app(dest)
    monkeypatch.syspath_prepend(str(dest))
    for mod in ("document", "settings"):
        sys.modules.pop(mod, None)
    from document import document
    from ux_compose.build import build

    app, _asgi, _bundle = build(dest, host="auto", live="off", document=document)
    assert app.strict_caps is True
    app.add(_Vault)
    with pytest.raises(AuthorityError):
        app.dispatch("vault.wipe")


def _runtime_caps(stem: str, fn: str) -> tuple[str, ...]:
    import importlib
    import inspect

    from ux_compose import Component

    mod = importlib.import_module(f"ux_compose.components.{stem}")
    for _, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ == mod.__name__ and issubclass(cls, Component) and fn in vars(cls):
            return tuple(getattr(vars(cls)[fn], "_ux_behavior_caps", ()) or ())
    raise AssertionError(f"{stem}.{fn} not found")


@pytest.mark.parametrize(
    "stem,fn,cap",
    [
        ("stockbadge", "sell", "stock.adjust"),
        ("stockbadge", "restock", "stock.adjust"),
        ("signupform", "submit", "account.create"),
        ("comments", "post", "comments.post"),
        ("chat", "send", "chat.send"),
    ],
)
def test_server_state_and_user_content_actions_are_gated(stem, fn, cap):
    assert _runtime_caps(stem, fn) == (cap,)


def test_optimisticlist_rollback_stays_local():
    # rollback only drops this instance's pending "…" lines; no server write.
    assert _runtime_caps("optimisticlist", "rollback") == ()


def test_scaffold_caps_are_namespace_verb(tmp_path):
    import importlib.util
    import re

    from ux_compose.scaffold import create_app

    dest = tmp_path / "web"
    create_app(dest)
    spec = importlib.util.spec_from_file_location("scaffold_hello", dest / "routes" / "hello.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    shape = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    caps = [c for fn in vars(mod.Hello).values() for c in getattr(fn, "_ux_behavior_caps", ()) or ()]
    assert caps == ["pulse.refresh"], caps
    assert all(shape.match(c) for c in caps)


def test_build_accepts_strict_caps_opt_out(tmp_path, monkeypatch):
    import sys

    from ux_compose.scaffold import create_app

    dest = tmp_path / "web"
    create_app(dest)
    monkeypatch.syspath_prepend(str(dest))
    for mod in ("document", "settings"):
        sys.modules.pop(mod, None)
    from document import document
    from ux_compose.build import build

    app, _a, _b = build(dest, host="auto", live="off", document=document, strict_caps=False)
    assert app.strict_caps is False
