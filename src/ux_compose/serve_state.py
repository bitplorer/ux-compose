"""Shared Channel draft/session store for ``uxcompose serve dev``.

Session lives with Channel (``ch.draft`` → ``ch.state``). Origin sends
Document GET to the ui worker and ``/ux-channel*`` to the channel worker,
so both processes must share one StateStore or nav-tab SSR paints defaults.

Redis (``REDIS_URL``) is the product multi-worker path. This module is the
no-Redis serve-dev plane: a sqlite file both workers open.

Isolation: this module never imports ``ux_channel``. ``wire/boot.py``
assigns the store onto ``ch.state`` after Channel.boot.
"""
from __future__ import annotations

import copy
import os
import pickle
import sqlite3
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

STATE_STORE_ENV = "UXCOMPOSE_STATE_STORE"
STATE_STORE_NAME = ".uxcompose-serve-dev.state"
Mutator = Callable[[Any], Any]


class StateConflict(RuntimeError):
    """CAS commit failed — another writer changed the key during ``edit``."""


@dataclass
class EditSlot:
    key: str
    value: Any
    _store: Any = field(repr=False)
    _version: int = field(repr=False)
    _default: Any = field(repr=False, default=None)
    _committed: bool = field(default=False, repr=False)

    def __enter__(self) -> "EditSlot":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            return None
        self._commit()
        return None

    async def __aenter__(self) -> "EditSlot":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            return None
        self._commit()
        self._committed = True
        return None

    def _commit(self) -> None:
        self._store._cas_set(self.key, self._version, self.value)
        self._committed = True


def _dump(value: Any) -> bytes:
    return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)


def _load(raw: bytes) -> Any:
    return pickle.loads(raw)


