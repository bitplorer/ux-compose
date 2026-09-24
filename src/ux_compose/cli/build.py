"""``uxcompose build`` — argv for the CSS minify wrap.

This is not ``ux_compose.build`` (the composition orchestra). The wrap is
``product_build.py``, which calls ``ux_compose.tailwind``.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str]) -> int:
    from ux_compose.cli.product_build import (
        format_product_build_report,
        run_product_build,
    )

    p = argparse.ArgumentParser(prog="uxcompose build")
    p.add_argument("--no-minify", action="store_true", help="Skip --minify")
    p.add_argument("--skip-tailwind", action="store_true")
    p.add_argument("--skip-import", action="store_true")
    p.add_argument("--app", default="app:asgi", help="ASGI entry for the import check")
    args = p.parse_args(argv)
    try:
        report = run_product_build(
            skip_tailwind=args.skip_tailwind,
            skip_import=args.skip_import,
            minify=not args.no_minify,
            watch=False,
            app_ref=args.app,
        )
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(format_product_build_report(report))
    return 0 if report.ok else 1
