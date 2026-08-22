"""uxcompose CLI — create-app, doctor."""
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("uxcompose create-app <dest> [--name NAME] [--level auto|0-3] [--host auto|fastapi|asgi]")
        print("uxcompose doctor [paths...] [--no-fail]")
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd in ("create-app", "create"):
        return _create_app(rest)
    if cmd == "doctor":
        return _doctor(rest)
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


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
    print("  Serve: uvicorn app:asgi --port 8080")
    print("  Doctor: uxcompose doctor .")
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
