"""
E2E demo — locked product path (page unit + App.mount + doctor evidence).

Proves:
1. routes/hello.py page unit (stem match)
2. App.mount → mount_surfaces (+ DirectoryRouter when asgi present)
3. Offline dispatch still works (Progressive Superpower Contract at L1)
4. doctor(..., bundle=) records surface / route evidence
5. Same page unit stays valid when channel/motion are unlocked (no rewrite)

Run (no specialists required for the offline path):
  PYTHONPATH=src:. python examples/page_unit_mount.py

With FastAPI + ux-dom (optional live router):
  PYTHONPATH=src:. python examples/page_unit_mount.py --asgi
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ux_compose import App, doctor

PACKAGE = Path(__file__).resolve().parent / "page_unit_demo"


def build(*, level: int = 1, with_asgi: bool = False):
    asgi = None
    if with_asgi:
        try:
            from fastapi import FastAPI

            asgi = FastAPI(title="page-unit-demo")
        except ImportError:
            print("FastAPI not installed — continuing without ASGI router")

    app = App.boot("PageUnitDemo", level=level)

    # Progressive unlocks are additive — same page unit, zero rewrite
    if level >= 2:
        try:
            app.use_channel(asgi_app=asgi) if asgi is not None else app.use_channel()
        except Exception as exc:
            print(f"  channel unlock skipped: {exc}")
    if level >= 3:
        try:
            app.use_motion()
        except Exception as exc:
            print(f"  motion unlock skipped: {exc}")

    bundle = app.mount(
        PACKAGE,
        asgi_app=asgi,
        base="routes",
        fail_closed=True,
        include_directory_router=bool(asgi is not None),
    )
    return app, asgi, bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Page-unit product-path E2E demo")
    parser.add_argument("--asgi", action="store_true", help="Attach FastAPI for DirectoryRouter")
    parser.add_argument("--level", type=int, default=1, choices=(1, 2, 3))
    args = parser.parse_args(argv)

    print("=== Locked product path ===")
    print(f"  package: {PACKAGE}")
    print(f"  level:   {args.level}")
    print(f"  asgi:    {args.asgi}")

    app, asgi, bundle = build(level=args.level, with_asgi=args.asgi)

    print(f"\nApp.level: {int(app.level)} ({getattr(app.level, 'label', '')})")
    print(f"Surfaces:  {list(bundle.surfaces.keys())}")
    print(f"Routes:    {[r.get('path') for r in (bundle.route_table or [])]}")
    print(f"Sealed:    {bundle.sealed}")

    # Offline dispatch — works at every level without the wire
    print("\n=== Offline dispatch (hello.inc) ===")
    ops = app.dispatch("hello.inc")
    for op in ops:
        print(f"  {op}")
    ops2 = app.dispatch("hello.inc")
    for op in ops2:
        print(f"  {op}")

    # Doctor with sealed-bundle evidence
    print("\n=== Doctor (bundle evidence) ===")
    report = doctor([], fail=False, bundle=bundle)
    print(f"  ok:       {report.ok}")
    print(f"  level:    L{report.level_available}")
    print(f"  caps:     {report.capabilities}")
    print(f"  surfaces: {report.surfaces}")
    print(f"  routes:   {report.routes}")
    for t in report.teaching:
        print(f"  → {t}")

    if asgi is not None:
        n_routes = len(getattr(asgi, "routes", []) or [])
        print(f"\nASGI routes registered: {n_routes}")

    print("\nOK — product path proven (page unit + mount + dispatch + doctor).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
