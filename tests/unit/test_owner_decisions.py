"""Owner decisions that were previously left open."""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
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


def test_morph_play_requires_component():
    """0.2.0: no deprecated empty-patch path; component is required."""
    with pytest.raises(TypeError, match="component"):
        morph_play("box", {"v": "1"})


def test_morph_play_explicit_none_component_raises():
    """component=None would morph an empty patch and clear the node."""
    with pytest.raises(TypeError, match="requires a component"):
        morph_play("box", {"v": "1"}, component=None)


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
    assert body == b"<div>\n  a\n</div>"
    assert b"Error:" not in body
    assert b"boom-mid-stream" not in body
    assert "boom-mid-stream" in caplog.text


def test_apply_html_document_logs_and_keeps_the_fragment(caplog):
    def shell(child=None):
        raise RuntimeError("shell-broke")

    fragment = "<script>alert(1)</script>"
    with caplog.at_level(logging.ERROR):
        out = apply_html_document(shell, fragment)
    assert str(out) == ""
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
        token = mod.read_restart_request(str(tmp_path))
        mod.write_clear_result(str(tmp_path), False, token)
        return None

    monkeypatch.setattr(mod.os, "kill", fake_kill)
    assert mod.restart_channel(cwd=str(tmp_path), timeout=1.0) == 1


def test_restart_channel_returns_zero_only_after_clear_ok(tmp_path: Path, monkeypatch):
    from ux_compose.cli import serve_restart as mod

    mod.pid_path(str(tmp_path)).write_text("4242", encoding="utf-8")

    def fake_kill(pid, sig):
        if sig == 0:
            return None
        token = mod.read_restart_request(str(tmp_path))
        mod.write_clear_result(str(tmp_path), True, token)
        return None

    monkeypatch.setattr(mod.os, "kill", fake_kill)
    assert mod.restart_channel(cwd=str(tmp_path), timeout=1.0) == 0


def test_restart_channel_ignores_a_late_write_for_another_token(tmp_path: Path, monkeypatch):
    from ux_compose.cli import serve_restart as mod

    mod.pid_path(str(tmp_path)).write_text("4242", encoding="utf-8")

    def fake_kill(pid, sig):
        if sig == 0:
            return None

        def late():
            time.sleep(0.05)
            mod.clear_result_path(str(tmp_path)).write_text("ok\n", encoding="utf-8")
            time.sleep(0.05)
            mod.clear_result_path(str(tmp_path)).write_text(
                f"{'ab' * 16} ok\n", encoding="utf-8"
            )

        threading.Thread(target=late, daemon=True).start()
        return None

    monkeypatch.setattr(mod.os, "kill", fake_kill)
    assert mod.restart_channel(cwd=str(tmp_path), timeout=0.35) == 1


def test_restart_channel_accepts_its_token_after_a_foreign_write(tmp_path: Path, monkeypatch):
    from ux_compose.cli import serve_restart as mod

    mod.pid_path(str(tmp_path)).write_text("4242", encoding="utf-8")
    seen: list[str] = []

    def fake_kill(pid, sig):
        if sig == 0:
            return None

        def late():
            time.sleep(0.05)
            mod.write_clear_result(str(tmp_path), True, "ab" * 16)
            time.sleep(0.05)
            token = mod.read_restart_request(str(tmp_path))
            seen.append(token)
            mod.write_clear_result(str(tmp_path), True, token)

        threading.Thread(target=late, daemon=True).start()
        return None

    monkeypatch.setattr(mod.os, "kill", fake_kill)
    assert mod.restart_channel(cwd=str(tmp_path), timeout=1.0) == 0
    assert seen and seen[0] and seen[0] != "ab" * 16


def test_clear_result_writes_use_a_distinct_tmp_name(tmp_path: Path, monkeypatch):
    from ux_compose.cli import serve_restart as mod

    arrived = threading.Condition()
    release = threading.Event()
    names: list[str] = []
    errors: list[BaseException] = []
    real_replace = mod.os.replace

    def blocking_replace(src, dst):
        with arrived:
            names.append(Path(src).name)
            arrived.notify_all()
            while len(names) < 2:
                if not arrived.wait(timeout=2):
                    raise TimeoutError("the other clear-result write did not arrive")
        if not release.wait(timeout=2):
            raise TimeoutError("clear-result writes were not released")
        return real_replace(src, dst)

    monkeypatch.setattr(mod.os, "replace", blocking_replace)

    def write(token: str) -> None:
        try:
            mod.write_clear_result(str(tmp_path), True, token)
        except BaseException as exc:
            errors.append(exc)

    first = threading.Thread(target=write, args=("ab" * 16,))
    second = threading.Thread(target=write, args=("cd" * 16,))
    first.start()
    second.start()
    with arrived:
        while len(names) < 2:
            assert arrived.wait(timeout=2)
    release.set()
    first.join(timeout=2)
    second.join(timeout=2)
    assert errors == []
    assert len(names) == 2
    assert len(set(names)) == 2
    text = mod.clear_result_path(str(tmp_path)).read_text(encoding="utf-8").strip()
    assert text in {f"{'ab' * 16} ok", f"{'cd' * 16} ok"}


def test_origin_records_sqlite_clear_failure(tmp_path: Path, monkeypatch):
    from ux_compose.cli.serve_dev import note_shared_clear
    from ux_compose.cli.serve_restart import read_clear_result
    from ux_compose.cli.serve_state import STATE_STORE_ENV

    path = tmp_path / "empty.sqlite"
    sqlite3.connect(path).close()
    monkeypatch.setenv(STATE_STORE_ENV, str(path))
    token = "0123456789abcdef" * 2
    assert note_shared_clear(str(tmp_path), token) is False
    assert read_clear_result(str(tmp_path)) == f"{token} fail"


def test_channel_still_respawns_when_the_clear_result_cannot_be_written():
    from ux_compose.cli.serve_dev import restart_channel_worker

    spawned: list[str] = []

    def clear_and_note() -> None:
        raise OSError("disk full")

    with pytest.raises(OSError, match="disk full"):
        restart_channel_worker(
            stop=lambda: None,
            clear_and_note=clear_and_note,
            spawn=lambda: spawned.append("spawned"),
        )
    assert spawned == ["spawned"]


def test_a_second_restart_is_ignored_while_one_is_in_progress():
    from ux_compose.cli.serve_dev import claim_channel_restart, release_channel_restart

    restarting = threading.Event()
    lock = threading.Lock()
    assert claim_channel_restart(restarting, lock) is True
    assert claim_channel_restart(restarting, lock) is False
    release_channel_restart(restarting, lock)
    assert claim_channel_restart(restarting, lock) is True


def test_concurrent_restart_claims_let_only_one_through():
    from ux_compose.cli.serve_dev import claim_channel_restart

    restarting = threading.Event()
    lock = threading.Lock()
    results: list[bool] = []
    barrier = threading.Barrier(8)

    def go() -> None:
        barrier.wait(timeout=2)
        results.append(claim_channel_restart(restarting, lock))

    threads = [threading.Thread(target=go) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)
    assert results.count(True) == 1
