"""``uxcompose add`` — argv for ``ux_compose.kit.copy``."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    from ux_compose.kit.catalog import list_components
    from ux_compose.kit.copy import KitCopyError, copy_component

    p = argparse.ArgumentParser(prog="uxcompose add")
    p.add_argument(
        "name",
        nargs="?",
        default=None,
        help="kit component to copy (omit with --list)",
    )
    p.add_argument("--list", action="store_true", help="list kit components")
    p.add_argument("--force", action="store_true", help="overwrite existing copy")
    p.add_argument(
        "--page",
        action="store_true",
        help="also write routes/{stem}.py so GET /{stem} hosts the card",
    )
    p.add_argument(
        "--root",
        default=None,
        help="app root (default: walk up from cwd for app.py + routes/)",
    )
    args = p.parse_args(argv)

    if args.list or not args.name:
        print("uxcompose kit (ownable copies — edit the dropped file)")
        for it in list_components():
            extras = []
            if it.get("css"):
                extras.append("css")
            if it.get("page"):
                extras.append("page")
            extra = f"  [{', '.join(extras)}]" if extras else ""
            print(f"  · {it['stem']:<12} {it['description']}{extra}")
        if not args.name:
            print("")
            print("  uxcompose add login")
            print("  uxcompose add login --page --force")
        return 0

    try:
        root = Path(args.root).resolve() if args.root else None
        written = copy_component(
            args.name, root=root, force=args.force, as_page=args.page
        )
    except KitCopyError as e:
        print(str(e), file=sys.stderr)
        return 1
    for label, path in written.items():
        if path is None:
            continue
        print(f"wrote {label}: {path}")
    print(
        "edit freely — this copy is yours. regenerate: uxcompose add "
        f"{args.name} --force"
    )
    return 0
