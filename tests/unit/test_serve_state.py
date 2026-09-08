"""Shared serve-dev draft store — two store objects, one file."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.serve_state import FileStateStore, STATE_STORE_ENV


def test_two_file_stores_share_values(tmp_path):
    path = tmp_path / "draft.sqlite"
    writer = FileStateStore(path)
    reader = FileStateStore(path)
    writer.set("ui.hello.n", 10)
    assert reader.get("ui.hello.n", 0) == 10


def test_file_store_change_is_visible_to_peer(tmp_path):
    path = tmp_path / "draft.sqlite"
    a = FileStateStore(path)
    b = FileStateStore(path)
    a.change("n", lambda v: (v or 0) + 1, default=0)
    a.change("n", lambda v: (v or 0) + 1, default=0)
    assert b.get("n", 0) == 2


def test_file_store_clear_empties_peer(tmp_path):
    path = tmp_path / "draft.sqlite"
    a = FileStateStore(path)
    b = FileStateStore(path)
    a.set("k", "v")
    a.clear()
    assert b.get("k", None) is None


def test_state_store_env_name():
    assert STATE_STORE_ENV == "UXCOMPOSE_STATE_STORE"
