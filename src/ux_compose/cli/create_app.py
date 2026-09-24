"""``uxcompose create-app`` — argv for ``ux_compose.scaffold.create_app``."""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str]) -> int:
    from ux_compose.scaffold import ReservedDestError, create_app

    p = argparse.ArgumentParser(prog="uxcompose create-app")
    p.add_argument("dest", help="Destination directory")
    p.add_argument("--name", default="myapp")
    p.add_argument("--level", default="auto")
    p.add_argument("--host", default="auto", choices=("auto", "fastapi", "asgi"))
    p.add_argument(
        "--brand",
        default=None,
        help="GET-only nav brand via brand_wrap (Document path; not inside render())",
    )
    args = p.parse_args(argv)
    level: int | str = "auto" if str(args.level).lower() == "auto" else int(args.level)
    try:
        root = create_app(
            args.dest, name=args.name, level=level, host=args.host, brand=args.brand
        )
    except ReservedDestError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"Created {root.resolve()} (level={args.level}, host={args.host})")
    print(f"  Next: cd {root} && uxcompose serve dev")
    print("  Ship:  uxcompose build && uxcompose deploy --provider docker")
    return 0
