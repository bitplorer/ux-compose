"""uxcompose CLI — sole product lifecycle DX.

Hard ownership (SoC + locality):
  create-app · build · serve · deploy · doctor · add  →  here only
  Pure Document tooling stays on uxdom (lint / profile / add ui|component).
  Tailwind *compiler resolution* lives here (``ux_compose.tailwind``).
  ux-dom owns className, the Document ``<link>``, and package static.
  App asset folders live here (``ux_compose.assets.WebAssets``).

serve is two modes, not a flag soup:
  ``uxcompose serve dev``   reload + HMR + sibling Tailwind --watch
  ``uxcompose serve prod``  clocks hard off (local prod-like run)
deploy still starts raw uvicorn — it does not call serve.
"""
from __future__ import annotations

import os
import sys
import threading


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        _help()
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd in ("create-app", "create"):
        return _create_app(rest)
    if cmd == "build":
        return _build(rest)
    if cmd == "serve":
        return _serve(rest)
    if cmd == "deploy":
        return _deploy(rest)
    if cmd == "doctor":
        return _doctor(rest)
    if cmd == "add":
        return _add(rest)
    print(f"unknown command: {cmd}", file=sys.stderr)
    _help()
    return 2


def _help() -> None:
    print("uxcompose — product lifecycle (composition + delivery)")
    print("")
    print("  uxcompose create-app <dest> [--name NAME] [--level auto|0-3] [--host auto|fastapi|asgi]")
    print("  uxcompose serve dev  [app:asgi] [--host 0.0.0.0] [--port 8080]")
    print("                      [--reload-dir PATH ...] [--tunnel none|ngrok|cloudflare]")
    print("  uxcompose serve prod [app:asgi] [--host 0.0.0.0] [--port 8080]")
    print("  uxcompose build [--no-minify] [--skip-tailwind] [--skip-import] [--app app:asgi]")
    print("  uxcompose deploy [--provider docker|fly|render|railway|vps|checklist] [--force] [--name NAME]")
    print("  uxcompose doctor [paths...] [--no-fail]")
    print("  uxcompose add [name] [--force] [--page]   # ownable kit copy (shadcn-style)")
    print("  uxcompose add --list")
    print("")
    print("Product path: create-app → serve dev → build → deploy")
    print("  serve dev  = reload + HMR + CSS watch (no clock flags to forget)")
    print("  serve prod = clocks hard off (does not replace deploy)")
    print("Kit copy: uxcompose add login  (drops components/login.py — you own it)")
    print("HMR / tunnel are delivery features of serve dev (not Document.use).")
    print("CSS minify: uxcompose build. App folders: ux_compose.assets.")
    print("Markup kit: uxdom add ui Button. Product Components: uxcompose add login")
