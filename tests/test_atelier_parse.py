"""Atelier host must parse browser FormData (multipart) as well as urlencoded."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from apps.atelier_shop.server import _parse_action_args


def test_urlencoded_sku():
    args = _parse_action_args(
        "application/x-www-form-urlencoded",
        b"sku=linen-01",
    )
    assert args == {"sku": "linen-01"}


def test_json_sku():
    args = _parse_action_args("application/json", b'{"sku":"oak-02"}')
    assert args == {"sku": "oak-02"}


def test_multipart_webkit_boundary():
    boundary = "----WebKitFormBoundaryum83Gri5Vz97DcGY"
    raw = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="sku"\r\n\r\n'
        "linen-01\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    args = _parse_action_args(
        f"multipart/form-data; boundary={boundary}",
        raw,
    )
    assert args == {"sku": "linen-01"}


def test_multipart_garbage_keys_are_dropped():
    # urlencoded parser on a multipart body yields one illegal key — must not leak.
    boundary = "----WebKitFormBoundary8QOPGpHv7M8B9Y0i"
    raw = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="sku"\r\n\r\n'
        "wool-03\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    args = _parse_action_args("application/x-www-form-urlencoded", raw)
    assert "sku" in args
    assert args["sku"] == "wool-03"
    assert all("\n" not in k and "Content-Disposition" not in k for k in args)
