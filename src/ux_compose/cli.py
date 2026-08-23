"""uxcompose CLI — product DX (create-app, serve, doctor).

Ownership (residual-free)
-------------------------
Product application DX lives here, not on ``uxdom``::

| Command | Role |
|---------|------|
| ``uxcompose create-app`` | **Sole** product scaffold |
| ``uxcompose serve`` | Run composition-root ASGI (uvicorn) |
| ``uxcompose doctor`` | Product surface / route health |

``uxdom`` CLI may still scaffold pure-dom experiments; product apps use this CLI.
See ``docs/FLOW.md``.
"""
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        _help()
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd in ("create-app", "create"):
        return _create_app(rest)
    if cmd == "serve":
        return _serve(rest)
    if cmd == "doctor":
        return _doctor(rest)
    print(f"unknown command: {cmd}", file=sys.stderr)
    _help()
    return 2


def _help() -> None:
    print("uxcompose — product DX for ux-compose (delivery + composition root)")
    print("")
    print("  uxcompose create-app <dest> [--name NAME] [--level auto|0-3] [--host auto|fastapi|asgi]")
    print("  uxcompose serve [app:asgi] [--host 0.0.0.0] [--port 8080] [--reload]")
    print("  uxcompose doctor [paths...] [--no-fail]")
    print("")
    print("Product path: create-app → routes/ + build() → serve")
    print("Render-only tooling stays on uxdom (doctor/lint/build for pure Document).")


def _create_app(argv: list[str]) -> int:
    import argparse
    from ux_compose.scaffold import create_app

    p = argparse.ArgumentParser(prog="uxcompose create-app")
    p.add_argument("dest", help="Destination directory")
    p.add_argument("--name", default="myapp", help="App name")
    p.add_argument("--level", default="auto", help="Progressive level: auto or 0..3")
    p.add_argument(
        "--host",
        default="auto",
        choices=("auto", "fastapi", "asgi"),
        help="Gateway: auto | fastapi | asgi",
    )
    args = p.parse_args(argv)
    level: int | str
    if str(args.level).lower() == "auto":
        level = "auto"
    else:
        level = int(args.level)
    root = create_app(args.dest, name=args.name, level=level, host=args.host)
    print(f"Created progressive app at {root.resolve()} (level={args.level}, host={args.host})")
    print("  Composition root: ux_compose.build(host=, live=, level=)")
    print("  Product path: routes/ page unit + trees + className")
    print(f"  Next: cd {root} && python app.py")
    print("  Serve: uxcompose serve app:asgi --port 8080")
    print("  Doctor: uxcompose doctor .")
    return 0


def _serve(argv: list[str]) -> int:
    """Run product ASGI via uvicorn (composition-root delivery)."""
    import argparse

    p = argparse.ArgumentParser(prog="uxcompose serve")
    p.add_argument(
        "app",
        nargs="?",
        default="app:asgi",
        help="ASGI import path (default: app:asgi from create-app)",
    )
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--reload", action="store_true", help="Dev reload")
    p.add_argument("--no-reload", action="store_true", help="Disable reload")
    args = p.parse_args(argv)
    reload = bool(args.reload) and not args.no_reload
    if not args.reload and not args.no_reload:
        reload = True  # product default: dev-friendly

    try:
        import uvicorn
    except ImportError:
        print("uvicorn required: pip install uvicorn", file=sys.stderr)
        return 1

    print(f"uxcompose serve {args.app} on http://{args.host}:{args.port} (reload={reload})")
    uvicorn.run(args.app, host=args.host, port=args.port, reload=reload)
    return 0


def _doctor(argv: list[str]) -> int:
    import argparse
    from pathlib import Path
    from ux_compose.doctor import doctor

    p = argparse.ArgumentParser(prog="uxcompose doctor")
    p.add_argument("paths", nargs="*", default=["."], help="Paths to scan")
    p.add_argument("--no-fail", action="store_true", help="Report only")
    args = p.parse_args(argv)
    paths = [Path(x) for x in args.paths]
    report = doctor(paths, fail=not args.no_fail)
    print(report)
    return 0 if args.no_fail or getattr(report, "ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
