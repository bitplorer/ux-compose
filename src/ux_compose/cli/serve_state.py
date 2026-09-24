"""Serve-dev shared-store *lifecycle* — not the store.

Channel owns ``FileStateStore`` (JSON sqlite) and opens it from
``UXCOMPOSE_STATE_STORE``. Redis (``REDIS_URL``) still wins inside
``Channel.boot``. Do not export both — Channel prefers Redis and
would ignore the sqlite path.

This module never imports ``ux_channel``. Origin prepares a cwd file
when Redis is unset, exports the env both workers inherit, clears the
bag on ``serve restart-channel``, and unlinks WAL sidecars on shutdown.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

STATE_STORE_ENV = "UXCOMPOSE_STATE_STORE"
STATE_STORE_NAME = ".uxcompose-serve-dev.state"
REDIS_URL_ENV = "REDIS_URL"


def redis_url() -> str | None:
    raw = os.environ.get(REDIS_URL_ENV)
    return raw or None


def state_store_path() -> Path | None:
    raw = os.environ.get(STATE_STORE_ENV)
    if not raw:
        return None
    return Path(raw)


def prepare_shared_state(cwd: str | Path) -> Path | None:
    """Origin: pick a cwd file, drop leftovers, export env for both workers.

    When ``REDIS_URL`` is set, Channel prefers Redis. Do not also export
    ``UXCOMPOSE_STATE_STORE`` — that pair is a lie (sqlite is unused).
    """
    if redis_url():
        os.environ.pop(STATE_STORE_ENV, None)
        return None
    path = Path(cwd) / STATE_STORE_NAME
    _unlink_store(path)
    os.environ[STATE_STORE_ENV] = str(path)
    return path


def clear_shared_state() -> None:
    """``serve restart-channel``: empty the bag; keep the same inode."""
    path = state_store_path()
    if path is None or not path.exists():
        return
    try:
        conn = sqlite3.connect(str(path), timeout=8.0)
        try:
            conn.execute("DELETE FROM kv")
            conn.commit()
        except sqlite3.OperationalError:
            return
        finally:
            conn.close()
    except sqlite3.Error:
        return


def drop_shared_state(cwd: str | Path | None = None) -> None:
    """Origin shutdown: remove the sqlite file (+ WAL sidecars)."""
    path = state_store_path()
    if path is None and cwd is not None:
        path = Path(cwd) / STATE_STORE_NAME
    if path is not None:
        _unlink_store(path)


def _unlink_store(path: Path) -> None:
    for extra in ("", "-wal", "-shm"):
        try:
            Path(str(path) + extra).unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue


__all__ = [
    "STATE_STORE_ENV",
    "STATE_STORE_NAME",
    "REDIS_URL_ENV",
    "redis_url",
    "state_store_path",
    "prepare_shared_state",
    "clear_shared_state",
    "drop_shared_state",
]
