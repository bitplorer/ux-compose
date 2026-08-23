"""Integration / live: Pulse app build + health surface.

Requires fastapi for full HTTP; otherwise skips.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")


def test_pulse_build_health():
    from apps.pulse.server import build

    ux, asgi, bundle = build()
    assert ux is not None
    assert bundle is not None
    if asgi is None:
        pytest.skip("FastAPI ASGI not built")
    from fastapi.testclient import TestClient

    client = TestClient(asgi)
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("app") == "Pulse"
    assert "surfaces" in data

    r2 = client.get("/")
    assert r2.status_code == 200
    assert "text/html" in r2.headers.get("content-type", "")


def test_pulse_doctor_api():
    from apps.pulse.server import build
    from fastapi.testclient import TestClient

    _, asgi, _ = build()
    if asgi is None:
        pytest.skip("no asgi")
    client = TestClient(asgi)
    r = client.get("/api/doctor")
    assert r.status_code == 200
    body = r.json()
    assert "ok" in body
    assert "capabilities" in body
