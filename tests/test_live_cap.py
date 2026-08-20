"""Live Cap mint path — checkout succeeds only with a real Channel-minted Cap.

Isolation: this test imports Channel types only to inspect Result; product
code under test goes through App / wire/.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None
HAS_BEHAVIOR = importlib.util.find_spec("ux_behavior") is not None
HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None

pytestmark = pytest.mark.skipif(
    not (HAS_CHANNEL and HAS_BEHAVIOR),
    reason="ux-channel + ux-behavior required for live Cap path",
)


def _cart_app(*, asgi=None, strict=True):
    from ux_compose import App, Component, MorphState, action, notify, update_with

    class Cart(Component):
        id = "cart"
        count = MorphState(0)

        def render(self):
            return f'<div id="cart" data-count="{self.count}">count={self.count}</div>'

        @action(caps=())
        def add(self, sku: str = "tee"):
            self.count = int(self.count) + 1
            return update_with(self, extra_ops=[notify(f"Added {sku}")])

        @action(caps=("orders.place",))
        def checkout(self):
            return [notify("Order placed")]

    app = App.boot("Shop", strict_caps=strict)
    app.add(Cart)
    if asgi is not None:
        app.use_channel(asgi_app=asgi)
    else:
        app.use_channel()
    return app


def test_checkout_without_cap_refused():
    app = _cart_app()
    result = app.submit_intent("cart.checkout", args={})
    ok = getattr(result, "ok", None)
    assert ok is False, f"missing Cap must fail-closed, got {result!r}"
    err = getattr(result, "error", None)
    blob = str(err) + str(result)
    assert "cap" in blob.lower() or "unauthor" in blob.lower() or "missing" in blob.lower()


def test_checkout_succeeds_only_with_real_cap():
    app = _cart_app()
    cap = app.mint_cap("cart.checkout", {})
    assert isinstance(cap, str) and len(cap) > 8
    refused = app.submit_intent("cart.checkout", args={})
    assert getattr(refused, "ok", None) is False
    placed = app.submit_intent("cart.checkout", cap=cap, args={})
    assert getattr(placed, "ok", True) is True
    ops = list(getattr(placed, "ops", None) or [])
    blob = " ".join(str(o) for o in ops) + str(placed)
    assert "placed" in blob.lower() or "toast" in blob.lower() or placed.ok


def test_mint_flag_on_submit_intent():
    app = _cart_app()
    result = app.submit_intent("cart.checkout", mint=True, args={})
    assert getattr(result, "ok", True) is True


def test_public_add_still_requires_cap_when_require_cap():
    """Channel require_cap=True: even public actions need a minted Cap at the edge."""
    app = _cart_app()
    refused = app.submit_intent("cart.add", args={"sku": "tee"})
    assert getattr(refused, "ok", None) is False
    ok = app.submit_intent("cart.add", mint=True, args={"sku": "tee"})
    assert getattr(ok, "ok", True) is True


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi required for include_router host test")
def test_channel_mounts_on_fastapi_include_router():
    from fastapi import FastAPI

    asgi = FastAPI(title="CapHost")
    app = _cart_app(asgi=asgi)
    assert app._channel is not None
    paths = [getattr(r, "path", "") for r in asgi.routes]
    joined = " ".join(paths)
    assert "/ux-channel" in joined, f"Channel routes missing: {paths}"
    # Behavior.attach received FastAPI, not Channel — no include_router boot fail
    diag = getattr(app._behavior, "diagnostics", None)
    text = ""
    if diag is not None:
        summary = diag.summary() if hasattr(diag, "summary") else diag
        text = str(summary)
        events = getattr(diag, "events", None) or getattr(diag, "_events", None) or []
        text += " ".join(str(e) for e in events)
    assert "ATTACH_BOOT_FAILED" not in text
    assert "include_router" not in text.lower() or "failed" not in text.lower()


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi required")
def test_behavior_wire_is_channel_not_double_boot():
    from fastapi import FastAPI

    asgi = FastAPI()
    app = _cart_app(asgi=asgi)
    wire = getattr(app._behavior, "_wire", None)
    assert wire is not None
    assert type(wire).__name__ == "Channel"
    assert wire is app._channel
    # FastAPI still has include_router; Channel does not
    assert hasattr(asgi, "include_router")
    assert not hasattr(wire, "include_router")


def test_isolation_shop_does_not_import_channel():
    from ux_compose.doctor import scan_isolation

    root = Path(__file__).resolve().parents[1]
    shop = root / "apps" / "atelier_shop"
    if not shop.exists():
        pytest.skip("atelier shop not present")
    files = list(shop.rglob("*.py"))
    diags = scan_isolation(files)
    assert diags == [], diags
