"""uxcompose CLI — doctor, progressive guidance, and create-app scaffold."""
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    if not argv or argv[0] in ("doctor", "check", "doc"):
        from ux_compose.doctor import main as doctor_main
        return doctor_main(argv[1:] if argv and argv[0] in ("doctor", "check", "doc") else argv)

    if argv[0] in ("create-app", "new", "init"):
        return _create_app(argv[1:])

    if argv[0] in ("--help", "-h", "help"):
        print("uxcompose — pure-Python progressive composition root")
        print()
        print("Commands:")
        print("  uxcompose doctor [path ...] [--no-fail]")
        print("      Protective coach: Isolation scan, dual-Document heuristic,")
        print("      progressive capability report, and unlock teaching messages.")
        print()
        print("  uxcompose create-app <dir> [--name NAME] [--level N]")
        print("      Scaffold a progressive app at Level N (default 1).")
        print("      Code written at Level 1 remains correct when you unlock L2/L3.")
        print()
        print("  uxcompose --help")
        print()
        print("Progressive Superpower Contract: code written at Level 1 remains")
        print("correct and unchanged when you unlock Channel or Motion.")
        return 0

    print(f"Unknown command: {argv[0]}. Try `uxcompose doctor` or `uxcompose --help`.")
    return 1


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
    print("  Progressive Superpower: Level-1 code stays correct when you unlock L2/L3.")
    print(f"  Next: cd {root} && PYTHONPATH=../src python app.py")
    print("  Doctor: uxcompose doctor .")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
