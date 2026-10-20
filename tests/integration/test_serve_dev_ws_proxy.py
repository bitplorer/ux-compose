"""Integration: the serve dev origin forwards a WebSocket close both ways.

A fake upstream stands in for the ui / channel worker. The origin is the
real ``make_origin_asgi`` under uvicorn. A close on one side must reach
the other side with its code and reason, within 2 s.
"""
from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

uvicorn = pytest.importorskip("uvicorn")
pytest.importorskip("websockets")
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect
from websockets.sync.server import serve

from ux_compose.cli.serve_dev import make_origin_asgi


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def upstream():
    """Fake worker. ``handler`` is set by each test."""
    state: dict = {"handler": None, "closed": threading.Event()}

    def handle(conn):
        state["handler"](conn, state)

    server = serve(handle, "127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield state, server.socket.getsockname()[1]
    finally:
        server.shutdown()


@pytest.fixture
def origin(upstream):
    state, up_port = upstream
    url = f"http://127.0.0.1:{up_port}"
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            make_origin_asgi(ui_url=url, channel_url=url),
            host="127.0.0.1",
            port=port,
            lifespan="off",
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started
    try:
        yield state, port
    finally:
        server.should_exit = True
        thread.join(5)


def test_worker_close_reaches_client_with_code_and_reason(origin):
    state, port = origin

    def handler(conn, state):
        conn.send("hello")
        conn.close(1012, "ui reload")

    state["handler"] = handler
    with connect(f"ws://127.0.0.1:{port}/__uxcompose/hmr", open_timeout=5) as ws:
        assert ws.recv(timeout=2) == "hello"
        t0 = time.monotonic()
        with pytest.raises(ConnectionClosed) as info:
            ws.recv(timeout=2)
        assert time.monotonic() - t0 < 2
    assert info.value.rcvd is not None
    assert (info.value.rcvd.code, info.value.rcvd.reason) == (1012, "ui reload")


def test_client_close_reaches_worker_with_code_and_reason(origin):
    state, port = origin
    seen: dict = {}

    def handler(conn, state):
        try:
            for _ in conn:
                pass
        except ConnectionClosed:
            pass
        seen["code"], seen["reason"] = conn.close_code, conn.close_reason
        state["closed"].set()

    state["handler"] = handler
    ws = connect(f"ws://127.0.0.1:{port}/ux-channel/ws", open_timeout=5)
    ws.send("ping")
    time.sleep(0.2)
    ws.close(4001, "tab closed")
    assert state["closed"].wait(2), "upstream never saw the close"
    assert (seen["code"], seen["reason"]) == (4001, "tab closed")
