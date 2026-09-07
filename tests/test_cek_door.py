"""CEK door — product default is require (cek-runtime Host via Channel).

adapt is compare-only lab. Offline-shim does not run this module.
"""
from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None
HAS_CEK = importlib.util.find_spec("cek_host") is not None

needs_channel = pytest.mark.skipif(not HAS_CHANNEL, reason="ux-channel required")


def _registry_caps(app):
    return getattr(getattr(app._channel, "registry", None), "_caps", None)


def _assert_product_cap(caps) -> None:
    assert type(caps).__name__ == "CekHostCapService"
    ssot = getattr(caps, "kernel_ssot", None)
    flag = getattr(caps, "cap_machine_is_cek_runtime", None)
    if callable(flag):
        flag = flag()
    assert ssot == "cek-runtime" or flag is True


def test_use_cek_and_attach_cek_default_mode_is_require():
    from ux_compose.app import App
    from ux_compose.wire.cek import attach_cek

    assert inspect.signature(App.use_cek).parameters["mode"].default == "require"
    assert inspect.signature(attach_cek).parameters["mode"].default == "require"


@needs_channel
def test_use_cek_off_is_noop():
    from ux_compose import App

    app = App.boot("T", strict_caps=False).use_channel().use_cek(mode="off")
    assert app._cek in (None, "off")
    caps = _registry_caps(app)
    assert caps is None or type(caps).__name__ != "CekHostCapService"


@needs_channel
def test_use_cek_adapt_is_lab_compare_only():
    """adapt = compare-only lab; Channel CapService remains authority."""
    from ux_compose import App

    app = App.boot("T", strict_caps=False).use_channel()
    before = type(_registry_caps(app)).__name__
    app.use_cek(mode="adapt")
    if HAS_CEK:
        assert app._cek == "adapt"
        caps = _registry_caps(app)
        assert type(caps).__name__ == before
        assert type(caps).__name__ != "CekHostCapService"
        lab = getattr(app._channel.registry, "_cek_caps", None)
        assert lab is not None
        _assert_product_cap(lab)
    else:
        assert app._cek in (None, "off")


@needs_channel
def test_use_cek_default_is_require_product_cap():
    from ux_compose import App

    app = App.boot("T", strict_caps=False).use_channel()
    if HAS_CEK:
        app.use_cek()
        assert app._cek == "require"
        _assert_product_cap(_registry_caps(app))
    else:
        with pytest.raises(ImportError):
            app.use_cek()


@needs_channel
def test_cek_require_raises_or_attaches():
    from ux_compose import App

    app = App.boot("T", strict_caps=False).use_channel()
    if HAS_CEK:
        app.use_cek(mode="require")
        assert app._cek == "require"
        _assert_product_cap(_registry_caps(app))
    else:
        with pytest.raises(ImportError):
            app.use_cek(mode="require")


@needs_channel
def test_unknown_cek_mode_resolves_to_require():
    from ux_compose import App

    app = App.boot("T", strict_caps=False).use_channel()
    if HAS_CEK:
        app.use_cek(mode="wat")
        assert app._cek == "require"
        _assert_product_cap(_registry_caps(app))
    else:
        with pytest.raises(ImportError):
            app.use_cek(mode="wat")


def test_cek_module_is_only_in_wire():
    from ux_compose.doctor import scan_isolation

    root = Path(__file__).resolve().parents[1] / "src" / "ux_compose"
    files = [p for p in root.rglob("*.py") if "wire" not in p.parts]
    diags = scan_isolation(files)
    assert diags == [], diags
