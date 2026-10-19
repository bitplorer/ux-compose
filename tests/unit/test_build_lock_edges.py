"""Behavior the build-lock mutants have to break.

Blank and unset stay on the default budget. ``none`` from the environment
does not. ``lock_timeout=None`` is not a half-second name-lock wait.
A failed reacquire and a false wait both raise, and an importer already
blocked on the name lock conflicts before that build runs.
"""
from __future__ import annotations

import importlib
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest

from tests.asgi_http import asgi_get

pytestmark = pytest.mark.import_isolation

_ENV = "UX_COMPOSE_BUILD_LOCK_TIMEOUT"


def _purge(name: str) -> None:
    for key in list(sys.modules):
        if key == name or key.startswith(name + "."):
            sys.modules.pop(key, None)


def _route(root: Path, name: str, body: str) -> Path:
    pkg = root / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "home.py").write_text(textwrap.dedent(body), encoding="utf-8")
    return pkg


def _hold_foreign(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, gate_name: str):
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nRELEASE = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    other = tmp_path / "b" / name
    other.mkdir(parents=True)
    (other / "__init__.py").write_text("", encoding="utf-8")
    (other / "main.py").write_text(
        textwrap.dedent(
            f"""\
            import {gate_name}
            {gate_name}.IN.set()
            {gate_name}.RELEASE.wait(5)
            VALUE = 'OTHER'
            """
        ),
        encoding="utf-8",
    )
    folder = _route(
        tmp_path / "a",
        name,
        """\
        class Home:
            id = 'home'
            routes = ('get',)
            def render(self):
                return 'OURS'
        """,
    )
    monkeypatch.syspath_prepend(str(other.parent))
    importlib.invalidate_caches()
    gate = importlib.import_module(gate_name)
    return folder, gate


def _expect_default_budget(tmp_path, monkeypatch, name: str, env: str | None) -> None:
    """A foreign import held past the patched default raises at that default."""
    from ux_compose.build import BuildLockTimeout, build

    monkeypatch.setattr("ux_compose.routing.core._DEFAULT_LOCK_TIMEOUT", 0.25)
    if env is None:
        monkeypatch.delenv(_ENV, raising=False)
    else:
        monkeypatch.setenv(_ENV, env)
    gate_name = f"gate_{name}"
    folder, gate = _hold_foreign(tmp_path, monkeypatch, name, gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    def caller() -> None:
        started = time.perf_counter()
        try:
            built = build(folder, name="X", host="asgi", live="null", level=1)
            out["text"] = asgi_get(built[1], "/home").text
        except BaseException as exc:
            out["err"] = exc
        out["elapsed"] = time.perf_counter() - started

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=caller, daemon=True)
    try:
        left.start()
        assert gate.IN.wait(2)
        right.start()
        right.join(1)
        assert not right.is_alive()
        err = out.get("err")
        assert isinstance(err, BuildLockTimeout), out.get("text")
        assert err.timeout == 0.25
        assert "after 0.25s" in str(err)
        assert float(out["elapsed"]) < 1
        assert "text" not in out
    finally:
        gate.RELEASE.set()
        left.join(1)
        right.join(1)
        _purge(name)
        sys.modules.pop(gate_name, None)


@pytest.mark.parametrize("env", ["", "   "])
def test_blank_env_times_out_at_the_default(tmp_path, monkeypatch, env: str):
    """'' and whitespace use the default budget, including a patched one.

    Making a blank value unbounded leaves this thread in the wait.
    """
    label = "empty" if env == "" else "spaces"
    _expect_default_budget(tmp_path, monkeypatch, f"blank{label}", env)


def test_unset_env_times_out_at_the_default(tmp_path, monkeypatch):
    """An unset variable uses the default budget, including a patched one.

    Treating a missing variable as no limit leaves this thread in the wait.
    """
    _expect_default_budget(tmp_path, monkeypatch, "unsetapp", None)


