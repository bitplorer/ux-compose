"""L5 locks: compose→channel happy paths on existing Pulse rooms.

HTTP merge bar: httpx ASGITransport against Pulse ``build()``.
Surfaces: ``/`` home, ``/lab``, ``/shop``, ``/settings``, Clock B
``/ux-channel/action``. No new Pulse room.

Isolation: this suite never imports ``ux_channel`` in product code under
test. Channel types are inspected only through compose / HTTP evidence.
"""
from __future__ import annotations

import asyncio
import ast
from pathlib import Path

import httpx
import pytest

from ux_compose import bind, optional_fade, optional_plan, optional_slide, update_with
from ux_compose.doctor import scan_isolation
from ux_compose.helpers import _fragment_for_target, _owner_extract_by_id
from ux_compose.live_client import CHANNEL_ENDPOINT
from tests.intent_from_control import intent_from_control

ROOT = Path(__file__).resolve().parents[2]
PULSE = ROOT / "apps" / "pulse"
SRC = ROOT / "src" / "ux_compose"

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("ux_dom")
pytest.importorskip("ux_behavior")
pytest.importorskip("ux_channel")
pytest.importorskip("ux_motion")


def _httpx(asgi, method: str, path: str, **kwargs) -> httpx.Response:
    """httpx TestClient-style request against Pulse ASGI."""

    async def _go():
        transport = httpx.ASGITransport(app=asgi)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://pulse.test"
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_go())


@pytest.fixture(scope="module")
def pulse_app():
    from apps.pulse.server import build

    ux, asgi, bundle = build()
    if asgi is None:
        pytest.skip("FastAPI ASGI not built")
    return ux, asgi, bundle


@pytest.fixture
def pulse(pulse_app):
    """Re-register after tests/conftest.py autouse clears the live Channel."""
    from ux_compose.wire.caps import register_live_channel

    ux, asgi, bundle = pulse_app
    register_live_channel(ux._channel)
    return ux, asgi, bundle


# --- 1. ux-dom -------------------------------------------------------------


def test_matrix_1_dom_build_document_html(pulse):
    """GET existing Pulse rooms are Document-path HTML from build(document=)."""
    ux, asgi, bundle = pulse
    assert bundle is not None
    assert ux._document is not None

    for path, eid in (
        ("/", "home"),
        ("/lab", "lab"),
        ("/shop", "shop"),
        ("/settings", "settings"),
    ):
        page = _httpx(asgi, "GET", path)
        assert page.status_code == 200, (path, page.text[:400])
        assert "text/html" in page.headers.get("content-type", "")
        assert "<html" in page.text.lower()
        assert f'id="{eid}"' in page.text
        assert "data-uxcompose-get-chrome" in page.text


def test_matrix_1_dom_extract_by_id_fragment_path(pulse):
    """Compose helpers prefer ux-dom extract_by_id; fragment has no GET chrome."""
    _, asgi, _ = pulse
    owner = _owner_extract_by_id()
    assert owner is not None, "ux-dom extract_by_id must be importable on this pin"

    page = _httpx(asgi, "GET", "/lab")
    assert page.status_code == 200
    via_owner = owner(page.text, "lab")
    via_helper = _fragment_for_target(page.text, "lab")
    assert via_owner == via_helper
    assert 'id="lab"' in via_helper
    assert "<html" not in via_helper.lower()
    assert "data-uxcompose-get-chrome" not in via_helper
    assert "<title" not in via_helper.lower()


# --- 2. ux-channel ---------------------------------------------------------


def test_matrix_2_channel_boot_and_mount_http(pulse):
    """Channel.boot via wire/ + mount_channel HTTP door on Pulse ASGI."""
    ux, asgi, _ = pulse
    wire = getattr(getattr(ux, "_behavior", None), "_wire", None)
    assert wire is not None
    assert type(wire).__name__ == "Channel"
    assert wire is ux._channel

    paths = [getattr(r, "path", "") for r in asgi.routes]
    joined = " ".join(paths)
    assert "/ux-channel" in joined, f"mount_channel routes missing: {paths}"

    health = _httpx(asgi, "GET", "/ux-channel/health")
    assert health.status_code == 200, health.text[:400]
    body = health.json()
    formats = body.get("formats") or []
    assert any("json" in str(item).lower() for item in formats), body


