"""Source-level locks. Do not import ux_compose (sandbox 3.10 / no specialists)."""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

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
    assert "if ch is None:" in before
    assert "no channel" in before
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
    cli = _read("cli/serve.py")
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
    assert "def _open_tag_id" in helpers


def test_fragment_walker_escape_prefers_dom_extract():
    """C2 Soft USE: prefer ux-dom extract_by_id; homemade walker is escape.

    Cite ux-dom#19/#20 and compose#80 C2. ``Fragment`` is a tree shell.
    ``parse_html`` / ``defHTML`` are ingest. CTO FullShellHello ``render()``
    is an HTML string, so ``dom_tag.get(id=)`` is not the morph path.
    Deleting the escape drops fragment-law when the owner symbol is
    absent. Not a second serialize. No ``fragment.py``.
    """
    helpers = _read("helpers.py")
    assert "from ux_compose.dom import TrustedHtml, html_text" in helpers
    assert "from ux_dom.response import to_html_bytes" in _read("dom.py")
    assert "extract_by_id" in helpers
    assert "No homemade HTML-string renderer" in helpers
    assert "escape" in helpers.lower()
    assert "No ``fragment.py``" in helpers or "No `fragment.py`" in helpers
    chunk = _fn(helpers, "_fragment_for_target")
    assert "_owner_extract_by_id" in chunk or "extract_by_id" in chunk
    assert "tokenize_html" not in helpers
    assert "defHTML" not in helpers
    assert "parse_html" not in helpers
    assert not (SRC / "fragment.py").exists()
    assert not (SRC / "helpers").exists()
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "_fragment_for_target" in agents
    assert "fragment.py" in agents
    assert "extract_by_id" in agents
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "extract_by_id" in arch
    assert "escape" in arch
    assert "to_html_bytes" in arch
    assert "KEEP until ux-dom owns extract" not in arch
    adr4 = (DOCS / "adr" / "0004-clarity-and-residuals.md").read_text(encoding="utf-8")
    assert "_fragment_for_target" in adr4
    assert "fragment.py" in adr4
    assert "extract_by_id" in adr4


def test_architecture_concern_table_is_the_module_map():
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "## Concern → file (lock)" in arch
    assert "Do **not** add `docs/MODULE_MAP.md`" in arch
    for owner in (
        "wire/boot.py",
        "wire/caps.py",
        "wire/cek.py",
        "cli/__init__.py",
        "routing/host.py",
        "routing/fastapi.py",
        "routing/asgi.py",
        "arrange.py",
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
        "cli/tunnel.py",
        "cli/deploy.py",
        "cli/serve_restart.py",
        "author.py",
        "progressive.py",
        "dom.py",
        "attach_notes.py",
    ):
        assert (SRC / rel).is_file(), rel


_CLI = "ux_compose.cli"


def _is_cli(name: str) -> bool:
    return name == _CLI or name.startswith(_CLI + ".")


def _cli_imports(source: str, rel_parts: tuple[str, ...]) -> list[str]:
    """Every way ``source`` (at ``SRC/<rel_parts>``) pulls in ``ux_compose.cli``.

    Covers absolute and relative imports (``node.level`` resolved against the
    file's package), ``from ux_compose import cli``, and
    ``importlib.import_module`` / ``__import__`` calls with a constant string.
    Docstrings and comments are prose, not imports, and are ignored.
    """
    package = ["ux_compose", *rel_parts[:-1]]
    hits: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            hits += [a.name for a in node.names if _is_cli(a.name)]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                keep = len(package) - (node.level - 1)
                base = package[:keep] if keep > 0 else []
                parts = base + (node.module.split(".") if node.module else [])
            else:
                parts = node.module.split(".")
            mod = ".".join(parts)
            if _is_cli(mod):
                hits.append(mod)
                continue
            hits += [f"{mod}.{a.name}" for a in node.names if _is_cli(f"{mod}.{a.name}")]
        elif isinstance(node, ast.Call) and node.args:
            func = node.func
            fname = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            arg = node.args[0]
            if (
                fname in {"import_module", "__import__"}
                and isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
            ):
                target = arg.value
                if target.startswith(".") and fname == "import_module":
                    pkg_node = node.args[1] if len(node.args) > 1 else next(
                        (k.value for k in node.keywords if k.arg == "package"), None
                    )
                    pkg = (
                        pkg_node.value
                        if isinstance(pkg_node, ast.Constant) and isinstance(pkg_node.value, str)
                        else ".".join(package)
                    )
                    dots = len(target) - len(target.lstrip("."))
                    base = pkg.split(".")[: len(pkg.split(".")) - (dots - 1)]
                    target = ".".join(base + [target.lstrip(".")])
                if _is_cli(target):
                    hits.append(target)
                elif fname == "__import__":
                    # __import__("ux_compose", fromlist=["cli"]) == from ux_compose import cli
                    fl = node.args[3] if len(node.args) > 3 else next(
                        (k.value for k in node.keywords if k.arg == "fromlist"), None
                    )
                    if isinstance(fl, (ast.List, ast.Tuple)):
                        for elt in fl.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                full = f"{target}.{elt.value}"
                                if _is_cli(full):
                                    hits.append(full)
    return hits


