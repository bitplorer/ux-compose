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
from ux_compose.scaffold import ROUTES_HELLO_PY, create_app

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


def _load_scaffold_hello(root: Path):
    path = root / "routes" / "hello.py"
    spec = importlib.util.spec_from_file_location("cto_hello_pulse", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _hello_html(mod, *, force_html: bool = False) -> str:
    if force_html:
        mod.HAS_DOM = False
    tree = mod.Hello().render()
    if not isinstance(tree, str):
        from ux_compose.helpers import _serialize_tree

        return _serialize_tree(tree)
    return tree


def _refused_unauthorized(result) -> bool:
    blob = (
        str(getattr(result, "error", None) or "")
        + " "
        + str(getattr(result, "reason", None) or "")
        + " "
        + str(result)
    ).lower()
    return (
        getattr(result, "ok", None) is False
        and (
            "unauthor" in blob
            or "cap" in blob
            or "authority" in blob
            or "permission" in blob
        )
    )


def test_scaffold_hello_source_has_pulse_cap_control():
    """create-app hello teaches gated pulse without importing ux_channel."""
    src = ROUTES_HELLO_PY
    assert "pulses = MorphState" in src
    assert '@action(caps=("pulse",))' in src
    assert 'control("hello.pulse")' in src
    assert "import ux_channel" not in src
    assert "from ux_channel" not in src


def test_scaffold_hello_render_mints_pulse_cap_attrs(tmp_path):
    """Cap mint attrs present for hello.pulse on both render paths."""
    from ux_compose.wire.caps import register_live_channel

    root = create_app(tmp_path / "mint", name="mint", level=1, host="asgi")
    mod = _load_scaffold_hello(root)
    ch = _FakeChannel(cap="tok.pulse.mint")
    register_live_channel(ch)
    try:
        live = _hello_html(mod)
        html = _hello_html(mod, force_html=True)
    finally:
        register_live_channel(None)
    for blob in (live, html):
        assert 'data-channel-action="hello.pulse"' in blob
        assert 'data-ux-action="hello.pulse"' in blob
        assert "data-channel-cap" in blob
        assert "tok.pulse.mint" in blob


def test_scaffold_hello_pulse_dispatch_fail_closed_without_cap(tmp_path):
    """Offline strict_caps: hello.pulse refuses; public hello.inc still dispatches."""
    from ux_compose import App

    root = create_app(tmp_path / "strict", name="strict", level=1, host="asgi")
    mod = _load_scaffold_hello(root)
    app = App.boot("HelloPulse", strict_caps=True).use_behavior()
    app.add(mod.Hello)
    ops = app.dispatch("hello.inc")
    assert ops, "public hello.inc must still dispatch"
    raised = False
    try:
        app.dispatch("hello.pulse")
    except Exception as exc:
        blob = type(exc).__name__ + " " + str(exc)
        raised = (
            "Cap" in blob
            or "Authority" in blob
            or "Permission" in blob
            or "cap" in blob.lower()
        )
    assert raised, "hello.pulse dispatch must fail closed without Cap"


@pytest.mark.skipif(not (HAS_CHANNEL and HAS_BEHAVIOR), reason="ux-channel + ux-behavior")
def test_scaffold_hello_pulse_intent_without_cap_unauthorized_mint_ok(tmp_path):
    """Live Cap Host: hello.pulse Intent without cap is unauthorized; minted cap is ok."""
    from ux_compose import App
    from ux_compose.helpers import control as live_control
    from ux_compose.wire.caps import register_live_channel

    root = create_app(tmp_path / "live", name="live", level=1, host="asgi")
    mod = _load_scaffold_hello(root)
    app = App.boot("HelloPulse", strict_caps=True)
    app.add(mod.Hello)
    app.use_channel()
    if app._channel is None:
        pytest.skip("Channel did not boot")
    register_live_channel(app._channel)

    refused = app.submit_intent("hello.pulse", args={})
    assert _refused_unauthorized(refused), (
        f"Intent without cap must be unauthorized, got {refused!r}"
    )

    attrs = live_control("hello.pulse")
    cap = attrs.get("data-channel-cap")
    assert isinstance(cap, str) and cap.strip(), attrs
    assert attrs["data-channel-action"] == "hello.pulse"
    assert attrs["data-ux-action"] == "hello.pulse"

    ok = app.submit_intent("hello.pulse", cap=cap, args={})
    assert getattr(ok, "ok", True) is True
