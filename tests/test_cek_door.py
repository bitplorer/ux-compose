"""Optional CEK door — Isolation-safe, degrades when cek_host is absent."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None
HAS_CEK = importlib.util.find_spec("cek_host") is not None

pytestmark = pytest.mark.skipif(not HAS_CHANNEL, reason="ux-channel required")


def test_use_cek_off_is_noop():
    from ux_compose import App

    app = App.boot("T", strict_caps=False).use_channel().use_cek(mode="off")
    assert app._cek in (None, "off")


def test_use_cek_adapt_degrades_without_cek_host():
    from ux_compose import App

    app = App.boot("T", strict_caps=False).use_channel().use_cek(mode="adapt")
    if HAS_CEK:
        assert app._cek in ("adapt", "require")
    else:
        assert app._cek in (None, "off")


def test_cek_require_raises_or_attaches():
    from ux_compose import App

    app = App.boot("T", strict_caps=False).use_channel()
    if HAS_CEK:
        app.use_cek(mode="require")
        assert app._cek == "require"
    else:
        with pytest.raises(ImportError):
            app.use_cek(mode="require")


def test_cek_module_is_only_in_wire():
    from ux_compose.doctor import scan_isolation

    root = Path(__file__).resolve().parents[1] / "src" / "ux_compose"
    files = [p for p in root.rglob("*.py") if "wire" not in p.parts]
    diags = scan_isolation(files)
    assert diags == [], diags
