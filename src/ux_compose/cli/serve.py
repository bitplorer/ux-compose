"""``uxcompose serve`` — mode argv. Clocks start in ``serve_dev.py``.

Frozen modes: ``dev`` / ``prod`` / ``restart-channel``.
argv ``development`` / ``production`` / ``restart_channel`` are not synonyms.
"""
from __future__ import annotations

import argparse
import sys


def _missing_serve_dev_extras() -> list[str]:
    """Packages origin needs. Missing → fail closed, no second architecture."""
    missing: list[str] = []
    for name in ("httpx", "starlette", "websockets"):
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    return missing


_SERVE_MODES = {
    "dev": "dev",
    "prod": "prod",
    "restart-channel": "restart-channel",
}


def _serve_help() -> None:
    print("uxcompose serve needs a mode — clocks are not flags")
    print("")
    print("  uxcompose serve dev  [app:asgi] [--host 0.0.0.0] [--port 8080]")
    print("                      [--reload-dir PATH ...] [--tunnel none|ngrok|cloudflare]")
    print("  uxcompose serve prod [app:asgi] [--host 0.0.0.0] [--port 8080]")
    print("  uxcompose serve restart-channel")
    print("")
    print("  dev              origin + ui worker + channel worker + CSS watch")
    print("  prod             clocks hard off (local prod-like run; deploy still uses uvicorn)")
    print("  restart-channel  one-shot: drop Channel RAM in a running serve dev")


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        _serve_help()
        return 0 if argv else 2
    raw = argv[0].lower()
    if raw not in _SERVE_MODES:
        print(
            f"unknown serve mode {argv[0]!r} — use 'dev', 'prod', or 'restart-channel'",
            file=sys.stderr,
        )
        _serve_help()
        return 2
    mode = _SERVE_MODES[raw]
    rest = argv[1:]

    if mode == "restart-channel":
        if rest and rest[0] in ("-h", "--help"):
            print("uxcompose serve restart-channel")
            print("  one-shot Channel RAM drop for a running serve dev in this directory")
            print("  does not change the next *.py save")
            return 0
        if rest:
            print(
                "serve restart-channel does not accept "
                + " ".join(rest)
                + " — it is a one-shot action, not a flag",
                file=sys.stderr,
            )
            return 2
        from ux_compose.cli.serve_restart import restart_channel

        return restart_channel()

    p = argparse.ArgumentParser(prog=f"uxcompose serve {mode}", add_help=True)
    p.add_argument("app", nargs="?", default="app:asgi")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    if mode == "dev":
        p.add_argument(
            "--reload-dir",
            action="append",
            default=None,
            dest="reload_dir",
            help="uvicorn reload dir (repeatable; default . and routes)",
        )
        p.add_argument(
            "--tunnel",
            default="none",
            help="Public tunnel after health green: none|ngrok|cloudflare",
        )
        p.add_argument("--tunnel-token", default=None)
        p.add_argument("--health-path", default="/")
        p.add_argument("--health-timeout", type=float, default=30.0)
    args, unknown = p.parse_known_args(rest)
    if unknown:
        print(
            f"uxcompose serve {mode} does not accept {' '.join(unknown)}",
            file=sys.stderr,
        )
        if mode == "prod":
            print("clocks live on 'serve dev', not flags on prod", file=sys.stderr)
        return 2

    tunnel_value = getattr(args, "tunnel", "none")
    tunnel_token = getattr(args, "tunnel_token", None)
    health_path = getattr(args, "health_path", "/")
    health_timeout = getattr(args, "health_timeout", 30.0)
    reload_dirs = list(getattr(args, "reload_dir", None) or [])
    if not reload_dirs:
        reload_dirs = [".", "routes"]

    try:
        import uvicorn
    except ImportError:
        print("uvicorn required: pip install uvicorn", file=sys.stderr)
        return 1

    from ux_compose.cli.tunnel import parse_provider

    try:
        provider = parse_provider(tunnel_value)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    if mode == "dev":
        missing = _missing_serve_dev_extras()
        if missing:
            print(
                "serve dev needs "
                + ", ".join(missing)
                + " — from the clone: pip install -e '.[serve]'",
                file=sys.stderr,
            )
            return 1
        from ux_compose.cli.serve_dev import run as run_serve_dev

        print(
            f"uxcompose serve dev {args.app} http://{args.host}:{args.port} "
            f"origin+ui+channel css_watch=on tunnel={provider}"
        )
        return run_serve_dev(
            app_ref=args.app,
            host=args.host,
            port=args.port,
            reload_dirs=reload_dirs,
            css_watch=True,
            tunnel=tunnel_value,
            tunnel_token=tunnel_token,
            health_path=health_path,
            health_timeout=health_timeout,
        )

    print(
        f"uxcompose serve prod {args.app} http://{args.host}:{args.port} "
        f"clocks=off"
    )
    uvicorn.run(args.app, host=args.host, port=args.port)
    return 0
