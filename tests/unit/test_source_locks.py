"""Source-level locks. Do not import ux_compose (sandbox 3.10 / no specialists)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"
DOCS = ROOT / "docs"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _fn(src: str, name: str) -> str:
    m = re.search(rf"^([ \t]*)def {re.escape(name)}\b", src, re.M)
    if not m:
        raise AssertionError(f"def {name} not found")
    indent = m.group(1)
    start = m.start()
    rest = src[m.end() :]
    nxt = re.search(rf"\n{re.escape(indent)}(?:def |class |@)", rest)
    end = m.end() + nxt.start() if nxt else len(src)
    return src[start:end]


def test_live_channel_swallows_importerror_only():
    src = _read("helpers.py")
    chunk = _fn(src, "_live_channel")
    assert "except ImportError" in chunk
    assert "except Exception" not in chunk
    assert "fail loud" in chunk
    assert "return None" in chunk


def test_attach_channel_secret_and_boot_fail_closed():
    src = _read("wire/boot.py")
    chunk = _fn(src, "attach_channel")
    assert "ChannelConfig(secret=secret)" in chunk
    assert "cfg = None" not in chunk
    assert "ch = None" not in chunk
    assert "fail closed" in chunk


def test_use_channel_stamps_l2_only_when_channel_exists():
    src = _read("app.py")
    chunk = _fn(src, "use_channel")
    stamp = "self._level = max(self._level, Level.L2)"
    assert stamp in chunk
    before, _, after = chunk.partition(stamp)
    assert "if ch is not None:" in before
    assert "register_live_channel(ch)" in after
    assert "except ImportError" in chunk
    assert 'self._note("use_channel", "L2", exc)' in chunk


def test_app_boot_keeps_attach_notes_on_channel_stepdown():
    src = _read("app.py")
    chunk = _fn(src, "boot")
    assert 'app._note("boot.use_channel", "L2", exc)' in chunk


def test_pypi_unclaimed_in_brand_tables():
    for rel in (ROOT / "README.md", DOCS / "README.md"):
        text = rel.read_text(encoding="utf-8")
        assert "**PyPI / pip**" not in text
        assert "not on PyPI" in text
    cli = _read("cli.py")
    assert "pip install -e '.[serve]'" in cli
    assert "pip install 'ux-compose[serve]'" not in cli
    assert 'pip install "ux-compose[serve]"' not in cli


def test_app_mount_is_scan_step_not_secondary_door():
    app_src = _read("app.py")
    assert "def mount(" in app_src
    leftover = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "secondary door" in leftover
    hits = []
    skip = {ROOT / "CHANGELOG.md", DOCS / "ARCHITECTURE.md"}
    for path in (
        list(ROOT.glob("*.md"))
        + list(DOCS.rglob("*.md"))
        + list((ROOT / "examples").rglob("*.py"))
        + list((ROOT / "src").rglob("*.py"))
        + [ROOT / "AGENTS.md"]
    ):
        if path.resolve() in {p.resolve() for p in skip}:
            continue
        text = path.read_text(encoding="utf-8")
        if "secondary door" in text.lower() or "secondary-door" in text.lower():
            hits.append(str(path.relative_to(ROOT)))
    assert hits == [], hits


def test_critic_names_fragment_walker_residual():
    critic = (ROOT / "CRITIC.md").read_text(encoding="utf-8")
    assert "homemade fragment walker" in critic
    assert "_fragment_for_target" in critic
    assert "PASS with residual" in critic
    helpers = _read("helpers.py")
    assert "def _fragment_for_target" in helpers
    assert "def _element_end" in helpers


def test_architecture_concern_table_is_the_module_map():
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "## Concern → file (lock)" in arch
    assert "Do **not** add `docs/MODULE_MAP.md`" in arch
    for owner in (
        "wire/boot.py",
        "wire/caps.py",
        "wire/cek.py",
        "cli.py",
        "routing/host.py",
        "routing/fastapi.py",
        "routing/asgi.py",
        "kit_construct.py",
        "serve_state.py",
        "dx/probe.py",
        "live_client.py",
        "hmr.py",
    ):
        assert owner in arch, owner
    assert not (DOCS / "MODULE_MAP.md").exists()
    index = (DOCS / "INDEX.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "MODULE_MAP.md" in index
    assert "MODULE_MAP.md" in agents
    assert "Concern→file" in index or "Concern → file" in arch


def test_architecture_owner_column_names_delivery_files():
    """MAP-2: concern table names delivery files. Still no MODULE_MAP.md."""
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    for owner in (
        "tunnel.py",
        "deploy.py",
        "serve_restart.py",
        "author.py",
        "progressive.py",
        "dom.py",
        "attach_notes.py",
    ):
        assert owner in arch, owner
    assert not (DOCS / "MODULE_MAP.md").exists()
    for rel in (
        "tunnel.py",
        "deploy.py",
        "serve_restart.py",
        "author.py",
        "progressive.py",
        "dom.py",
        "attach_notes.py",
    ):
        assert (SRC / rel).is_file(), rel


def test_folder_law_keeps_kit_construct_and_cli_at_package_root():
    """Folders are copy/isolation laws. Do not invent cli/ or kit/kit_construct."""
    assert (SRC / "kit_construct.py").is_file()
    assert not (SRC / "kit" / "kit_construct.py").exists()
    assert not (SRC / "cli").exists()
    assert not (SRC / "serve").exists()
    assert not (SRC / "services").exists()
    assert (SRC / "cli.py").is_file()
    assert (SRC / "cli_build.py").is_file()
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "## Folder law" in arch
    assert "Do **not** add `cli/`" in arch
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Folder law" in agents
    construct = _read("kit_construct.py")
    assert "Not under ``kit/``" in construct
    copy = _read("kit/copy.py")
    assert "kit_construct lives outside kit/" in copy


def test_on_disk_packages_are_mapped_not_ghosts():
    """Cut 3 / channel Cut 2 class: every package dir is on the concern table."""
    packages = sorted(
        p.name
        for p in SRC.iterdir()
        if p.is_dir() and (p / "__init__.py").is_file() and p.name != "__pycache__"
    )
    assert packages == ["dx", "kit", "routing", "wire"], packages
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    for name in packages:
        assert f"`{name}/`" in arch, name
    assert not (SRC / "cli").exists()
    assert not (SRC / "serve").exists()
    assert not (SRC / "services").exists()
    cli = _read("cli.py")
    serve = _read("serve_dev.py")
    assert "argv only" in cli or "argv ``create``" in cli
    assert "start_tailwind_watch" in serve
    assert "start_css_watcher:" not in serve
    assert "start_css_watcher=" in serve


def test_routing_adapters_path_absent_and_taught():
    adapters = SRC / "routing" / "adapters"
    assert not adapters.exists()
    src_hits = []
    for path in SRC.rglob("*.py"):
        if path.name == "doctor.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "routing.adapters" in text or "routing/adapters" in text:
            src_hits.append(str(path.relative_to(ROOT)))
    assert src_hits == [], src_hits
    doctor = _read("doctor.py")
    assert "ux_compose.routing.adapters" in doctor
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "`ux_compose.routing.adapters`" in arch


def test_create_argv_dropped_create_app_stays():
    cli = _read("cli.py")
    assert 'cmd in ("create-app", "create")' not in cli
    assert 'cmd == "create-app"' in cli
    assert "argv ``create`` is leftover" in cli
    help_fn = _fn(cli, "_help")
    assert "create-app" in help_fn
    assert "create |" not in help_fn and '", "create"' not in help_fn
    assert '"development": "dev"' not in cli
    assert '"production": "prod"' not in cli
    assert '"restart_channel": "restart-channel"' not in cli
    assert "argv ``development``" in cli
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "argv `create`" in arch
    assert "argv `development`" in arch


def _load_doctor():
    import importlib.util
    import sys

    path = SRC / "doctor.py"
    spec = importlib.util.spec_from_file_location("ux_compose_doctor_src", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_leftover_scan_has_no_first_token_break():
    chunk = _fn(_read("doctor.py"), "scan_leftover_aliases")
    assert "break" not in chunk
    import tempfile
    from pathlib import Path as P

    doctor = _load_doctor()
    with tempfile.TemporaryDirectory() as td:
        product = P(td) / "app.py"
        product.write_text(
            'build(PACKAGE, host="batteries")\nfrom leftover import DirectoryRouter\n',
            encoding="utf-8",
        )
        diags = doctor.scan_leftover_aliases([product])
        joined = "\n".join(diags)
        assert "batteries" in joined
        assert "DirectoryRouter" in joined
        assert len(diags) >= 2


def test_render_chrome_scan_has_no_first_hit_break():
    chunk = _fn(_read("doctor.py"), "scan_render_chrome")
    assert "break" not in chunk
    import tempfile
    from pathlib import Path as P

    doctor = _load_doctor()
    with tempfile.TemporaryDirectory() as td:
        product = P(td) / "routes" / "hello.py"
        product.parent.mkdir(parents=True)
        product.write_text(
            "class Hello:\n"
            "    def render(self):\n"
            "        return '<div id=\"stunning-root\">a</div>'\n"
            "class Other:\n"
            "    def render(self):\n"
            "        return '<nav class=\"nav\"><span class=\"brand\">Acme</span></nav>'\n",
            encoding="utf-8",
        )
        diags = doctor.scan_render_chrome([product])
        joined = "\n".join(diags)
        assert "stunning-root" in joined
        assert 'class="nav"' in joined
        assert len(diags) >= 2


def test_copy_keeps_kit_construct_library_import_lock():
    copy = _read("kit/copy.py")
    assert "kit_construct lives outside kit/" in copy
    assert r"from ux_compose\.kit_construct" not in copy
    for stem in ("fab.py", "dialog.py"):
        src = _read(f"kit/{stem}")
        assert "from ux_compose.kit_construct import" in src


def test_flow_citations_point_at_ownership():
    readme = (DOCS / "README.md").read_text(encoding="utf-8")
    assert "FLOW (ownership)" not in readme
    assert "START_HERE → OWNERSHIP" in readme
    matrix = (DOCS / "resilience" / "MATRIX.md").read_text(encoding="utf-8")
    assert "FLOW law on the compose surface" not in matrix
    assert "OWNERSHIP law on the compose surface" in matrix
    cli_build = _read("cli_build.py")
    assert "Ownership (FLOW law):" not in cli_build
    assert "Ownership (OWNERSHIP law):" in cli_build
    stub = (DOCS / "FLOW.md").read_text(encoding="utf-8")
    assert "# Moved" in stub
    assert "OWNERSHIP.md" in stub


def test_internals_ownership_is_moved_stub_lock():
    path = DOCS / "internals" / "OWNERSHIP.md"
    text = path.read_text(encoding="utf-8")
    assert "# Moved" in text
    assert "../OWNERSHIP.md" in text
    assert text.count("\n") <= 12
    assert "DirectoryRoutes + thin adapters" not in text
    assert "ux_compose.tailwind" not in text


def test_docs_start_here_is_not_a_second_cli_recipe():
    text = (DOCS / "START_HERE.md").read_text(encoding="utf-8")
    assert "uxcompose create-app" not in text
    contrib = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "in sync with the root START_HERE" not in contrib
    assert "not a second CLI recipe" in contrib


def test_makefile_has_no_ghost_property_suite():
    mk = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "tests/property" not in mk
    testing = (DOCS / "guides" / "TESTING.md").read_text(encoding="utf-8")
    assert "tests/property" not in testing
    assert not (ROOT / "tests" / "property").exists()
    contrib = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "load, property, security" not in contrib


def test_wire_boot_names_package_door():
    boot = _read("wire/boot.py")
    assert "ONLY place" not in boot
    assert "package door" in boot
    assert "boot.py, caps.py, cek.py" in boot
    assert (SRC / "wire" / "caps.py").is_file()
    assert (SRC / "wire" / "cek.py").is_file()


def test_unknown_host_fail_closed_lock():
    host = _read("routing/host.py")
    chunk = _fn(host, "open")
    assert 'want == "starlette"' not in chunk
    assert "unknown host" in chunk
    assert 'want not in ("auto", "fastapi", "asgi")' in chunk
    surfaces = _read("surfaces_host.py")
    assert '"starlette"' not in _fn(surfaces, "attach_page_router")
    spec = (DOCS / "reference" / "host.md").read_text(encoding="utf-8")
    assert "alias of `auto`" not in spec
    doctor = _read("doctor.py")
    assert 'host="starlette"' in doctor


def test_command_does_not_import_overlay_chrome():
    src = _read("kit/command.py")
    assert "from ux_compose.kit.overlay" not in src
    assert "overlay_chrome" not in src
    assert "def _chrome" not in src
    assert "click keydown.escape" in src
    overlay = _read("kit/overlay.py")
    doc = overlay.split('"""', 2)[1]
    assert "Command take ids" not in doc
    assert "does not import this" in doc
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "`kit/command.py` owns local" in arch
    assert "must not import" in arch


