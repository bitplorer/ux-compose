"""CTO gate 2: Cap mint on control() when Cap Host is live; fail-closed without cap.

Isolation Law: product code never imports ux_channel. This suite mints through
ux_compose.helpers.control / App.control and duck-typed Channel.control.
No Cap re-implementation.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.helpers import control
from ux_compose.doctor import scan_isolation

HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None
HAS_BEHAVIOR = importlib.util.find_spec("ux_behavior") is not None


class _FakeAttrs:
    def __init__(self, action: str, trust: dict | None = None, cap: str = "minted.cap"):
        self._map = {
            "data-channel-action": action,
            "data-channel-cap": cap,
        }
        if trust:
            self._map["data-channel-args"] = json.dumps(
                {k: str(v) for k, v in trust.items()},
                separators=(",", ":"),
            )

    def as_dict(self) -> dict[str, str]:
        return dict(self._map)


class _FakeChannel:
    """Duck-typed Channel.control / Channel.mint — no ux_channel import."""

    def __init__(self, *, cap: str = "minted.cap"):
        self.seen: list[tuple[str, dict]] = []
        self.cap = cap

    def control(self, action, trust=None, **_kw):
        payload = dict(trust or {})
        self.seen.append((str(action), payload))
        return _FakeAttrs(str(action), payload, self.cap)

    def mint(self, action, args=None, **_kw):
        payload = dict(args or {})
        self.seen.append((str(action), payload))
        return self.cap


def test_isolation_product_never_imports_ux_channel():
    src_root = ROOT / "src" / "ux_compose"
    files = [
        src_root / "helpers.py",
        src_root / "app.py",
        src_root / "component.py",
        src_root / "scaffold.py",
        src_root / "build.py",
    ]
    diags = scan_isolation(files)
    assert diags == [], diags
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("ux_channel"), path
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("ux_channel"), path


def test_control_offline_has_no_cap():
    attrs = control("hello.inc")
    assert attrs["data-ux-action"] == "hello.inc"
    assert attrs["data-channel-action"] == "hello.inc"
    assert "data-channel-cap" not in attrs


def test_control_mints_cap_when_cap_host_live():
    from ux_compose.wire.caps import register_live_channel

    ch = _FakeChannel(cap="tok.cto")
    register_live_channel(ch)
    attrs = control("hello.inc", sku="tee")
    assert attrs["data-channel-cap"] == "tok.cto"
    assert attrs["data-channel-action"] == "hello.inc"
    assert attrs["data-ux-action"] == "hello.inc"
    assert ch.seen == [("hello.inc", {"sku": "tee"})]


def test_app_control_mints_product_verb_when_cap_host_live():
    from ux_compose import App
    from ux_compose.wire.caps import register_live_channel

    ch = _FakeChannel(cap="tok.app")
    app = App.boot("Shop", strict_caps=False)
    app._channel = ch
    register_live_channel(ch)
    attrs = app.control("hello.inc")
    assert attrs["data-channel-cap"] == "tok.app"
    assert attrs["data-channel-action"] == "hello.inc"
    assert "dispatch" not in attrs["data-channel-action"]


def test_dispatch_fail_closed_without_cap_for_caps_required_action():
    """Offline strict_caps: caps-required actions refuse without Cap."""
    from ux_compose import App, Component, action, notify

    class Cart(Component):
        id = "cart"

        @action(caps=("orders.place",))
        def checkout(self):
            return [notify("placed")]

        @action(caps=())
        def add(self):
            return [notify("added")]

    app = App.boot("Shop", strict_caps=True).use_behavior()
    app.add(Cart)
    ops = app.dispatch("cart.add")
    assert ops, "public action must still dispatch"
    raised = False
    try:
        app.dispatch("cart.checkout")
    except Exception as exc:
        blob = type(exc).__name__ + " " + str(exc)
        raised = (
            "Cap" in blob
            or "Authority" in blob
            or "Permission" in blob
            or "cap" in blob.lower()
        )
    assert raised, "caps-required dispatch must fail closed without Cap"


@pytest.mark.skipif(not (HAS_CHANNEL and HAS_BEHAVIOR), reason="ux-channel + ux-behavior")
def test_intent_without_cap_fails_closed_for_caps_required_action():
    """Live Cap Host: Intent without cap is refused; minted control() cap is ok."""
    from ux_compose import App, Component, action, notify
    from ux_compose.helpers import control as live_control
    from ux_compose.wire.caps import register_live_channel

    class Cart(Component):
        id = "cart"

        @action(caps=("orders.place",))
        def checkout(self):
            return [notify("Order placed")]

    app = App.boot("Shop", strict_caps=True)
    app.add(Cart)
    app.use_channel()
    if app._channel is None:
        pytest.skip("Channel did not boot")
    register_live_channel(app._channel)

    refused = app.submit_intent("cart.checkout", args={})
    assert getattr(refused, "ok", None) is False, (
        f"Intent without cap must fail closed, got {refused!r}"
    )

    attrs = live_control("cart.checkout")
    cap = attrs.get("data-channel-cap")
    assert isinstance(cap, str) and cap.strip(), attrs
    assert attrs["data-channel-action"] == "cart.checkout"

    ok = app.submit_intent("cart.checkout", cap=cap, args={})
    assert getattr(ok, "ok", True) is True