# The base allow-listed kit/catalog.py and kit/copy.py (cli re-export shims).
# This branch deleted kit/ and kit_construct.py; helpers live in arrange.py.
# An allow-list entry for a missing file would hide a reintroduction, so the
# set stays empty and those paths are locked absent below.
RUNTIME_ALLOWED: set[str] = set()


def test_folder_law_components_canonical_no_cli_imports():
    """components/ is canonical (Q13); arrange is a library import; kit/ and
    kit_construct are gone. CLI is the cli/ package, not the root."""
    assert (SRC / "components" / "__init__.py").is_file()
    assert (SRC / "arrange.py").is_file()
    assert not (SRC / "kit_construct.py").exists()
    assert list((SRC / "kit").rglob("*.py")) == []  # *.py: a stale empty dir is not kit
    for rel in ("kit/catalog.py", "kit/copy.py"):
        assert not (SRC / rel).exists(), rel
    assert (SRC / "cli" / "__init__.py").is_file()
    assert not (SRC / "cli.py").exists()
    assert not (SRC / "cli_build.py").exists()
    assert not (SRC / "serve_dev.py").exists()
    assert not (SRC / "serve").exists()
    assert not (SRC / "services").exists()
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "## Folder law" in arch
    assert "Library modules do not import `ux_compose.cli`" in arch
    assert "Do **not** add `cli/`" not in arch
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Folder law" in agents
    copy = _read("cli/copy_component.py")
    assert "Widget helpers live in ``ux_compose.arrange``" in copy
    for rel in RUNTIME_ALLOWED:
        assert (SRC / rel).is_file(), f"stale allow-list entry {rel}"
    offenders = {}
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC)
        if rel.parts[0] == "cli" or rel.as_posix() in RUNTIME_ALLOWED:
            continue
        hits = _cli_imports(path.read_text(encoding="utf-8"), rel.parts)
        if hits:
            offenders[rel.as_posix()] = hits
    assert offenders == {}, offenders


def test_on_disk_packages_are_mapped_not_ghosts():
    """Cut 3 / channel Cut 2 class: every package dir is on the concern table."""
    packages = sorted(
        p.name
        for p in SRC.iterdir()
        if p.is_dir() and (p / "__init__.py").is_file() and p.name != "__pycache__"
    )
    assert packages == ["cli", "components", "dx", "routing", "wire"], packages
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    for name in packages:
        assert f"`{name}/`" in arch, name
    assert not (SRC / "cli.py").exists()
    assert not (SRC / "serve").exists()
    assert not (SRC / "services").exists()
    cli = _read("cli/__init__.py")
    serve = _read("cli/serve_dev.py")
    assert "argv only" in cli
    assert "start_tailwind_watch" in serve
    assert "start_css_watcher" not in serve


def test_routing_adapters_path_absent():
    adapters = SRC / "routing" / "adapters"
    assert not adapters.exists()
    src_hits = []
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "routing.adapters" in text or "routing/adapters" in text:
            src_hits.append(str(path.relative_to(ROOT)))
    assert src_hits == [], src_hits