def test_live_client_does_not_synthesize_html_shell():
    src = _read("live_client.py")
    chunk = _fn(src, "insert_live_client")
    assert "<!DOCTYPE html>" not in chunk
    assert "return page" in chunk
    assert "synthesize a Document" in chunk
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "synthesized HTML shell for fragments" in arch


def test_css_watch_spawn_lives_in_tailwind():
    cli = _read("cli.py")
    tw = _read("tailwind.py")
    hmr = _read("hmr.py")
    assert "def start_tailwind_watch" in tw
    assert "def _start_tailwind_watch" not in cli
    serve = _read("serve_dev.py")
    assert "start_tailwind_watch" not in cli
    assert "start_tailwind_watch" in serve
    assert "start_css_watcher:" not in cli
    assert "start_css_watcher:" not in serve
    assert "start_css_watcher=" in cli
    assert "start_css_watcher=" in serve
    assert "subprocess.Popen" in tw
    assert "subprocess.Popen" not in cli
    assert "Popen" not in hmr
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "`tailwind.py` sibling Tailwind" in agents
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "Tailwind `Popen` in `cli.py`" in arch
    assert not (SRC / "cli").exists()


def test_catalog_scan_and_http_discover_are_two_walkers():
    """SURF-1: KEEP both walks. Stop teaching them as one implementation."""
    build = _read("build.py")
    assert "app.mount(" in build
    assert "bind_pages=False" in build
    assert "core.discover()" in build
    assert "Two walkers, one product door" in build
    surfaces = _read("surfaces.py")
    assert "def scan_surfaces(" in surfaces
    core = _read("routing/core.py")
    assert "def discover(" in core
    adr = (DOCS / "adr" / "0004-clarity-and-residuals.md").read_text(encoding="utf-8")
    assert "DirectoryRoutes.discover" in adr
    assert "one implementation, two callers" not in adr
    assert "Do not merge them" in adr
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "Two walkers, one product" in arch
    assert "fold `scan_surfaces` into `DirectoryRoutes.discover`" in arch
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Two" in agents and "walkers" in agents.lower()
    assert _read("app.py").count("def mount(") == 1
    assert "thin adapter" not in surfaces


