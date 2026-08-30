"""uxcompose CLI — sole product lifecycle DX.

Hard ownership (SoC + locality):
  create-app · build · serve · deploy · doctor · add  →  here only
  Pure Document tooling stays on uxdom (lint / profile / add ui|component).
  Tailwind *compiler resolution* lives here (``ux_compose.tailwind``).
  ux-dom owns className, the Document ``<link>``, and package static.
  App asset folders live here (``ux_compose.assets.WebAssets``).

serve is two run modes plus one action, not a flag soup:
  ``uxcompose serve dev``              origin + ui worker + channel worker + CSS watch
  ``uxcompose serve prod``             clocks hard off (local prod-like run)
  ``uxcompose serve restart-channel``  one-shot Channel RAM drop in a running serve dev
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


def _add(argv: list[str]) -> int:
    import argparse
    from pathlib import Path

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
    print("edit freely — this copy is yours. regenerate: uxcompose add "
          f"{args.name} --force")
    return 0


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
    print(f"  Next: cd {root} && uxcompose serve dev")
    print("  Ship:  uxcompose build && uxcompose deploy --provider docker")
    return 0


def _build(argv: list[str]) -> int:
    import argparse
    from ux_compose.cli_build import format_product_build_report, run_product_build

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


def _start_tailwind_watch(*, cwd: str | None = None):
    """Sibling Tailwind --watch. Lives in serve, not in hmr.py.

    Returns a Popen or None. None is quiet when the tree has no input.css.
    Missing CLI is a warning, not a failed serve.
    """
    import subprocess
    from pathlib import Path

    from ux_compose.tailwind import argv_with_io, discover_css_io, resolve_tailwind

    root = Path(cwd or ".").resolve()
    io = discover_css_io(root)
    if io is None:
        return None
    input_css, output_css = io
    hit = resolve_tailwind(cwd=root, ensure=False)
    if hit is None:
        print(
            "CSS: Tailwind CLI not found — skip sibling --watch "
            "(pip install pytailwindcss, or run uxcompose build)",
            file=sys.stderr,
        )
        return None
    output_css.parent.mkdir(parents=True, exist_ok=True)
    cmd = argv_with_io(
        hit.argv,
        input_css=input_css,
        output_css=output_css,
        minify=False,
        watch=True,
    )
    cmd = [("--watch=always" if part == "--watch" else part) for part in cmd]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(root), env.get("PYTHONPATH", "")])
    env["UXDOM_TAILWIND_OWNED"] = "1"
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(root), env=env, stdin=subprocess.DEVNULL
        )
    except OSError as exc:
        print(f"CSS: sibling --watch spawn failed: {exc}", file=sys.stderr)
        return None
    print(f"CSS: tailwind --watch ({hit.source}) → {output_css}")
    return proc


def _stop_proc(proc) -> None:
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()


def _missing_serve_dev_extras() -> list[str]:
    """Packages origin needs. Missing → fail closed, no second architecture."""
    missing: list[str] = []
    for name in ("httpx", "starlette", "websockets"):
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    return missing


_SERVE_MODES = {
    "dev": "dev",
    "development": "dev",
    "prod": "prod",
    "production": "prod",
    "restart-channel": "restart-channel",
    "restart_channel": "restart-channel",
}


def _serve_help() -> None:
    print("uxcompose serve needs a mode — clocks are not flags")
    print("")
    print("  uxcompose serve dev  [app:asgi] [--host 0.0.0.0] [--port 8080]")
    print("                      [--reload-dir PATH ...] [--tunnel none|ngrok|cloudflare]")
    print("  uxcompose serve prod [app:asgi] [--host 0.0.0.0] [--port 8080]")
    print("  uxcompose serve restart-channel")
    print("")
    print("  dev              origin + ui worker + channel worker + CSS watch")
    print("  prod             clocks hard off (local prod-like run; deploy still uses uvicorn)")
    print("  restart-channel  one-shot: drop Channel RAM in a running serve dev")


def _serve(argv: list[str]) -> int:
    import argparse

    if not argv or argv[0] in ("-h", "--help"):
        _serve_help()
        return 0 if argv else 2
    raw = argv[0].lower()
    if raw not in _SERVE_MODES:
        print(
            f"unknown serve mode {argv[0]!r} — use 'dev', 'prod', or 'restart-channel'",
            file=sys.stderr,
        )
        _serve_help()
        return 2
    mode = _SERVE_MODES[raw]
    rest = argv[1:]

    if mode == "restart-channel":
        if rest and rest[0] in ("-h", "--help"):
            print("uxcompose serve restart-channel")
            print("  one-shot Channel RAM drop for a running serve dev in this directory")
            print("  does not change the next *.py save")
            return 0
        if rest:
            print(
                "serve restart-channel does not accept "
                + " ".join(rest)
                + " — it is a one-shot action, not a flag",
                file=sys.stderr,
            )
            return 2
        from ux_compose.serve_restart import restart_channel

        return restart_channel()

    p = argparse.ArgumentParser(prog=f"uxcompose serve {mode}", add_help=True)
    p.add_argument("app", nargs="?", default="app:asgi")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    if mode == "dev":
        p.add_argument(
            "--reload-dir",
            action="append",
            default=None,
            dest="reload_dir",
            help="uvicorn reload dir (repeatable; default . and routes)",
        )
        p.add_argument(
            "--tunnel",
            default="none",
            help="Public tunnel after health green: none|ngrok|cloudflare",
        )
        p.add_argument("--tunnel-token", default=None)
        p.add_argument("--health-path", default="/")
        p.add_argument("--health-timeout", type=float, default=30.0)
    args, unknown = p.parse_known_args(rest)
    if unknown:
        print(
            f"uxcompose serve {mode} does not accept {' '.join(unknown)}",
            file=sys.stderr,
        )
        if mode == "prod":
            print("clocks live on 'serve dev', not flags on prod", file=sys.stderr)
        return 2

    css_watch = mode == "dev"
    tunnel_value = getattr(args, "tunnel", "none")
    tunnel_token = getattr(args, "tunnel_token", None)
    health_path = getattr(args, "health_path", "/")
    health_timeout = getattr(args, "health_timeout", 30.0)
    reload_dirs = list(getattr(args, "reload_dir", None) or [])
    if not reload_dirs:
        reload_dirs = [".", "routes"]

    try:
        import uvicorn
    except ImportError:
        print("uvicorn required: pip install uvicorn", file=sys.stderr)
        return 1

    from ux_compose.tunnel import parse_provider, start_tunnel, wait_for_health

    try:
        provider = parse_provider(tunnel_value)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    tunnel_handle = None
    css_proc = _start_tailwind_watch() if css_watch else None

    def _tunnel_worker() -> None:
        nonlocal tunnel_handle
        try:
            wait_for_health(
                args.port,
                host=args.host,
                path=health_path,
                timeout=health_timeout,
            )
            tunnel_handle = start_tunnel(
                provider, args.port, token=tunnel_token, host=args.host
            )
            if tunnel_handle:
                print(f"tunnel[{tunnel_handle.provider}]: {tunnel_handle.public_url}")
        except Exception as exc:
            print(f"tunnel failed: {exc}", file=sys.stderr)

    if mode == "dev":
        missing = _missing_serve_dev_extras()
        if missing:
            print(
                "serve dev needs "
                + ", ".join(missing)
                + " — pip install 'ux-compose[serve]'",
                file=sys.stderr,
            )
            _stop_proc(css_proc)
            return 1
        from ux_compose.serve_dev import run as run_serve_dev

        print(
            f"uxcompose serve dev {args.app} http://{args.host}:{args.port} "
            f"origin+ui+channel css_watch={css_proc is not None} tunnel={provider}"
        )
        if provider != "none":
            threading.Thread(target=_tunnel_worker, name="uxcompose-tunnel", daemon=True).start()
        try:
            return run_serve_dev(
                app_ref=args.app,
                host=args.host,
                port=args.port,
                reload_dirs=reload_dirs,
                start_css_watcher=None,
            )
        finally:
            _stop_proc(css_proc)
            if tunnel_handle is not None:
                tunnel_handle.close()

    print(
        f"uxcompose serve prod {args.app} http://{args.host}:{args.port} "
        f"clocks=off tunnel={provider}"
    )
    if provider != "none":
        threading.Thread(target=_tunnel_worker, name="uxcompose-tunnel", daemon=True).start()
    try:
        uvicorn.run(args.app, host=args.host, port=args.port)
    finally:
        _stop_proc(css_proc)
        if tunnel_handle is not None:
            tunnel_handle.close()
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
    from ux_compose.doctor import main as doctor_main

    return doctor_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
