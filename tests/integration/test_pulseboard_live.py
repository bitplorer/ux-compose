"""Integration: Pulseboard app build + health + composed GET."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")


def test_pulseboard_build_health_and_home():
    from apps.pulseboard.app import main
    from tests.asgi_http import asgi_get, asgi_http

    ux, asgi, bundle = main()
    from apps.pulseboard.server import attach_doors

    asgi = attach_doors(asgi, ux)
    assert ux is not None
    assert bundle is not None
    if asgi is None:
        pytest.skip("FastAPI ASGI not built")

    r = asgi_get(asgi, "/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("app") == "Pulseboard"
    assert "desk_kpis" in data.get("board", [])

    r2 = asgi_get(asgi, "/")
    assert r2.status_code == 200
    assert "text/html" in r2.headers.get("content-type", "")
    assert "Pulseboard" in r2.text
    assert "desk_kpis" in r2.text
    assert "desk_kanban" in r2.text
    assert "desk_timeline" in r2.text

    r3 = asgi_get(asgi, "/pipeline")
    assert r3.status_code == 200
    assert "This week's paper" in r3.text or "Qualify" in r3.text


def test_pulseboard_kpi_action_morphs():
    from apps.pulseboard.app import main
    from apps.pulseboard.server import attach_doors
    from tests.asgi_http import asgi_http

    ux, asgi, _ = main()
    asgi = attach_doors(asgi, ux)
    if asgi is None:
        pytest.skip("no asgi")
    status, headers, body = asgi_http(
        asgi,
        "/action/desk_kpis.tick_up",
        method="POST",
        body=b"",
        headers={"hx-request": "true", "content-type": "application/x-www-form-urlencoded"},
    )
    assert status == 200
    text = body.decode("utf-8", "replace")
    assert "186" in text or "MRR" in text