def test_wire_imports_only_frozen_channel_paths():
    """Isolation Law: wire/ may import only Channel, ChannelConfig,
    apply_host_adapter, Intent. ActionRegistry is not a compose door."""
    import ast

    allowed = {
        ("ux_channel", ("Channel", "ChannelConfig")),
        ("ux_channel.cek.host_adapter", ("apply_host_adapter",)),
        ("ux_channel.protocol.types", ("Intent",)),
    }
    wire = SRC / "wire"
    for path in sorted(wire.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "ux_channel" or alias.name.startswith("ux_channel."):
                        raise AssertionError(
                            f"{path.name}: bare import {alias.name!r} — use frozen from-imports"
                        )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == "ux_channel" or mod.startswith("ux_channel."):
                    names = tuple(sorted(alias.name for alias in node.names))
                    assert (mod, names) in allowed or (
                        mod == "ux_channel" and set(names) <= {"Channel", "ChannelConfig"}
                    ), f"{path.name}: from {mod} import {', '.join(names)}"


def test_channel_health_formats_vs_codecs_documented():
    """Compose fronts Channel HTTP. Health formats (HTTP) ≠ codecs (library)."""
    spec = (DOCS / "reference" / "host.md").read_text(encoding="utf-8")
    assert "formats" in spec and "codecs" in spec
    assert "application/ux-channel+json" in spec or "HTTP today" in spec
    assert "/ux-channel/health" in spec


def test_store_precedence_docs_name_redis_wins():
    """Do not set UXCOMPOSE_STATE_STORE and REDIS_URL as if both were the session."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    hmr = (DOCS / "internals" / "hmr.md").read_text(encoding="utf-8")
    adr = (DOCS / "adr" / "0006-serve-dev-shared-store.md").read_text(encoding="utf-8")
    serve = _read("serve_state.py")
    serve_dev = _read("serve_dev.py")
    assert "REDIS_URL" in agents
    assert "prefers Redis" in agents or "Redis wins" in agents
    assert "REDIS_URL" in hmr
    assert "REDIS_URL" in serve
    assert "REDIS_URL" in serve_dev
    assert "will not export both" in adr
    assert "does not clear Redis" in adr
    assert "d0fe716" not in adr
    assert "15cb1ed" in adr
    doctor = _read("doctor.py")
    assert "scan_store_precedence" in doctor
    assert "diagnostics.extend(scan_store_precedence())" in doctor


def test_leftover_table_splits_doctor_tokens_from_agent_locks():
    """Doctor is not credited for names it does not scan in product trees."""
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "### Doctor leftover tokens" in arch
    assert "### Agent leftovers" in arch
    assert "Doctor flags these in product trees" not in arch
    assert "Doctor will not print these from `scan_leftover_aliases`" in arch
    doctor_src = _read("doctor.py")
    for token in (
        'host="batteries"',
        "DirectoryRouter",
        "ux_compose.routing.adapters",
        'host="starlette"',
        'serve="webassets"',
    ):
        assert token in doctor_src, token
    doctor_sec = arch.split("### Doctor leftover tokens")[1].split("### Agent leftovers")[0]
    agent_sec = arch.split("### Agent leftovers")[1]
    assert "`ux_compose.routing.adapters`" in doctor_sec
    assert '`host="starlette"`' in doctor_sec
    assert "argv `create`" in agent_sec
    assert "`src/ux_compose/cli/` package" in agent_sec
    assert "`kit/kit_construct.py`" in agent_sec
    assert "`docs/MODULE_MAP.md`" in agent_sec
    assert "argv `development`" in agent_sec
    assert "`start_css_watcher=`" in agent_sec
    assert "`src/ux_compose/serve/`" in agent_sec
    assert "Channel `ops/`" in agent_sec
    assert "argv `create`" not in doctor_sec
    assert "`src/ux_compose/cli/` package" not in doctor_sec
    assert "`start_css_watcher=`" not in doctor_sec
