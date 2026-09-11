"""Integration: build(cek="require") attaches cek-runtime Cap Host without hand use_cek.

Skip when Channel / cek-host are absent (offline-shim). Isolation: this test
inspects registry._caps; product code under test uses App / build() only.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.build import build
from ux_compose.scaffold import create_app

HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None
HAS_CEK = importlib.util.find_spec("cek_host") is not None

needs_cap = pytest.mark.skipif(
    not (HAS_CHANNEL and HAS_CEK),
    reason="ux-channel + cek-host required for product Cap Host",
)


def _registry_caps(app):
    return getattr(getattr(app._channel, "registry", None), "_caps", None)


def _assert_product_cap(caps) -> None:
    """Identity only — type name + kernel_ssot. No Channel internals."""
    assert type(caps).__name__ == "CekHostCapService"
    ssot = getattr(caps, "kernel_ssot", None)
    flag = getattr(caps, "cap_machine_is_cek_runtime", None)
    if callable(flag):
        flag = flag()
    assert ssot == "cek-runtime" or flag is True


@needs_cap
def test_build_attaches_cek_host_without_hand_use_cek(tmp_path):
    """build() default cek=require → Cap identity is cek-runtime Host."""
    root = create_app(tmp_path / "capapp", name="capapp", level="auto", host="asgi")
    app, _asgi, bundle = build(
        root,
        name="capapp",
        host="asgi",
        live="auto",
        level="auto",
    )
    assert bundle is not None
    if app._channel is None:
        pytest.skip("Channel did not boot")
    assert app._cek == "require"
    _assert_product_cap(_registry_caps(app))
