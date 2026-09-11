"""Serve-dev store lifecycle — compose prepares the file; Channel owns the class."""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.serve_state import (
    REDIS_URL_ENV,
    STATE_STORE_ENV,
    STATE_STORE_NAME,
    clear_shared_state,
    drop_shared_state,
    prepare_shared_state,
)


def test_frozen_names():
    assert STATE_STORE_ENV == "UXCOMPOSE_STATE_STORE"
    assert STATE_STORE_NAME == ".uxcompose-serve-dev.state"
    assert REDIS_URL_ENV == "REDIS_URL"


def test_lifecycle_exports_env_and_clears_kv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(STATE_STORE_ENV, raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    path = prepare_shared_state(tmp_path)
    assert path.name == STATE_STORE_NAME
    assert os.environ[STATE_STORE_ENV] == str(path)
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT, ver INTEGER)")
    conn.execute("INSERT INTO kv VALUES ('n', '1', 1)")
    conn.commit()
    conn.close()
    clear_shared_state()
    conn = sqlite3.connect(str(path))
    assert conn.execute("SELECT COUNT(*) FROM kv").fetchone()[0] == 0
    conn.close()
    drop_shared_state(tmp_path)
    assert not path.exists()


def test_prepare_does_not_export_file_store_when_redis_url_set(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    monkeypatch.setenv(STATE_STORE_ENV, str(tmp_path / "stale.state"))
    path = prepare_shared_state(tmp_path)
    assert path is None
    assert STATE_STORE_ENV not in os.environ
    leftover = tmp_path / STATE_STORE_NAME
    assert not leftover.exists()


def test_drop_unlinks_wal_sidecars(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(STATE_STORE_ENV, raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    path = prepare_shared_state(tmp_path)
    path.write_bytes(b"x")
    wal = Path(str(path) + "-wal")
    shm = Path(str(path) + "-shm")
    wal.write_bytes(b"w")
    shm.write_bytes(b"s")
    drop_shared_state(tmp_path)
    assert not path.exists()
    assert not wal.exists()
    assert not shm.exists()


def test_clear_without_env_is_noop(monkeypatch):
    monkeypatch.delenv(STATE_STORE_ENV, raising=False)
    clear_shared_state()


def test_compose_does_not_own_a_store_class():
    import ast

    banned = {
        "FileStateStore",
        "MemoryStateStore",
        "RedisStateStore",
        "StateConflict",
        "EditSlot",
    }
    root = ROOT / "src" / "ux_compose"
    for path in root.rglob("*.py"):
        if "wire" in path.parts:
            continue
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        assert not (names & banned), (path, names & banned)
        if path.name == "serve_state.py":
            assert "import pickle" not in src
            assert "pickle.dumps" not in src
            assert "pickle.loads" not in src
            assert "import ux_channel" not in src
            assert "from ux_channel" not in src
    boot = (root / "wire" / "boot.py").read_text(encoding="utf-8")
    assert "_bind_shared_draft" not in boot
    assert "channel.state =" not in boot
