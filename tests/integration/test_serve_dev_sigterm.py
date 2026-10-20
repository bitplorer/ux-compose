"""Integration: a stop signal to ``uxcompose serve dev`` leaves no process behind.

Starts the real command in a fresh scaffold, waits for ``GET /`` 200,
opens the HMR WebSocket through origin, records every descendant from
``/proc`` (stdlib only), signals the origin, and asserts that:

- the WebSocket gets a close frame (1012, what uvicorn sends on shutdown);
- every descendant is gone, including the ui reloader's
  ``multiprocessing`` worker and resource tracker;
- the exit status is main's: Ctrl-C exits 0, SIGTERM and SIGHUP end the
  process by that signal (uvicorn re-raises SIGTERM; SIGHUP is default);
- the origin, ui and channel ports bind again at once.

Linux only: it reads ``/proc``.
"""
from __future__ import annotations

import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app

pytestmark = pytest.mark.skipif(
    not Path("/proc/self/stat").is_file(), reason="reads /proc (Linux)"
)


def _stat(pid: int) -> tuple[str, int, str] | None:
    """(state, ppid, starttime) of a live pid, or None when gone or a zombie."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    fields = raw[raw.rindex(")") + 2 :].split()
    if fields[0] == "Z":
        return None
    return fields[0], int(fields[1]), fields[19]


def _descendants(root: int) -> dict[int, str]:
    """Every live descendant of ``root`` -> its starttime (guards pid reuse)."""
    children: dict[int, list[int]] = {}
    starts: dict[int, str] = {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        st = _stat(int(entry))
        if st is not None:
            children.setdefault(st[1], []).append(int(entry))
            starts[int(entry)] = st[2]
    out: dict[int, str] = {}
    todo = [root]
    while todo:
        for pid in children.get(todo.pop(), []):
            out[pid] = starts[pid]
            todo.append(pid)
    return out


def _alive(procs: dict[int, str]) -> dict[int, str]:
    out = {}
    for pid, start in procs.items():
        st = _stat(pid)
        if st is not None and st[2] == start:
            out[pid] = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode()
    return out


def _in_dir(root: Path) -> dict[int, str]:
    """Live processes whose cwd is ``root``: catches a child reparented to init."""
    out: dict[int, str] = {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            cwd = os.readlink(f"/proc/{entry}/cwd")
        except OSError:
            continue
        st = _stat(int(entry))
        if st is not None and Path(cwd) == root:
            out[int(entry)] = st[2]
    return out


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _binds(port: int) -> bool:
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return False
        return True


def _get_200(url: str, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except OSError:
            pass
        time.sleep(0.3)
    return False


@pytest.fixture
def serve_dev(tmp_path):
    root = create_app(tmp_path / "demo", name="demo", level="auto", host="auto").resolve()
    port = _free_port()
    log = tmp_path / "serve.log"
    env = {**os.environ, "UX_CHANNEL_SECRET": "s" * 32}
    env.pop("DEBUG", None)
    with log.open("wb") as out:
        proc = subprocess.Popen(
            [sys.executable, "-m", "ux_compose.cli", "serve", "dev", "--port", str(port)],
            cwd=root,
            env=env,
            stdout=out,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    seen: dict[int, str] = {}
    try:
        assert _get_200(f"http://127.0.0.1:{port}/", 60), log.read_text()
        seen.update(_descendants(proc.pid))
        text = log.read_text()
        ports = [port] + [int(p) for p in re.findall(r"(?:ui|channel) http://127\.0\.0\.1:(\d+)", text)]
        assert len(ports) == 3, text
        proc.app_root = root
        cmds = " | ".join(_alive(seen).values())
        # uvicorn --reload: the ui worker and the resource tracker it starts.
        assert "multiprocessing.spawn import spawn_main" in cmds, cmds
        assert "multiprocessing.resource_tracker import main" in cmds, cmds
        proc.hmr = connect(f"ws://127.0.0.1:{port}/__uxcompose/hmr", open_timeout=10)
        yield proc, ports, seen, log
    finally:
        seen.update(_descendants(proc.pid))
        seen.update(_in_dir(root))
        for pid in _alive(seen):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if proc.poll() is None:
            proc.kill()
            proc.wait()


# Exit status of serve dev on main, kept as is (Popen returncode).
EXPECTED_RC = {signal.SIGINT: 0, signal.SIGTERM: -signal.SIGTERM, signal.SIGHUP: -signal.SIGHUP}


def _assert_clean_exit(proc, ports, seen, log, signum) -> None:
    t0 = time.monotonic()
    with pytest.raises(ConnectionClosed) as closed:
        proc.hmr.recv(timeout=10)
    assert time.monotonic() - t0 < 10
    assert closed.value.rcvd is not None, "no close frame"
    assert closed.value.rcvd.code == 1012
    try:
        rc = proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        pytest.fail("origin did not exit:\n" + log.read_text())
    deadline = time.time() + 10
    while time.time() < deadline:
        seen.update(_in_dir(proc.app_root))
        if not _alive(seen):
            break
        time.sleep(0.1)
    assert _alive(seen) == {}, log.read_text()
    assert rc == EXPECTED_RC[signum], log.read_text()
    for p in ports:
        assert _binds(p), f"port {p} still held"


@pytest.mark.parametrize(
    "signum",
    [signal.SIGTERM, signal.SIGHUP],
    ids=["SIGTERM", "SIGHUP"],
)
def test_stop_signal_leaves_no_descendant(serve_dev, signum):
    proc, ports, seen, log = serve_dev
    assert len(seen) >= 3, seen  # channel, ui reloader, ui worker (+ tailwind)
    os.kill(proc.pid, signum)
    _assert_clean_exit(proc, ports, seen, log, signum)


def test_ctrl_c_leaves_no_descendant(serve_dev):
    """Ctrl-C: the terminal sends SIGINT to the foreground process group."""
    proc, ports, seen, log = serve_dev
    os.killpg(proc.pid, signal.SIGINT)
    _assert_clean_exit(proc, ports, seen, log, signal.SIGINT)


def test_sigterm_during_channel_respawn_leaves_no_descendant(serve_dev):
    """SIGTERM right after restart-channel stopped the old channel worker."""
    proc, ports, seen, log = serve_dev
    channel = next(
        pid
        for pid, cmd in _alive(seen).items()
        if "uvicorn app:asgi" in cmd
    )
    os.kill(proc.pid, signal.SIGUSR1)
    deadline = time.time() + 10
    while _stat(channel) is not None and time.time() < deadline:
        time.sleep(0.005)
    os.kill(proc.pid, signal.SIGTERM)
    seen.update(_descendants(proc.pid))
    _assert_clean_exit(proc, ports, seen, log, signal.SIGTERM)
    time.sleep(1)  # a respawn the origin did not wait for would show up here
    seen.update(_in_dir(proc.app_root))
    assert _alive(seen) == {}, log.read_text()
