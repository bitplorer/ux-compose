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


def test_folder_law_keeps_kit_construct_and_cli_at_package_root():
    """Folders are copy/isolation laws. Do not invent cli/ or kit/kit_construct."""
    assert (SRC / "kit_construct.py").is_file()
    assert not (SRC / "kit" / "kit_construct.py").exists()
    assert not (SRC / "cli").exists()
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
    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "argv `create`" in arch


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