def test_matrix_2_channel_cap_path_http(pulse):
    """POST /ux-channel/action: minted home.beat cap is 200; missing cap is 401."""
    _, asgi, _ = pulse
    page = _httpx(asgi, "GET", "/")
    minted = intent_from_control(page.text, "home.beat")
    assert minted["cap"].strip(), minted

    refused = _httpx(
        asgi,
        "POST",
        CHANNEL_ENDPOINT,
        json={"v": "1", "action": "home.beat", "args": {}, "cap": None},
        headers={"x-channel": "1"},
    )
    assert refused.status_code == 401, refused.text[:500]
    blob = refused.text.lower()
    assert "unauthor" in blob or "cap" in blob or "missing" in blob

    ok = _httpx(
        asgi,
        "POST",
        CHANNEL_ENDPOINT,
        json={
            "v": "1",
            "action": minted["action"],
            "args": minted["args"],
            "cap": minted["cap"],
        },
        headers={"x-channel": "1"},
    )
    assert ok.status_code == 200, ok.text[:500]
    body = ok.json()
    assert body.get("ok") is True or bool(body.get("ops"))


# --- 3. ux-behavior --------------------------------------------------------


def test_matrix_3_bind_action_verified_ops(pulse):
    """Existing Lab @action: GET control attrs; bind() + dispatch → real Ops."""
    ux, asgi, _ = pulse
    page = _httpx(asgi, "GET", "/lab")
    assert page.status_code == 200
    assert 'data-channel-action="lab.inc"' in page.text
    assert 'data-ux-action="lab.inc"' in page.text
    assert "data-channel-cap" in page.text

    lab = ux._behavior.get("lab")
    attrs = bind(lab.inc)
    assert attrs.get("data-channel-action") == "lab.inc"
    assert attrs.get("data-ux-action") == "lab.inc"
    assert str(attrs.get("data-channel-cap") or "").strip()

    ops = ux.dispatch("lab.inc")
    assert isinstance(ops, list) and ops
    first = ops[0]
    assert getattr(first, "ns", None) == "ui.dom"
    assert getattr(first, "name", None) == "morph"
    payload = getattr(first, "payload", {}) or {}
    html = str(payload.get("patch") or payload.get("html") or "")
    assert 'id="lab"' in html
    assert "<html" not in html.lower()


def test_matrix_3_behavior_attach_owns_channel_boot(pulse):
    """Behavior.attach(asgi) owns Channel.boot — wire is Channel, not a remount."""
    ux, asgi, _ = pulse
    behavior = ux._behavior
    assert behavior is not None
    assert getattr(behavior, "_wire", None) is ux._channel
    assert hasattr(asgi, "include_router")
    assert not hasattr(ux._channel, "include_router")


# --- 4. ux-motion ----------------------------------------------------------


def _ops_blob(ops) -> str:
    return " ".join(str(o) for o in (ops or []))


