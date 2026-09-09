"""One-shot Channel restart for a running ``serve dev``.

Not a clock. Not a sticky flag. ``uxcompose serve restart-channel``
reads ``.uxcompose-serve-dev.pid`` and sends SIGUSR1 to the origin.
The origin respawns only the channel worker.
"""
from __future__ import annotations

import os
import signal
import sys
from pathlib import Path

PID_NAME = ".uxcompose-serve-dev.pid"


def pid_path(cwd: str | None = None) -> Path:
    return Path(cwd or os.getcwd()) / PID_NAME


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


def restart_channel(*, cwd: str | None = None) -> int:
    """Signal a running serve dev origin to respawn Channel. Fail closed."""
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
    os.kill(pid, sig)
    print(f"serve restart-channel: signalled origin pid {pid}")
    return 0
