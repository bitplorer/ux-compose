"""Security / pen-style: Isolation Law + input cleaning patterns."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def test_cold_import_does_not_require_channel():
    # Importing package must not force ux_channel
    import importlib

    mod = importlib.import_module("ux_compose")
    assert hasattr(mod, "App")


def test_pulse_clean_args_rejects_bad_keys():
    sys.path.insert(0, str(ROOT))
    from apps.pulse.server import _clean_args

    dirty = {
        "action": "evil",
        "submit": "1",
        "ok_sku": "tee",
        "../path": "no",
        "a;drop": "no",
        "qty": "2",
    }
    clean = _clean_args(dirty)
    assert "action" not in clean
    assert "submit" not in clean
    assert "../path" not in clean
    assert "a;drop" not in clean
    assert clean.get("ok_sku") == "tee"
    assert clean.get("qty") == "2"


def test_hmr_path_not_open_redirect():
    from ux_compose.hmr import HMR_PATH

    assert HMR_PATH.startswith("/")
    assert "://" not in HMR_PATH