def test_matrix_4_morph_then_motion_after_result(pulse):
    """Order law on Pulse Lab via helpers; HTTP home.beat Result is morph-first."""
    ux, asgi, _ = pulse
    lab = ux._behavior.get("lab")
    for plan, token in (
        (optional_fade("pulse-lab-fade", "#lab"), "fade"),
        (optional_plan("pulse-lab-rise", "#lab"), "rise"),
        (optional_slide("pulse-lab-slide", "#lab"), "slide"),
    ):
        ops = update_with(lab, plan)
        assert isinstance(ops, list) and len(ops) >= 2
        first = ops[0]
        assert getattr(first, "ns", None) == "ui.dom"
        assert getattr(first, "name", None) == "morph"
        play = [
            o
            for o in ops[1:]
            if getattr(o, "ns", "") == "transition" and getattr(o, "name", "") == "play"
        ]
        assert play, f"must append transition.play after morph: {ops!r}"
        blob = _ops_blob(play).lower()
        assert token in blob or "enter" in blob, blob
        for o in play:
            plan_payload = (getattr(o, "payload", None) or {}).get("plan")
            assert "html" not in str(plan_payload).lower() or '"html"' not in str(
                plan_payload
            )

    page = _httpx(asgi, "GET", "/")
    minted = intent_from_control(page.text, "home.beat")
    result = _httpx(
        asgi,
        "POST",
        CHANNEL_ENDPOINT,
        json={
            "v": "1",
            "action": minted["action"],
            "args": minted["args"],
            "cap": minted["cap"],
        },
        headers={"x-channel": "1"},
    )
    assert result.status_code == 200, result.text[:500]
    body = result.json()
    ops = body.get("ops") or []
    assert ops, body
    first_name = str(ops[0].get("op") or ops[0].get("name") or "")
    assert "morph" in first_name or ops[0].get("ns") == "ui.dom"


def _imports_ux_channel(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.startswith("ux_channel") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").startswith("ux_channel"):
                return True
    return False


def test_matrix_4_channel_never_learns_transition_star():
    """Pulse + compose product never import ux_channel; Pulse does not emit transition.*."""
    pulse_py = list(PULSE.rglob("*.py"))
    assert pulse_py
    for path in pulse_py:
        assert not _imports_ux_channel(path), path
        src = path.read_text(encoding="utf-8")
        assert "transition.play" not in src
        assert "transition.*" not in src
    wire = SRC / "wire"
    for path in SRC.rglob("*.py"):
        if wire in path.parents or path.parent == wire:
            continue
        assert not _imports_ux_channel(path), path


# --- 5. Isolation ----------------------------------------------------------


def test_matrix_5_isolation_no_ux_channel_outside_wire():
    pulse_files = list(PULSE.rglob("*.py"))
    assert pulse_files
    assert scan_isolation(pulse_files) == []

    compose_files = [p for p in SRC.rglob("*.py") if "wire" not in p.parts]
    diags = scan_isolation(compose_files)
    assert diags == [], diags
    for path in compose_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("ux_channel"), path
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("ux_channel"), path


# --- 6. Fail-closed --------------------------------------------------------


def test_matrix_6_cap_deny_fail_closed(pulse):
    """Cap-gated shop.checkout without cap is 401; minted cap is 200."""
    ux, asgi, _ = pulse
    from ux_compose.helpers import control as live_control

    denied = _httpx(
        asgi,
        "POST",
        CHANNEL_ENDPOINT,
        json={"v": "1", "action": "shop.checkout", "args": {}, "cap": None},
        headers={"x-channel": "1"},
    )
    assert denied.status_code == 401, denied.text[:500]

    minted = live_control("shop.checkout")
    cap = str(minted.get("data-channel-cap") or "").strip()
    assert cap, minted
    ok = _httpx(
        asgi,
        "POST",
        CHANNEL_ENDPOINT,
        json={"v": "1", "action": "shop.checkout", "args": {}, "cap": cap},
        headers={"x-channel": "1"},
    )
    assert ok.status_code == 200, ok.text[:500]


def test_matrix_6_empty_content_type_fail_closed(pulse):
    """Cut C: empty Content-Type on HTTP /action is bad_request (channel lock)."""
    _, asgi, _ = pulse
    r = _httpx(
        asgi,
        "POST",
        CHANNEL_ENDPOINT,
        content=b'{"v":"1","action":"home.beat","args":{},"cap":null}',
        headers={"x-channel": "1", "content-type": ""},
    )
    assert r.status_code == 400, r.text[:500]
    blob = r.text.lower()
    assert "bad_request" in blob or "content-type" in blob
