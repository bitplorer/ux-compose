"""serve-dev process split: Channel action MorphState must paint on UI GET.

Repro: origin routes Document GET to the ui worker and /ux-channel* to the
channel worker. Each used to boot its own MemoryStateStore, so Cap morph
was live while nav-tab GET re-painted defaults.

This test boots two independent Channel ASGI apps that share only
``UXCOMPOSE_STATE_STORE`` — Channel.boot opens FileStateStore — and proves
GET after action shows MorphState.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app
from ux_compose.serve.state import STATE_STORE_ENV

from tests.intent_from_control import intent_from_control

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None
HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None
HAS_BEHAVIOR = importlib.util.find_spec("ux_behavior") is not None
HAS_DOM = importlib.util.find_spec("ux_dom") is not None
HAS_CEK = importlib.util.find_spec("cek_host") is not None


def _hello_counters(html: str) -> list[int]:
    return [int(n) for n in re.findall(r"tabular-nums[^>]*>\s*(\d+)", html)]


def _load_document(root: Path, mod_name: str):
    root_s = str(root.resolve())
    sys.path.insert(0, root_s)
    try:
        path = root / "document.py"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.document
    finally:
        if sys.path and sys.path[0] == root_s:
            sys.path.pop(0)


def _build_worker(root: Path, *, name: str, cek: str = "require"):
    from ux_compose.build import build

    document = _load_document(root, f"{name}_document")
    return build(
        root,
        name=name,
        host="fastapi",
        live="auto",
        level=1,
        document=document,
        wrap=document,
        cek=cek,
    )


@pytest.mark.skipif(
    not (HAS_FASTAPI and HAS_CHANNEL and HAS_BEHAVIOR and HAS_DOM and HAS_CEK),
    reason="fastapi + specialists",
)
def test_ui_document_get_paints_channel_morphstate_via_shared_store(tmp_path, monkeypatch):
    """Action on a channel-worker ASGI + GET on a ui-worker ASGI share MorphState."""
    from ux_compose.live_client import CHANNEL_ENDPOINT
    from tests.asgi_http import asgi_get, asgi_post_json

    store = tmp_path / "serve-dev-state.sqlite"
    monkeypatch.setenv(STATE_STORE_ENV, str(store))
    monkeypatch.delenv("REDIS_URL", raising=False)

    channel_root = create_app(tmp_path / "chapp", name="chapp", level=1, host="fastapi")
    ui_root = create_app(tmp_path / "uiapp", name="uiapp", level=1, host="fastapi")

    app_ch, asgi_ch, _ = _build_worker(channel_root, name="chapp")
    if asgi_ch is None or app_ch._channel is None:
        pytest.skip("Channel did not bind ASGI")

    page = asgi_get(asgi_ch, "/hello")
    assert page.status_code == 200, page.text[:400]
    minted = intent_from_control(page.text, "hello.inc")
    assert minted["cap"].strip(), minted

    for _ in range(3):
        ok = asgi_post_json(
            asgi_ch,
            CHANNEL_ENDPOINT,
            {
                "v": "1",
                "action": minted["action"],
                "args": minted["args"],
                "cap": minted["cap"],
            },
        )
        assert ok.status_code == 200, ok.text[:500]

    channel_after = asgi_get(asgi_ch, "/hello")
    assert channel_after.status_code == 200, channel_after.text[:400]
    ch_counts = _hello_counters(channel_after.text)
    assert ch_counts, channel_after.text[:500]
    assert ch_counts[0] >= 3, ch_counts

    app_ui, asgi_ui, _ = _build_worker(ui_root, name="uiapp")
    if asgi_ui is None or app_ui._channel is None:
        pytest.skip("UI Channel did not bind ASGI")

    ui_page = asgi_get(asgi_ui, "/hello")
    assert ui_page.status_code == 200, ui_page.text[:400]
    ui_counts = _hello_counters(ui_page.text)
    assert ui_counts, ui_page.text[:500]
    assert ui_counts[0] == ch_counts[0], (
        f"UI GET painted {ui_counts} after channel action; "
        f"channel GET was {ch_counts}"
    )


@pytest.mark.skipif(
    not (HAS_FASTAPI and HAS_CHANNEL and HAS_BEHAVIOR and HAS_DOM),
    reason="fastapi + specialists",
)
def test_without_shared_store_ui_get_stays_at_default(tmp_path, monkeypatch):
    """Split workers with no shared store keep process-local MorphState."""
    monkeypatch.delenv(STATE_STORE_ENV, raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    from tests.asgi_http import asgi_get

    ch_root = create_app(tmp_path / "memch", name="memch", level=1, host="fastapi")
    ui_root = create_app(tmp_path / "memui", name="memui", level=1, host="fastapi")

    app_ch, asgi_ch, _ = _build_worker(ch_root, name="memch", cek="off")
    if asgi_ch is None or app_ch._channel is None:
        pytest.skip("Channel did not bind ASGI")

    app_ch.dispatch("hello.inc")
    app_ch.dispatch("hello.inc")
    ch_page = asgi_get(asgi_ch, "/hello")
    assert ch_page.status_code == 200
    ch_counts = _hello_counters(ch_page.text)
    assert ch_counts and ch_counts[0] == 2, ch_counts

    _app_ui, asgi_ui, _ = _build_worker(ui_root, name="memui", cek="off")
    if asgi_ui is None:
        pytest.skip("UI ASGI missing")
    ui_page = asgi_get(asgi_ui, "/hello")
    assert ui_page.status_code == 200
    ui_counts = _hello_counters(ui_page.text)
    assert ui_counts and ui_counts[0] == 0, ui_counts
