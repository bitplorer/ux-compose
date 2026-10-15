"""Owner decisions that were previously left open."""
from __future__ import annotations

import logging
import sqlite3
import warnings
from pathlib import Path

import pytest

from ux_compose.helpers import morph_play
from ux_compose.routing.asgi import DirectoryASGI
from ux_compose.routing.core import (
    DirectoryRoutes,
    RouteRecord,
    apply_html_document,
)


def test_morph_play_without_component_warns_that_it_clears_the_node():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        ops = morph_play("box", {"v": "1"})
    assert ops[0].payload["patch"] == ""
    assert any(
        issubclass(item.category, DeprecationWarning) and "clears the node" in str(item.message)
        for item in caught
    )


def test_morph_play_component_renders_that_fragment():
    class Box:
        def render(self):
            return "<html><body><div id='box'>n=3</div></body></html>"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        ops = morph_play("box", {"v": "1"}, component=Box())
    patch = ops[0].payload["patch"]
    assert "n=3" in patch
    assert "<html>" not in patch
    assert not any(issubclass(item.category, DeprecationWarning) for item in caught)


def test_stream_error_after_first_byte_is_logged_and_not_sent(tmp_path: Path, caplog):
    from tests.asgi_http import asgi_http

    class StreamPage:
        def render(self):
            def gen():
                yield "<div>a</div>"
                raise RuntimeError("boom-mid-stream")

            return gen()

    core = DirectoryRoutes(tmp_path)
    core.records = [
        RouteRecord(
            method="GET",
            path="/g",
            name="StreamPage",
            page_cls=StreamPage,
            kind="page",
        )
    ]
    with caplog.at_level(logging.ERROR):
        status, _headers, body = asgi_http(DirectoryASGI(core), "/g")
    assert status == 200
    assert b"<div>a</div>" in body
    assert b"Error:" not in body
    assert b"boom-mid-stream" not in body
    assert "boom-mid-stream" in caplog.text


def test_apply_html_document_logs_and_keeps_the_fragment(caplog):
    def shell(child=None):
        raise RuntimeError("shell-broke")

    fragment = "<script>alert(1)</script>"
    with caplog.at_level(logging.ERROR):
        out = apply_html_document(shell, fragment)
    assert out == fragment
    assert "shell-broke" in caplog.text


def test_restart_channel_times_out_without_a_clear_result(tmp_path: Path, monkeypatch):
    from ux_compose.cli import serve_restart as mod

    mod.pid_path(str(tmp_path)).write_text("4242", encoding="utf-8")
    mod.clear_result_path(str(tmp_path)).write_text("ok\n", encoding="utf-8")

    def fake_kill(pid, sig):
        if sig == 0:
            return None
        return None

    monkeypatch.setattr(mod.os, "kill", fake_kill)
    assert mod.restart_channel(cwd=str(tmp_path), timeout=0.2) == 1


def test_restart_channel_returns_nonzero_when_clear_fails(tmp_path: Path, monkeypatch):
    from ux_compose.cli import serve_restart as mod

    mod.pid_path(str(tmp_path)).write_text("4242", encoding="utf-8")

    def fake_kill(pid, sig):
        if sig == 0:
            return None
        mod.write_clear_result(str(tmp_path), False)
        return None

    monkeypatch.setattr(mod.os, "kill", fake_kill)
    assert mod.restart_channel(cwd=str(tmp_path), timeout=1.0) == 1


def test_restart_channel_returns_zero_only_after_clear_ok(tmp_path: Path, monkeypatch):
    from ux_compose.cli import serve_restart as mod

    mod.pid_path(str(tmp_path)).write_text("4242", encoding="utf-8")

    def fake_kill(pid, sig):
        if sig == 0:
            return None
        mod.write_clear_result(str(tmp_path), True)
        return None

    monkeypatch.setattr(mod.os, "kill", fake_kill)
    assert mod.restart_channel(cwd=str(tmp_path), timeout=1.0) == 0


def test_origin_records_sqlite_clear_failure(tmp_path: Path, monkeypatch):
    from ux_compose.cli.serve_dev import note_shared_clear
    from ux_compose.cli.serve_restart import read_clear_result
    from ux_compose.cli.serve_state import STATE_STORE_ENV

    path = tmp_path / "empty.sqlite"
    sqlite3.connect(path).close()
    monkeypatch.setenv(STATE_STORE_ENV, str(path))
    assert note_shared_clear(str(tmp_path)) is False
    assert read_clear_result(str(tmp_path)) == "fail"