def test_env_none_waits_past_a_tiny_default(tmp_path, monkeypatch):
    """``UX_COMPOSE_BUILD_LOCK_TIMEOUT=none`` does not become the default.

    The argument is omitted. The environment is what says there is no limit.
    A tiny patched default must not raise while the import is still held.
    """
    from ux_compose.build import build

    monkeypatch.setattr("ux_compose.routing.core._DEFAULT_LOCK_TIMEOUT", 0.2)
    monkeypatch.setenv(_ENV, "none")
    name = "envnone"
    gate_name = "gate_envnone"
    folder, gate = _hold_foreign(tmp_path, monkeypatch, name, gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    def caller() -> None:
        started = time.perf_counter()
        try:
            built = build(folder, name="X", host="asgi", live="null", level=1)
            out["text"] = asgi_get(built[1], "/home").text
        except BaseException as exc:
            out["err"] = exc
        out["elapsed"] = time.perf_counter() - started

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=caller, daemon=True)
    try:
        left.start()
        assert gate.IN.wait(2)
        right.start()
        time.sleep(0.7)
        assert right.is_alive(), out.get("err")
        gate.RELEASE.set()
        right.join(2)
        assert not right.is_alive()
        assert out.get("err") is None, out.get("err")
        assert out.get("text") == "OURS"
        assert float(out["elapsed"]) > 0.6
        left.join(2)
        assert out.get("loader") is None, out.get("loader")
    finally:
        gate.RELEASE.set()
        left.join(1)
        right.join(1)
        _purge(name)
        sys.modules.pop(gate_name, None)


