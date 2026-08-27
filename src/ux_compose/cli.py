"""uxcompose CLI — sole product lifecycle DX.

Hard ownership (SoC + locality):
  create-app · build · serve · deploy · doctor · add  →  here only
  Pure Document tooling stays on uxdom (lint / profile / add ui|component).
  Tailwind *compiler resolution* lives here (``ux_compose.tailwind``).
  ux-dom owns className, the Document ``<link>``, and package static.
  App asset folders live here (``ux_compose.assets.WebAssets``).

serve owns process reload, optional browser HMR, optional public tunnel.
"""
from __future__ import annotations

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
    print("  uxcompose build [--watch] [--no-minify] [--skip-tailwind] [--skip-import] [--app app:asgi]")
    print("  uxcompose serve [app:asgi] [--host 0.0.0.0] [--port 8080] [--reload|--no-reload]")
    print("                 [--hmr] [--watch PATH ...]" )
    print("                 [--tunnel none|ngrok|cloudflare] [--tunnel-token TOKEN]")
    print("  uxcompose deploy [--provider docker|fly|render|railway|vps|checklist] [--force] [--name NAME]")
    print("  uxcompose doctor [paths...] [--no-fail]")
    print("  uxcompose add [name] [--force] [--page]   # ownable kit copy (shadcn-style)")
    print("  uxcompose add --list")
    print("")
    print("Product path: create-app → build → serve → deploy")
    print("Kit copy: uxcompose add login  (drops components/login.py — you own it)")
    print("HMR / tunnel are delivery features of serve (not Document.use).")
    print("CSS minify: ux_compose.tailwind (finder + ensure). App folders: ux_compose.assets.")
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
    print(f"  Next: cd {root} && uxcompose build && uxcompose serve app:asgi")
    print("  Deploy: uxcompose deploy --provider docker")
    return 0


def _build(argv: list[str]) -> int:
    import argparse
    from ux_compose.cli_build import format_product_build_report, run_product_build

    p = argparse.ArgumentParser(prog="uxcompose build")
    p.add_argument("--watch", action="store_true", help="Tailwind --watch (XOR with minify)")
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
            watch=args.watch,
            app_ref=args.app,
        )
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(format_product_build_report(report))
    return 0 if report.ok else 1


def _load_asgi(app_ref: str):
    """Import ``module:attr`` ASGI app object."""
    if ":" not in app_ref:
        raise ValueError(f"ASGI path must be module:attr, got {app_ref!r}")
    mod_name, attr = app_ref.split(":", 1)
    import importlib

    mod = importlib.import_module(mod_name)
    obj = mod
    for part in attr.split("."):
        obj = getattr(obj, part)
    return obj


def _serve(argv: list[str]) -> int:
    import argparse
    from pathlib import Path

    p = argparse.ArgumentParser(prog="uxcompose serve")
    p.add_argument("app", nargs="?", default="app:asgi")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--reload", action="store_true")
    p.add_argument("--no-reload", action="store_true")
    p.add_argument("--hmr", action="store_true", default=False, help="Attach browser HMR websocket (needs --no-reload)")
    p.add_argument("--no-hmr", action="store_true", help="Disable browser HMR (default)")
    p.add_argument("--watch", action="append", default=None, help="Extra HMR watch path (repeatable)")
    p.add_argument(
        "--tunnel",
        default="none",
        help="Public tunnel after health green: none|ngrok|cloudflare",
    )
    p.add_argument("--tunnel-token", default=None)
    p.add_argument("--health-path", default="/")
    p.add_argument("--health-timeout", type=float, default=30.0)
    args = p.parse_args(argv)

    reload = True if not args.no_reload else False
    if args.reload:
        reload = True
    hmr = bool(args.hmr) and not args.no_hmr

    try:
        import uvicorn
    except ImportError:
        print("uvicorn required: pip install uvicorn", file=sys.stderr)
        return 1

    tunnel_handle = None
    asgi_obj = None
    run_target: str | object = args.app

    if hmr and not reload:
        # Need concrete app object to attach WS route; reload workers re-import
        try:
            asgi_obj = _load_asgi(args.app)
            from ux_compose.hmr import attach_hmr

            watch = list(args.watch or [])
            if not watch:
                watch = [".", "routes"]
            attach_hmr(asgi_obj, watch_paths=watch)
            run_target = asgi_obj
            print(f"HMR: websocket /__uxcompose/hmr watching {watch}")
        except Exception as exc:
            print(f"HMR attach skipped: {exc}", file=sys.stderr)
            run_target = args.app
    elif hmr and reload:
        print(
            "HMR: browser WS needs --no-reload to attach on this process; "
            "using uvicorn --reload only (process HMR).",
            file=sys.stderr,
        )

    # Tunnel after origin is up (background thread)
    from ux_compose.tunnel import parse_provider, start_tunnel, wait_for_health

    try:
        provider = parse_provider(args.tunnel)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    def _tunnel_worker() -> None:
        nonlocal tunnel_handle
        try:
            wait_for_health(
                args.port,
                host=args.host,
                path=args.health_path,
                timeout=args.health_timeout,
            )
            tunnel_handle = start_tunnel(
                provider, args.port, token=args.tunnel_token, host=args.host
            )
            if tunnel_handle:
                print(f"tunnel[{tunnel_handle.provider}]: {tunnel_handle.public_url}")
        except Exception as exc:
            print(f"tunnel failed: {exc}", file=sys.stderr)

    if provider != "none":
        threading.Thread(target=_tunnel_worker, name="uxcompose-tunnel", daemon=True).start()

    print(
        f"uxcompose serve {args.app} http://{args.host}:{args.port} "
        f"reload={reload} hmr={hmr and not reload} tunnel={provider}"
    )
    try:
        uvicorn.run(run_target, host=args.host, port=args.port, reload=reload and isinstance(run_target, str))
    finally:
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
