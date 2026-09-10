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
