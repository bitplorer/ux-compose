"""uxcompose CLI — argv dispatch only.

Hard ownership (SoC + locality):
  create-app · build · serve · deploy · doctor · add  →  command modules here
  argv ``create`` is leftover — use ``create-app``.
  argv ``development`` / ``production`` / ``restart_channel`` are leftover —
  use ``dev`` / ``prod`` / ``restart-channel``.
  ``cli/__init__.py`` is argv only. Clock bodies (sibling Tailwind ``--watch``,
  tunnel) live in ``cli/serve_dev.py``. Leftover ``start_css_watcher=`` is gone.
  Pure Document tooling stays on uxdom (lint / profile / add ui|component).
  Tailwind *compiler resolution* lives in ``ux_compose.tailwind``.
  ux-dom owns className, the Document ``<link>``, and package static.
  App asset folders live in ``ux_compose.assets.WebAssets``.

Library modules do not import ``ux_compose.cli``.
``doctor.py``, ``build.py``, ``scaffold.py``, and ``tailwind.py`` stay at the
package root — they are library, not this layer.

serve is two run modes plus one action, not a flag soup:
  ``uxcompose serve dev``              origin + ui worker + channel worker + CSS watch
  ``uxcompose serve prod``             clocks hard off (local prod-like run)
  ``uxcompose serve restart-channel``  one-shot Channel RAM drop in a running serve dev
deploy still starts raw uvicorn — it does not call serve.
"""
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        _help()
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "create-app":
        from ux_compose.cli.create_app import main as run

        return run(rest)
    if cmd == "build":
        from ux_compose.cli.build import main as run

        return run(rest)
    if cmd == "serve":
        from ux_compose.cli.serve import main as run

        return run(rest)
    if cmd == "deploy":
        from ux_compose.cli.deploy import main as run

        return run(rest)
    if cmd == "doctor":
        from ux_compose.cli.doctor import main as run

        return run(rest)
    if cmd == "add":
        from ux_compose.cli.add import main as run

        return run(rest)
    print(f"unknown command: {cmd}", file=sys.stderr)
    _help()
    return 2


def _help() -> None:
    print("uxcompose — product lifecycle (composition + delivery)")
    print("")
    print("  uxcompose create-app <dest> [--name NAME] [--level auto|0-3] [--host auto|fastapi|asgi] [--brand LABEL]")
    print("  uxcompose serve dev  [app:asgi] [--host 0.0.0.0] [--port 8080]")
    print("                      [--reload-dir PATH ...] [--tunnel none|ngrok|cloudflare]")
    print("  uxcompose serve prod [app:asgi] [--host 0.0.0.0] [--port 8080]")
    print("  uxcompose serve restart-channel   # one-shot Channel RAM drop (running serve dev)")
    print("  uxcompose build [--no-minify] [--skip-tailwind] [--skip-import] [--app app:asgi]")
    print("  uxcompose deploy [--provider docker|fly|render|railway|vps|checklist] [--force] [--name NAME]")
    print("  uxcompose doctor [paths...] [--no-fail]")
    print("  uxcompose add [name] [--force] [--page]   # ownable kit copy (shadcn-style)")
    print("  uxcompose add --list")
    print("")
    print("Product path: create-app → serve dev → build → deploy")
    print("  serve dev  = origin + ui reload + channel + CSS watch")
    print("  serve prod = clocks hard off (does not replace deploy)")
    print("  restart-channel = drop Channel RAM once; next *.py save still leaves Channel up")
    print("Kit copy: uxcompose add login  (drops components/login.py — you own it)")
    print("HMR / tunnel are delivery features of serve dev (not Document.use).")
    print("CSS minify: uxcompose build (ux_compose.tailwind). App folders: ux_compose.assets.")
    print("Markup kit: uxdom add ui Button. Product Components: uxcompose add login")


if __name__ == "__main__":
    raise SystemExit(main())
