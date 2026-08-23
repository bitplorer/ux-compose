"""uxcompose CLI — sole product lifecycle DX.

Hard ownership (SoC + locality):
  create-app · serve · deploy · doctor  →  here only
  Pure Document tooling stays on uxdom (lint/build/profile).
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
    if cmd == "deploy":
        return _deploy(rest)
    if cmd == "doctor":
        return _doctor(rest)
    print(f"unknown command: {cmd}", file=sys.stderr)
    _help()
    return 2


def _help() -> None:
    print("uxcompose — product lifecycle (composition + delivery)")
    print("")
    print("  uxcompose create-app <dest> [--name NAME] [--level auto|0-3] [--host auto|fastapi|asgi]")
    print("  uxcompose serve [app:asgi] [--host 0.0.0.0] [--port 8080] [--reload|--no-reload]")
    print("  uxcompose deploy [--provider docker|fly|render|railway|vps|checklist] [--force] [--name NAME]")
    print("  uxcompose doctor [paths...] [--no-fail]")
    print("")
    print("Product path: create-app → serve → deploy")
    print("Render-only tooling: uxdom doctor|lint|build|profile")


def _create_app(argv: list[str]) -> int:
    import argparse
    from ux_compose.scaffold import create_app

    p = argparse.ArgumentParser(prog="uxcompose create-app")
    p.add_argument("dest", help="Destination directory")
    p.add_argument("--name", default="myapp")
    p.add_argument("--level", default="auto")
    p.add_argument("--host", default="auto", choices=("auto", "fastapi", "asgi"))
    args = p.parse_args(argv)
    level: int | str = "auto" if str(args.level).lower() == "auto" else int(args.level)
    root = create_app(args.dest, name=args.name, level=level, host=args.host)
    print(f"Created {root.resolve()} (level={args.level}, host={args.host})")
    print(f"  Next: cd {root} && uxcompose serve app:asgi")
    print("  Deploy: uxcompose deploy --provider docker")
    return 0


def _serve(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="uxcompose serve")
    p.add_argument("app", nargs="?", default="app:asgi")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--reload", action="store_true")
    p.add_argument("--no-reload", action="store_true")
    args = p.parse_args(argv)
    reload = True if not args.no_reload else False
    if args.reload:
        reload = True

    try:
        import uvicorn
    except ImportError:
        print("uvicorn required: pip install uvicorn", file=sys.stderr)
        return 1

    print(f"uxcompose serve {args.app} http://{args.host}:{args.port} reload={reload}")
    uvicorn.run(args.app, host=args.host, port=args.port, reload=reload)
    return 0


def _deploy(argv: list[str]) -> int:
    import argparse
    from ux_compose.deploy import format_deploy_result, prepare_deploy

    p = argparse.ArgumentParser(prog="uxcompose deploy")
    p.add_argument(
        "--provider",
        "-p",
        default="docker",
        choices=("docker", "fly", "render", "railway", "vps", "checklist"),
    )
    p.add_argument("--force", action="store_true")
    p.add_argument("--name", default=None)
    args = p.parse_args(argv)
    try:
        result = prepare_deploy(args.provider, force=args.force, app_name=args.name)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(format_deploy_result(result))
    return 0


def _doctor(argv: list[str]) -> int:
    import argparse
    from pathlib import Path
    from ux_compose.doctor import doctor

    p = argparse.ArgumentParser(prog="uxcompose doctor")
    p.add_argument("paths", nargs="*", default=["."])
    p.add_argument("--no-fail", action="store_true")
    args = p.parse_args(argv)
    report = doctor([Path(x) for x in args.paths], fail=not args.no_fail)
    print(report)
    return 0 if args.no_fail or getattr(report, "ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