def test_none_acquire_waits_past_half_a_second(tmp_path, monkeypatch):
    """``lock_timeout=None`` keeps waiting on the name lock past 0.5s.

    Another thread holds that lock for more than a second. Capping the
    acquire at 0.5s raises ``BuildLockTimeout`` while this call is still
    supposed to be waiting. After the holder releases, the build serves.
    """
    from ux_compose.build import BuildLockTimeout, build
    from ux_compose.routing.core import package_build_lock

    monkeypatch.delenv(_ENV, raising=False)
    name = "nonelock"
    folder = _route(
        tmp_path,
        name,
        """\
        class Home:
            id = 'home'
            routes = ('get',)
            def render(self):
                return 'OURS'
        """,
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    lock = package_build_lock(name)
    release = threading.Event()
    out: dict[str, object] = {}

    def holder() -> None:
        assert lock.acquire(timeout=2)
        try:
            release.wait(5)
        finally:
            lock.release()

    def waiter() -> None:
        started = time.perf_counter()
        try:
            built = build(folder, name="X", host="asgi", live="null", level=1, lock_timeout=None)
            out["text"] = asgi_get(built[1], "/home").text
        except BaseException as exc:
            out["err"] = exc
        out["elapsed"] = time.perf_counter() - started

    left = threading.Thread(target=holder, daemon=True)
    right = threading.Thread(target=waiter, daemon=True)
    try:
        left.start()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and lock.owner() != left.ident:
            time.sleep(0.01)
        assert lock.owner() == left.ident
        right.start()
        time.sleep(1.1)
        assert right.is_alive(), out.get("err")
        assert "err" not in out
        release.set()
        right.join(3)
        assert not right.is_alive()
        assert not isinstance(out.get("err"), BuildLockTimeout)
        assert out.get("err") is None, out.get("err")
        assert out.get("text") == "OURS"
        assert float(out["elapsed"]) > 1
    finally:
        release.set()
        left.join(1)
        right.join(1)
        _purge(name)


def test_failed_reacquire_raises_and_serves_nothing(tmp_path, monkeypatch):
    """The wait ends, then taking the name lock back fails.

    Returning from that failure lets the build continue. The import has
    already released, so a later false-outcome check does not raise.
    ``BuildLockTimeout`` has to leave ``build()``, and no page is served.
    """
    import ux_compose.routing.core as routing_core
    from ux_compose.build import BuildLockTimeout, build

    monkeypatch.delenv(_ENV, raising=False)
    name = "reacq"
    gate_name = "gate_reacq"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\n"
        "IN = threading.Event()\n"
        "HELD = threading.Event()\n"
        "RELEASE = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    other = tmp_path / "b" / name
    other.mkdir(parents=True)
    (other / "__init__.py").write_text("", encoding="utf-8")
    (other / "main.py").write_text(
        textwrap.dedent(
            f"""\
            import {gate_name}
            {gate_name}.IN.set()
            {gate_name}.HELD.wait(5)
            VALUE = 'OTHER'
            """
        ),
        encoding="utf-8",
    )
    folder = _route(
        tmp_path / "a",
        name,
        """\
        class Home:
            id = 'home'
            routes = ('get',)
            def render(self):
                return 'OURS'
        """,
    )
    monkeypatch.syspath_prepend(str(other.parent))
    importlib.invalidate_caches()
    gate = importlib.import_module(gate_name)
    entered = threading.Event()
    real_wait = routing_core._wait_for_import_or_name_lock

    def _mark(names, lock, timeout):
        entered.set()
        return real_wait(names, lock, timeout)

    monkeypatch.setattr(routing_core, "_wait_for_import_or_name_lock", _mark)
    # The other folder is still loaded, so the generation check would raise
    # PackageImportConflict before the failed reacquire. This case is the
    # reacquire itself: nothing left to name as the other folder.
    monkeypatch.setattr(routing_core, "_loaded_from_other_folder", lambda *args, **kwargs: None)
    lock = routing_core.package_build_lock(name)
    stop = threading.Event()
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    def holder() -> None:
        assert entered.wait(2)
        while not stop.is_set():
            if lock.acquire(timeout=0.05):
                gate.HELD.set()
                stop.wait(3)
                if lock.depth_of_current() > 0:
                    lock.release()
                return

    def caller() -> None:
        assert gate.IN.wait(2)
        try:
            built = build(
                folder, name="X", host="asgi", live="null", level=1, lock_timeout=0.4
            )
            out["text"] = asgi_get(built[1], "/home").text
        except BaseException as exc:
            out["err"] = exc

    left = threading.Thread(target=loader, daemon=True)
    mid = threading.Thread(target=holder, daemon=True)
    right = threading.Thread(target=caller, daemon=True)
    try:
        left.start()
        mid.start()
        right.start()
        right.join(2)
        assert not right.is_alive()
        err = out.get("err")
        assert isinstance(err, BuildLockTimeout), out.get("text")
        assert err.timeout == 0.4
        assert "text" not in out
        left.join(2)
        assert out.get("loader") is None, out.get("loader")
    finally:
        stop.set()
        gate.HELD.set()
        gate.RELEASE.set()
        left.join(1)
        mid.join(1)
        right.join(1)
        _purge(name)
        sys.modules.pop(gate_name, None)


def test_false_wait_raises_and_serves_nothing(tmp_path, monkeypatch):
    """A wait that reports the budget is over raises after the import clears.

    The next pass would load this folder. Dropping the raise serves a page
    instead of letting ``BuildLockTimeout`` out of ``build()``.
    """
    import ux_compose.routing.core as routing_core
    from ux_compose.build import BuildLockTimeout, build

    monkeypatch.delenv(_ENV, raising=False)
    name = "falsewait"
    gate_name = "gate_falsewait"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nOUT = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    other = tmp_path / "b" / name
    other.mkdir(parents=True)
    (other / "__init__.py").write_text("", encoding="utf-8")
    (other / "main.py").write_text(
        textwrap.dedent(
            f"""\
            import {gate_name}
            {gate_name}.IN.set()
            {gate_name}.OUT.wait(5)
            VALUE = 'OTHER'
            """
        ),
        encoding="utf-8",
    )
    folder = _route(
        tmp_path / "a",
        name,
        """\
        class Home:
            id = 'home'
            routes = ('get',)
            def render(self):
                return 'OURS'
        """,
    )
    monkeypatch.syspath_prepend(str(other.parent))
    importlib.invalidate_caches()
    gate = importlib.import_module(gate_name)

    def _budget_over(names, lock, timeout):
        gate.OUT.set()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and any(
            routing_core._other_thread_importing(item) for item in names
        ):
            time.sleep(0.01)
        return False

    monkeypatch.setattr(routing_core, "_wait_for_import_or_name_lock", _budget_over)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    def caller() -> None:
        assert gate.IN.wait(2)
        try:
            built = build(
                folder, name="X", host="asgi", live="null", level=1, lock_timeout=2
            )
            out["text"] = asgi_get(built[1], "/home").text
        except BaseException as exc:
            out["err"] = exc

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=caller, daemon=True)
    try:
        left.start()
        right.start()
        right.join(2)
        left.join(2)
        assert not right.is_alive() and not left.is_alive()
        err = out.get("err")
        assert isinstance(err, BuildLockTimeout), out.get("text")
        assert err.timeout == 2
        assert "text" not in out
        assert out.get("loader") is None, out.get("loader")
    finally:
        gate.OUT.set()
        left.join(1)
        right.join(1)
        _purge(name)
        sys.modules.pop(gate_name, None)