class FileStateStore:
    """Sqlite StateStore shared across serve-dev ui + channel workers."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            str(self.path),
            timeout=8.0,
            check_same_thread=False,
            isolation_level=None,
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=8000")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS kv ("
            " k TEXT PRIMARY KEY NOT NULL,"
            " v BLOB NOT NULL,"
            " ver INTEGER NOT NULL"
            ")"
        )

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            row = self._conn.execute(
                "SELECT v FROM kv WHERE k = ?", (key,)
            ).fetchone()
        if row is None:
            return copy.deepcopy(default)
        return copy.deepcopy(_load(row[0]))

    def set(self, key: str, value: Any) -> None:
        blob = _dump(copy.deepcopy(value))
        with self._lock:
            self._conn.execute(
                "INSERT INTO kv(k, v, ver) VALUES (?, ?, 1) "
                "ON CONFLICT(k) DO UPDATE SET v = excluded.v, ver = kv.ver + 1",
                (key, blob),
            )

    def delete(self, key: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM kv WHERE k = ?", (key,))

    def _snapshot(self, key: str, default: Any) -> tuple[Any, int]:
        with self._lock:
            row = self._conn.execute(
                "SELECT v, ver FROM kv WHERE k = ?", (key,)
            ).fetchone()
        if row is None:
            return copy.deepcopy(default), 0
        return copy.deepcopy(_load(row[0])), int(row[1])

    def _cas_set(self, key: str, expected_ver: int, value: Any) -> None:
        blob = _dump(copy.deepcopy(value))
        with self._lock:
            if expected_ver == 0:
                try:
                    self._conn.execute(
                        "INSERT INTO kv(k, v, ver) VALUES (?, ?, 1)",
                        (key, blob),
                    )
                    return
                except sqlite3.IntegrityError:
                    cur = self._conn.execute(
                        "SELECT ver FROM kv WHERE k = ?", (key,)
                    ).fetchone()
                    now = int(cur[0]) if cur else -1
                    raise StateConflict(
                        f"state key {key!r} changed during edit "
                        f"(expected ver={expected_ver}, now={now}); retry the with-block"
                    ) from None
            cur = self._conn.execute(
                "UPDATE kv SET v = ?, ver = ver + 1 WHERE k = ? AND ver = ?",
                (blob, key, expected_ver),
            )
            if cur.rowcount == 1:
                return
            row = self._conn.execute(
                "SELECT ver FROM kv WHERE k = ?", (key,)
            ).fetchone()
            now = int(row[0]) if row else 0
            raise StateConflict(
                f"state key {key!r} changed during edit "
                f"(expected ver={expected_ver}, now={now}); retry the with-block"
            )

    def edit(self, key: str, *, default: Any = None) -> EditSlot:
        value, ver = self._snapshot(key, default)
        return EditSlot(
            key=key, value=value, _store=self, _version=ver, _default=default
        )

    def edit_retry(
        self,
        key: str,
        fn: Mutator,
        *,
        default: Any = None,
        retries: int = 32,
    ) -> Any:
        last: Exception | None = None
        for _ in range(max(1, int(retries))):
            try:
                with self.edit(key, default=default) as slot:
                    slot.value = fn(slot.value)
                return self.get(key, default)
            except StateConflict as exc:
                last = exc
                continue
        raise StateConflict(
            f"edit_retry exhausted for {key!r} after {retries} attempts"
        ) from last

    def change(self, key: str, mutator: Mutator, *, default: Any = None) -> Any:
        with self._lock:
            row = self._conn.execute(
                "SELECT v FROM kv WHERE k = ?", (key,)
            ).fetchone()
            if row is None:
                current = copy.deepcopy(default)
            else:
                current = copy.deepcopy(_load(row[0]))
            new = mutator(current)
            blob = _dump(copy.deepcopy(new))
            self._conn.execute(
                "INSERT INTO kv(k, v, ver) VALUES (?, ?, 1) "
                "ON CONFLICT(k) DO UPDATE SET v = excluded.v, ver = kv.ver + 1",
                (key, blob),
            )
            return copy.deepcopy(new)

    def merge(self, key: str, updates: Mapping[str, Any], *, default: Any = None) -> Any:
        def _mut(base: Any) -> Any:
            if base is None:
                base = {}
            if not isinstance(base, dict):
                raise TypeError(f"StateStore.merge expects dict at {key!r}")
            return {**base, **dict(updates)}

        return self.change(key, _mut, default=default if default is not None else {})

    def update(self, key: str, mutator: Mutator, *, default: Any = None) -> Any:
        return self.change(key, mutator, default=default)

    def patch(self, key: str, updates: Mapping[str, Any], *, default: Any = None) -> Any:
        return self.merge(key, updates, default=default)

    def incr(self, key: str, delta: float = 1, *, default: float = 0) -> float:
        def _mut(cur: Any) -> Any:
            base = default if cur is None else cur
            try:
                if (
                    isinstance(base, int)
                    and isinstance(delta, int)
                    and not isinstance(delta, bool)
                ):
                    return int(base) + int(delta)
                return float(base) + float(delta)
            except (TypeError, ValueError) as exc:
                raise TypeError(
                    f"StateStore.incr expects numeric at {key!r}, got {type(base).__name__}"
                ) from exc

        return self.change(key, _mut, default=default)  # type: ignore[return-value]

    def clear(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM kv")

    def keys(self) -> list[str]:
        with self._lock:
            rows = self._conn.execute("SELECT k FROM kv").fetchall()
        return [str(r[0]) for r in rows]


def state_store_path() -> Path | None:
    raw = os.environ.get(STATE_STORE_ENV)
    if not raw:
        return None
    return Path(raw)


def shared_state_store() -> FileStateStore | None:
    """Open the serve-dev shared store, or None when env is unset (prod / tests)."""
    if os.environ.get("REDIS_URL"):
        return None
    path = state_store_path()
    if path is None:
        return None
    return FileStateStore(path)


def prepare_shared_state(cwd: str | Path) -> Path:
    """Origin: pick a cwd file, drop leftovers, export env for both workers."""
    path = Path(cwd) / STATE_STORE_NAME
    _unlink_store(path)
    os.environ[STATE_STORE_ENV] = str(path)
    FileStateStore(path)
    return path


def clear_shared_state() -> None:
    """``serve restart-channel``: empty the bag; keep the same inode."""
    store = shared_state_store()
    if store is not None:
        store.clear()


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
    "StateConflict",
    "FileStateStore",
    "state_store_path",
    "shared_state_store",
    "prepare_shared_state",
    "clear_shared_state",
    "drop_shared_state",
]
