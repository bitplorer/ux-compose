"""uxcompose CLI — doctor, progressive guidance, and create-app scaffold."""
from __future__ import annotations

import sys
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        return _help()

    if argv[0] in ("doctor", "check"):
        return _doctor(argv[1:])

    if argv[0] in ("create-app", "new", "init"):
        return _create_app(argv[1:])

    if argv[0] in ("-h", "--help", "help"):
        return _help()

    print(f"Unknown command: {argv[0]}. Try `uxcompose doctor` or `uxcompose --help`.")
    return 1


def _help() -> int:
    print("uxcompose — progressive UX composition")
    print()
    print("Commands:")
    print("  uxcompose doctor [path ...] [--no-fail]")
    print("      Protective coach: Isolation scan, dual-Document heuristic,")
    print("      progressive capability report, and unlock teaching messages.")
    print()
    print("  uxcompose create-app <dir> [--name NAME] [--level N]")
    print("      Scaffold a progressive app at Level N (default 1).")
    print("      Emits routes/ page unit + app.mount (DirectoryRouter via RouterHooks).")
    print("      Code written at Level 1 remains correct when you unlock L2/L3.")
    print()
    print("  uxcompose --help")
    print()
    print("Progressive Superpower Contract: code written at Level 1 remains")
    print("correct and unchanged when you unlock Channel or Motion.")
    return 0


def _create_app(argv: list[str]) -> int:
    import argparse
    from pathlib import Path
    from ux_compose.scaffold import create_app

    p = argparse.ArgumentParser(prog="uxcompose create-app")
    p.add_argument("dest", nargs="?", default="myapp", help="Destination directory")
    p.add_argument("--name", default=None, help="App name (default: dir name)")
    p.add_argument("--level", type=int, default=1, choices=[0, 1, 2, 3], help="Progressive level")
    args = p.parse_args(argv)
    name = args.name or Path(args.dest).name
    root = create_app(args.dest, name=name, level=args.level)
    print(f"Created progressive app at {root.resolve()} (Level {args.level})")
    print("  Product path: routes/ page unit + app.mount (RouterHooks)")
    print("  Progressive Superpower: Level-1 code stays correct when you unlock L2/L3.")
    print(f"  Next: cd {root} && PYTHONPATH=../src python app.py")
    print("  Doctor: uxcompose doctor .")
    return 0


def _doctor(argv: list[str]) -> int:
    import argparse
    from pathlib import Path
    from ux_compose.doctor import doctor

    p = argparse.ArgumentParser(prog="uxcompose doctor")
    p.add_argument("paths", nargs="*", default=["."], help="Paths to scan")
    p.add_argument("--no-fail", action="store_true", help="Report only, never exit non-zero")
    args = p.parse_args(argv)
    paths = [Path(x) for x in args.paths]
    report = doctor(paths, fail=not args.no_fail)
    print(report)
    return 0 if (args.no_fail or not report.errors) else 1


if __name__ == "__main__":
    raise SystemExit(main())
