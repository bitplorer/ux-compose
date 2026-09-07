"""helpers.control/bind mint Caps when Cap Host is live; offline stays dual-attr.

Isolation: product/helpers never import ux_channel. Mint is duck-typed
Channel.control / Channel.mint behind ux_compose.wire.caps.
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

from ux_compose.helpers import bind, control
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

    def __init__(self, *, cap: str = "minted.cap", underscore: bool = False):
        self.seen: list[tuple[str, dict]] = []
        self.cap = cap
        self.underscore = underscore

    def control(self, action, trust=None, **_kw):
        payload = dict(trust or {})
        self.seen.append((str(action), payload))
        attrs = _FakeAttrs(str(action), payload, self.cap)
        if self.underscore:
            return type(
                "UnderscoreAttrs",
                (),
                {
                    "as_dict": lambda _self=attrs: {
                        k.replace("-", "_"): v for k, v in attrs.as_dict().items()
                    }
                },
            )()
        return attrs

    def mint(self, action, args=None, **_kw):
        payload = dict(args or {})
        self.seen.append((str(action), payload))
        return self.cap


class _MintOnlyChannel:
    def __init__(self, cap: str = "mint-only.cap"):
        self.cap = cap
        self.seen: list[tuple[str, dict]] = []

    def mint(self, action, args=None, **_kw):
        payload = dict(args or {})
        self.seen.append((str(action), payload))
        return self.cap


@pytest.fixture
def _restore_live_channel():
    try:
        from ux_compose.wire.caps import live_channel, register_live_channel
    except ImportError:
        yield
        return
    prev = live_channel()
    register_live_channel(None)
    try:
        yield
    finally:
        register_live_channel(prev)


def test_helpers_control_offline_unchanged(_restore_live_channel):
    attrs = control("hello.inc", sku="tee")
    assert attrs["data-ux-action"] == "hello.inc"
    assert attrs["data-channel-action"] == "hello.inc"
    assert attrs["data-ux-arg-sku"] == "tee"
    assert "tee" in attrs["data-channel-args"]
    assert "data-channel-cap" not in attrs


def test_helpers_bind_offline_unchanged(_restore_live_channel):
    attrs = bind("cart.add", sku="oak")
    assert attrs["data-ux-action"] == "cart.add"
    assert attrs["data-channel-action"] == "cart.add"
    assert attrs["data-ux-arg-sku"] == "oak"
    assert "data-channel-cap" not in attrs


def test_helpers_control_emits_cap_when_channel_live(_restore_live_channel):
    from ux_compose.wire.caps import register_live_channel

    ch = _FakeChannel(cap="tok.hello")
    register_live_channel(ch)
    attrs = control("hello.inc", sku="tee")
    assert attrs["data-ux-action"] == "hello.inc"
    assert attrs["data-channel-action"] == "hello.inc"
    assert attrs["data-channel-cap"] == "tok.hello"
    assert attrs["data-ux-arg-sku"] == "tee"
    assert ch.seen == [("hello.inc", {"sku": "tee"})]


def test_helpers_control_normalizes_underscore_keys(_restore_live_channel):
    from ux_compose.wire.caps import register_live_channel

    ch = _FakeChannel(cap="tok.hyphen", underscore=True)
    register_live_channel(ch)
    attrs = control("hello.inc")
    assert "data-channel-cap" in attrs
    assert "data_channel_cap" not in attrs
    assert attrs["data-channel-cap"] == "tok.hyphen"


def test_helpers_control_falls_back_to_mint(_restore_live_channel):
    from ux_compose.wire.caps import register_live_channel

    ch = _MintOnlyChannel(cap="tok.mint")
    register_live_channel(ch)
    attrs = control("hello.inc", n="1")
    assert attrs["data-channel-cap"] == "tok.mint"
    assert attrs["data-channel-action"] == "hello.inc"
    assert attrs["data-ux-action"] == "hello.inc"
    assert attrs["data-ux-arg-n"] == "1"


def test_helpers_bind_enriches_when_channel_live(_restore_live_channel):
    from ux_compose.wire.caps import register_live_channel

    ch = _FakeChannel(cap="tok.bind")
    register_live_channel(ch)
    attrs = bind("cart.add", sku="oak")
    assert attrs["data-channel-cap"] == "tok.bind"
    assert attrs["data-ux-action"] == "cart.add"
    assert attrs["data-channel-action"] == "cart.add"


@pytest.mark.skipif(not HAS_BEHAVIOR, reason="ux-behavior")
def test_bind_action_method_enriches_when_channel_live(_restore_live_channel):
    """ux_behavior.bind must not win without Cap when Cap Host is live."""
    from ux_compose import Component, action
    from ux_compose.wire.caps import register_live_channel

    class Hello(Component):
        id = "hello"

        @action(caps=())
        def inc(self):
            return []

    ch = _FakeChannel(cap="tok.method")
    register_live_channel(ch)
    attrs = bind(Hello().inc)
    assert attrs["data-channel-cap"] == "tok.method"
    assert attrs["data-ux-action"] == "hello.inc"
    assert attrs["data-channel-action"] == "hello.inc"


def test_app_control_mints_product_verb_not_dispatch_remap(_restore_live_channel):
    from ux_compose import App
    from ux_compose.wire.caps import register_live_channel

    ch = _FakeChannel(cap="tok.app")
    app = App.boot("Shop", strict_caps=False)
    app._channel = ch
    register_live_channel(ch)
    attrs = app.control("hello.inc", sku="tee")
    assert attrs["data-channel-action"] == "hello.inc"
    assert attrs["data-ux-action"] == "hello.inc"
    assert attrs["data-channel-cap"] == "tok.app"
    assert ch.seen == [("hello.inc", {"sku": "tee"})]
    for action, _trust in ch.seen:
        assert action != "ux_behavior.dispatch"
        assert "dispatch" not in action


def test_use_channel_registers_live_channel_for_helpers(_restore_live_channel):
    from ux_compose import App
    from ux_compose.wire.caps import live_channel

    app = App.boot("Shop", strict_caps=False)
    if not HAS_CHANNEL:
        ch = _FakeChannel(cap="tok.reg")
        app._channel = ch
        from ux_compose.wire.caps import register_live_channel

        register_live_channel(ch)
    else:
        app.use_channel()
        if app._channel is None:
            pytest.skip("Channel did not boot")
    assert live_channel() is app._channel


def test_component_control_mints_via_helpers(_restore_live_channel):
    from ux_compose import Component
    from ux_compose.wire.caps import register_live_channel

    ch = _FakeChannel(cap="tok.comp")
    register_live_channel(ch)
    comp = Component()
    attrs = comp.control("hello.inc")
    assert attrs["data-channel-cap"] == "tok.comp"
    assert attrs["data-channel-action"] == "hello.inc"


def test_isolation_helpers_and_app_never_import_ux_channel():
    src_root = ROOT / "src" / "ux_compose"
    files = [
        src_root / "helpers.py",
        src_root / "app.py",
        src_root / "component.py",
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


@pytest.mark.skipif(not (HAS_CHANNEL and HAS_BEHAVIOR), reason="ux-channel + ux-behavior")
def test_intent_without_cap_fails_minted_cap_from_control_ok(_restore_live_channel):
    from ux_compose import App, Component, MorphState, action, update_with
    from ux_compose.helpers import control as live_control
    from ux_compose.wire.caps import register_live_channel

    class Hello(Component):
        id = "hello"
        n = MorphState(0)

        @action(caps=())
        def inc(self):
            self.n = int(self.n or 0) + 1
            return update_with(self)

    app = App.boot("Demo", strict_caps=False)
    app.add(Hello)
    app.use_channel()
    if app._channel is None:
        pytest.skip("Channel did not boot")
    register_live_channel(app._channel)

    refused = app.submit_intent("hello.inc", args={})
    assert getattr(refused, "ok", None) is False

    attrs = live_control("hello.inc")
    cap = attrs.get("data-channel-cap")
    assert isinstance(cap, str) and len(cap) > 8
    assert attrs["data-channel-action"] == "hello.inc"

    ok = app.submit_intent("hello.inc", cap=cap, args={})
    assert getattr(ok, "ok", True) is True

    app_attrs = app.control("hello.inc")
    assert app_attrs["data-channel-action"] == "hello.inc"
    assert app_attrs.get("data-channel-cap")
    assert "dispatch" not in app_attrs["data-channel-action"]