def test_create_argv_dropped_create_app_stays():
    cli = _read("cli/__init__.py")
    assert 'cmd in ("create-app", "create")' not in cli
    assert 'cmd == "create-app"' in cli
    help_fn = _fn(cli, "_help")
    assert "create-app" in help_fn
    assert "create |" not in help_fn and '", "create"' not in help_fn
    assert '"development": "dev"' not in cli
    assert '"production": "prod"' not in cli
    assert '"restart_channel": "restart-channel"' not in cli
    from ux_compose.cli import main

    assert main(["create", "x"]) == 2


def _load_doctor():
    import importlib.util
    import sys

    path = SRC / "doctor.py"
    spec = importlib.util.spec_from_file_location("ux_compose_doctor_src", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


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


def test_copy_keeps_arrange_library_import_lock():
    copy = _read("cli/copy_component.py")
    assert "Widget helpers live in ``ux_compose.arrange``" in copy
    assert r"from ux_compose\.arrange" not in copy
    for stem in ("fab.py", "dialog.py"):
        src = _read(f"components/{stem}")
        assert "from ux_compose.arrange import" in src


def test_flow_citations_point_at_ownership():
    readme = (DOCS / "README.md").read_text(encoding="utf-8")
    assert "FLOW (ownership)" not in readme
    assert "START_HERE → OWNERSHIP" in readme
    matrix = (DOCS / "resilience" / "MATRIX.md").read_text(encoding="utf-8")
    assert "FLOW law on the compose surface" not in matrix
    assert "OWNERSHIP law on the compose surface" in matrix
    cli_build = _read("cli/product_build.py")
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


def test_command_does_not_import_overlay_chrome():
    src = _read("components/command.py")
    assert "from ux_compose.components.overlay" not in src
    assert "overlay_chrome" not in src
    assert "def _chrome" not in src
    assert "click keydown.escape" in src
    overlay = _read("components/overlay.py")
    doc = overlay.split('"""', 2)[1]
    assert "Command take ids" not in doc
    assert "does not import this" in doc
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "`components/command.py` owns local" in arch
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
    cli = _read("cli/__init__.py")
    tw = _read("tailwind.py")
    hmr = _read("hmr.py")
    assert "def start_tailwind_watch" in tw
    assert "def _start_tailwind_watch" not in cli
    serve = _read("cli/serve_dev.py")
    assert "start_tailwind_watch" not in cli
    assert "start_tailwind_watch" in serve
    assert "start_css_watcher" not in cli
    assert "start_css_watcher" not in serve
    assert "subprocess.Popen" in tw
    assert "subprocess.Popen" not in cli
    assert "Popen" not in hmr
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "`tailwind.py` sibling Tailwind" in agents
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "Tailwind `Popen` in `cli/`" in arch
    assert not (SRC / "cli.py").exists()
    assert (SRC / "cli" / "__init__.py").is_file()


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
    """Isolation Law: wire/ may import only Channel, ChannelConfig, Principal
    (the visitor as Channel caller), apply_host_adapter, Intent.
    ActionRegistry is not a compose door."""
    import ast

    allowed = {
        ("ux_channel", ("Channel", "ChannelConfig")),
        ("ux_channel", ("Principal",)),
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
    serve = _read("cli/serve_state.py")
    serve_dev = _read("cli/serve_dev.py")
    assert "REDIS_URL" in agents
    assert "prefers Redis" in agents or "Redis wins" in agents
    assert "REDIS_URL" in hmr
    assert "REDIS_URL" in serve
    assert "REDIS_URL" in serve_dev
    assert "will not export both" in adr
    assert "does not clear Redis" in adr
    assert "d0fe716" not in adr
    assert "985e58a" in adr
    doctor = _read("doctor.py")
    assert "scan_store_precedence" in doctor
    assert "diagnostics.extend(scan_store_precedence())" in doctor


def test_encyclopedia_teaches_cut3_leftovers():
    """Cut 4: encyclopedia names leftover dual doors instead of teaching them live."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    start = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
    cli = (DOCS / "guides" / "CLI.md").read_text(encoding="utf-8")
    own = (DOCS / "OWNERSHIP.md").read_text(encoding="utf-8")
    adr4 = (DOCS / "adr" / "0004-clarity-and-residuals.md").read_text(encoding="utf-8")
    host = (DOCS / "reference" / "host.md").read_text(encoding="utf-8")
    contrib = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "serve_dev.py" in agents
    assert "985e58a" in agents
    assert "Channel.boot" in agents
    assert "serve_dev.py" in start
    assert "argv only" in cli
    for doc in (agents, start, cli, own):
        assert "start_css_watcher" not in doc
    assert "Channel.attach(asgi)" not in own
    assert "Channel.boot" in own
    assert "serve_dev.py" in own
    assert "do not raise when a specialist is absent" not in adr4
    assert "fail loud" in adr4
    assert "start_css_watcher" not in adr4
    assert "_fragment_for_target" in adr4
    assert "authors import `build()`" in host
    assert "Channel.boot" in host
    assert "985e58a" in host
    assert "uxcompose serve apps.pulse" not in contrib
    assert "serve dev apps.pulse.server:app" in contrib


@pytest.mark.parametrize(
    "source, rel_parts, caught",
    [
        ("from ux_compose.cli import x", ("app.py",), True),
        ("import ux_compose.cli.serve", ("app.py",), True),
        ("def f():\n    from ux_compose.cli import x", ("app.py",), True),
        ("from ux_compose import cli", ("app.py",), True),
        ("from ..cli import serve", ("routing", "core.py"), True),
        ("from . import cli", ("app.py",), True),
        ("from .cli.serve import x", ("app.py",), True),
        ("import importlib\nimportlib.import_module('ux_compose.cli')", ("app.py",), True),
        ("from importlib import import_module\nimport_module('ux_compose.cli.registry')", ("app.py",), True),
        ("__import__('ux_compose.cli')", ("app.py",), True),
        ("import importlib\nimportlib.import_module('.cli', package='ux_compose')", ("app.py",), True),
        ("import importlib\nimportlib.import_module('.cli', 'ux_compose')", ("routing", "x.py"), True),
        ("import importlib\nimportlib.import_module('.serve', 'ux_compose.cli')", ("routing", "x.py"), True),
        ("__import__('ux_compose', fromlist=['cli'])", ("app.py",), True),
        ("__import__('ux_compose', None, None, ('cli',))", ("app.py",), True),
        ("__import__('ux_compose.cli', fromlist=['serve'])", ("app.py",), True),
        ("__import__('ux_compose', fromlist=['components'])", ("app.py",), False),
        ("import importlib\nimportlib.import_module('.routing', 'ux_compose')", ("app.py",), False),
        ('"""See ux_compose.cli for the CLI."""', ("app.py",), False),
        ("from ux_compose import components", ("app.py",), False),
        ("from . import arrange", ("app.py",), False),
        ("from ..routing import core", ("components", "tabs.py"), False),
        ("import ux_compose.client", ("app.py",), False),
    ],
)
def test_cli_import_detector_catches_every_form(source, rel_parts, caught):
    assert bool(_cli_imports(source, rel_parts)) is caught


_RUNTIME_GUARD = r"""
import importlib, importlib.abc, json, pathlib, sys

ATTEMPTS = []  # recorded before raising, so a swallowed ImportError still counts

class _BlockCli(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name == "ux_compose.cli" or name.startswith("ux_compose.cli."):
            ATTEMPTS.append(name)
            raise ImportError(f"library module pulled in {name}")
        return None

sys.meta_path.insert(0, _BlockCli())
src = pathlib.Path(sys.argv[1])
allowed = set(json.loads(sys.argv[2]))
optional = set(json.loads(sys.argv[3]))
bad, errors = {}, {}
for path in sorted((src / "ux_compose").rglob("*.py")):
    rel = path.relative_to(src / "ux_compose")
    if rel.parts[0] == "cli" or rel.as_posix() in allowed or rel.name == "__main__.py":
        continue
    parts = ["ux_compose", *rel.with_suffix("").parts]
    if parts[-1] == "__init__":
        parts.pop()
    before = len(ATTEMPTS)
    try:
        importlib.import_module(".".join(parts))
    except ImportError as exc:
        if "library module pulled in" not in str(exc) and rel.as_posix() not in optional:
            errors[rel.as_posix()] = repr(exc)
    if len(ATTEMPTS) > before:
        bad[rel.as_posix()] = sorted(set(ATTEMPTS[before:]))
leaked = sorted(m for m in sys.modules if m == "ux_compose.cli" or m.startswith("ux_compose.cli."))
cli_dir = (src / "ux_compose" / "cli").resolve()
cli_files = {}
for name, mod in list(sys.modules.items()):
    f = getattr(mod, "__file__", None)
    if f and pathlib.Path(f).resolve().is_relative_to(cli_dir):
        cli_files[name] = pathlib.Path(f).resolve().relative_to(cli_dir.parent).as_posix()
print(json.dumps({"attempted": sorted(set(ATTEMPTS)), "bad": bad, "errors": errors, "leaked": leaked, "cli_files": cli_files}))
"""

# Modules allowed to fail import for a missing optional dependency (none today).
RUNTIME_OPTIONAL: set[str] = set()


def _run_guard(src_parent, allowed=(), optional=()):
    import json
    import os
    import subprocess
    import sys

    out = subprocess.run(
        [
            sys.executable,
            "-c",
            _RUNTIME_GUARD,
            str(src_parent),
            json.dumps(sorted(allowed)),
            json.dumps(sorted(optional)),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(src_parent)},
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_runtime_no_library_module_imports_cli():
    """Layer 2 of the folder law (layer 1 is the static ``_cli_imports`` scan).

    A fresh interpreter with a ``sys.meta_path`` finder that refuses
    ``ux_compose.cli*`` imports every library module. The finder records each
    attempt before raising, so an ``except ImportError: pass`` downstream does
    not hide it. That catches the dynamic import-time forms the AST scan cannot
    decide (string concatenation, f-strings, aliased ``import_module``,
    ``exec``, ``runpy``, ...). Any other ImportError fails too, because an
    unimportable module would go unchecked; list real optional-dependency
    modules in RUNTIME_OPTIONAL. Imports inside function bodies stay with the
    static check.
    """
    result = _run_guard(SRC.parent, RUNTIME_ALLOWED, RUNTIME_OPTIONAL)
    assert result == {"attempted": [], "bad": {}, "errors": {}, "leaked": [], "cli_files": {}}, result


@pytest.mark.parametrize(
    "body, key",
    [
        # swallowed: the module imports fine, but the attempt is recorded
        ('try:\n    exec("import ux_compose.cli")\nexcept ImportError:\n    pass\n', "bad"),
        ('try:\n    import ux_compose.cli\nexcept Exception:\n    pass\n', "bad"),
        ('import importlib\nimportlib.import_module("ux_compose." + "cli")\n', "bad"),
        # an unrelated ImportError is reported, not skipped
        ("import ux_compose_no_such_dependency\n", "errors"),
        # cli/ code loaded by file path under another name bypasses the finder
        (
            "import importlib.util, pathlib\n"
            "_p = pathlib.Path(__file__).parent / 'cli' / 'tool.py'\n"
            "_s = importlib.util.spec_from_file_location('not_cli_tool', _p)\n"
            "_m = importlib.util.module_from_spec(_s)\n"
            "_s.loader.exec_module(_m)\n"
            "import sys; sys.modules['not_cli_tool'] = _m\n",
            "cli_files",
        ),
    ],
)
def test_runtime_guard_probe(tmp_path, body, key):
    pkg = tmp_path / "ux_compose"
    (pkg / "cli").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "cli" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "cli" / "tool.py").write_text("X = 1\n", encoding="utf-8")
    (pkg / "sneaky.py").write_text(body, encoding="utf-8")
    result = _run_guard(tmp_path)
    assert result["leaked"] == []
    if key == "cli_files":
        assert result["cli_files"] == {"not_cli_tool": "cli/tool.py"}, result
        return
    assert "sneaky.py" in result[key], result
    if key == "bad":
        assert result["attempted"] == ["ux_compose.cli"]