def test_name_lock_waiter_conflicts_before_that_build_runs(tmp_path, monkeypatch):
    """The importer is already waiting on the name lock this build holds.

    ``PackageImportConflict`` is raised before that other ``build()`` returns.
    Nothing from this folder is served. The waiters check and the precheck
    are what stop the call. Letting the waiter run first, then conflicting,
    is a different path.
    """
    from ux_compose.build import build
    from ux_compose.routing.core import PackageImportConflict, package_build_lock

    monkeypatch.delenv(_ENV, raising=False)
    name = "failfast"
    gate_name = "gate_failfast"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nDONE = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    folder_b = tmp_path / "b" / name
    folder_a = tmp_path / "a" / name
    for folder, marker in ((folder_b, "B"), (folder_a, "A")):
        _route(
            folder.parent,
            name,
            f"""\
            class Home:
                id = 'home'
                routes = ('get',)
                def render(self):
                    return 'FROM_{marker}'
            """,
        )
    (folder_b / "main.py").write_text(
        textwrap.dedent(
            f"""\
            import {gate_name}
            from pathlib import Path
            from ux_compose.build import build
            {gate_name}.IN.set()
            build(Path(__file__).resolve().parent, name='B', host='asgi', live='null', level=1, lock_timeout=None)
            {gate_name}.DONE.set()
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(folder_b.parent))
    importlib.invalidate_caches()
    gate = importlib.import_module(gate_name)
    lock = package_build_lock(name)
    assert lock.acquire(timeout=1)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
            out["loader"] = "ok"
        except BaseException as exc:
            out["loader"] = exc

    left = threading.Thread(target=loader, daemon=True)
    try:
        left.start()
        assert gate.IN.wait(2)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not lock.waiters():
            time.sleep(0.01)
        assert lock.waiters()
        try:
            built = build(
                folder_a, name="A", host="asgi", live="null", level=1, lock_timeout=None
            )
            out["text"] = asgi_get(built[1], "/home").text
        except BaseException as exc:
            out["err"] = exc
        assert isinstance(out.get("err"), PackageImportConflict), out.get("text")
        err = out["err"]
        assert isinstance(err, PackageImportConflict)
        assert err.loaded_from == folder_b.resolve()
        assert err.building == folder_a.resolve()
        assert "text" not in out
        assert not gate.DONE.is_set()
        assert left.is_alive()
    finally:
        if lock.depth_of_current() > 0:
            lock.release()
        left.join(2)
        _purge(name)
        sys.modules.pop(gate_name, None)
