"""One-shot Channel restart for a running ``serve dev``.

Not a clock. Not a sticky flag. ``uxcompose serve restart-channel``
reads ``.uxcompose-serve-dev.pid`` and sends SIGUSR1 to the origin.
The origin clears the sqlite bag, writes ``.uxcompose-serve-dev.clear``,
and respawns only the channel worker. The command waits for that result.
"""
from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

PID_NAME = ".uxcompose-serve-dev.pid"
CLEAR_NAME = ".uxcompose-serve-dev.clear"
# clear_shared_state lets sqlite wait 8s on a lock. Stay past that so a
# locked bag is reported as a failed clear, not a timeout.
CLEAR_TIMEOUT_S = 10.0


def pid_path(cwd: str | None = None) -> Path:
    return Path(cwd or os.getcwd()) / PID_NAME


def clear_result_path(cwd: str | None = None) -> Path:
    return Path(cwd or os.getcwd()) / CLEAR_NAME


def write_clear_result(cwd: str | None, ok: bool) -> None:
    """Atomically publish whether the sqlite bag was cleared."""
    path = clear_result_path(cwd)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("ok\n" if ok else "fail\n", encoding="utf-8")
    os.replace(tmp, path)


def read_clear_result(cwd: str | None = None) -> str | None:
    path = clear_result_path(cwd)
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def _drop_clear_result(cwd: str | None) -> bool:
    path = clear_result_path(cwd)
    try:
        path.unlink()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


def write_pid(cwd: str) -> Path:
    path = pid_path(cwd)
    path.write_text(str(os.getpid()), encoding="utf-8")
    return path


def clear_pid(cwd: str) -> None:
    path = pid_path(cwd)
    try:
        if path.is_file() and path.read_text(encoding="utf-8").strip() == str(os.getpid()):
            path.unlink()
    except OSError:
        return


def restart_channel(*, cwd: str | None = None, timeout: float = CLEAR_TIMEOUT_S) -> int:
    """Signal a running serve dev origin to respawn Channel. Fail closed.

    Waits until the origin writes the sqlite-clear result, or until
    ``timeout`` seconds pass.
    """
    sig = getattr(signal, "SIGUSR1", None)
    if sig is None:
        print("serve restart-channel: SIGUSR1 is not available on this OS", file=sys.stderr)
        return 1
    path = pid_path(cwd)
    if not path.is_file():
        print(
            "serve restart-channel: no running serve dev in this directory "
            f"(missing {path.name})",
            file=sys.stderr,
        )
        return 1
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        print("serve restart-channel: pidfile is not an integer", file=sys.stderr)
        return 1
    if pid <= 0:
        print("serve restart-channel: pidfile is not an integer", file=sys.stderr)
        return 1
    try:
        os.kill(pid, 0)
    except OSError:
        print("serve restart-channel: pidfile is stale — no such process", file=sys.stderr)
        try:
            path.unlink()
        except OSError:
            pass
        return 1
    if not _drop_clear_result(cwd):
        print(
            "serve restart-channel: could not remove the previous sqlite result",
            file=sys.stderr,
        )
        return 1
    os.kill(pid, sig)
    deadline = time.monotonic() + timeout
    while True:
        result = read_clear_result(cwd)
        if result == "ok":
            print(f"serve restart-channel: sqlite bag cleared (origin pid {pid})")
            return 0
        if result is not None:
            print("serve restart-channel: sqlite bag was not cleared", file=sys.stderr)
            return 1
        if time.monotonic() >= deadline:
            print(
                "serve restart-channel: timed out waiting for the sqlite clear",
                file=sys.stderr,
            )
            return 1
        time.sleep(0.05)
