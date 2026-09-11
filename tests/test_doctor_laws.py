"""Doctor enforces Isolation + dual-Document heuristics (fail-closed, teaching)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ux_compose.doctor import (
    doctor,
    scan_isolation,
    scan_dual_document,
    IsolationViolation,
    scan_store_clone,
    scan_store_precedence,
)


def test_isolation_clean_on_package():
    root = Path(__file__).resolve().parents[1] / "src" / "ux_compose"
    # Public modules must not import channel; wire/ is allowlisted
    files = [p for p in root.rglob("*.py") if "wire" not in p.parts]
    diags = scan_isolation(files)
    assert diags == [], diags


def test_isolation_does_not_flag_ux_channel_static_name():
    with tempfile.TemporaryDirectory() as td:
        ok = Path(td) / "runtime.py"
        ok.write_text(
            "from ux_dom.plugins.package_static import ux_channel_static\n",
            encoding="utf-8",
        )
        assert scan_isolation([ok]) == []

    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "product_cart.py"
        bad.write_text(
            "from ux_channel import Channel\n"
            "def add():\n"
            "    pass\n",
            encoding="utf-8",
        )
        diags = scan_isolation([bad])
        assert diags, "expected Isolation diagnostic"
        assert any("Isolation" in d or "ux_channel" in d for d in diags)


def test_isolation_allows_wire_door():
    with tempfile.TemporaryDirectory() as td:
        # Simulate path containing ux_compose/wire
        wire_dir = Path(td) / "ux_compose" / "wire"
        wire_dir.mkdir(parents=True)
        ok = wire_dir / "boot.py"
        ok.write_text("from ux_channel import Channel\n", encoding="utf-8")
        diags = scan_isolation([ok])
        assert diags == [], f"wire door must be allowlisted, got {diags}"


def test_doctor_fail_closed_raises():
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "leak.py"
        bad.write_text("import ux_channel\n", encoding="utf-8")
        try:
            doctor([bad], fail=True)
            raised = False
        except IsolationViolation:
            raised = True
        assert raised


def test_doctor_no_fail_reports():
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "leak.py"
        bad.write_text("import ux_channel\n", encoding="utf-8")
        report = doctor([bad], fail=False)
        assert report.ok is False
        assert report.diagnostics


def test_dual_document_heuristic():
    with tempfile.TemporaryDirectory() as td:
        mod = Path(td) / "shells.py"
        mod.write_text(
            "from somewhere import Document\n"
            "d1 = Document()\n"
            "d2 = Document(head=[])\n",
            encoding="utf-8",
        )
        diags = scan_dual_document([mod])
        assert diags, "expected dual-Document diagnostic"
        assert any("Document" in d for d in diags)


def test_single_document_ok():
    with tempfile.TemporaryDirectory() as td:
        mod = Path(td) / "one.py"
        mod.write_text("d = Document()\n", encoding="utf-8")
        diags = scan_dual_document([mod])
        assert diags == []


class _Caps:
    kernel_ssot = None


def _app(*, caps_name: str, kernel_ssot=None, cek="require", channel=True):
    caps = type(caps_name, (_Caps,), {"kernel_ssot": kernel_ssot})()

    class _Registry:
        _caps = caps

    class _Channel:
        registry = _Registry()

    class _App:
        _channel = _Channel() if channel else None
        _cek = cek

    return _App()


def test_doctor_fail_loud_when_require_is_not_cek_runtime():
    """cek=require + live Channel without CekHostCapService is a hard violation."""
    app = _app(caps_name="CapService", kernel_ssot="channel", cek="require")
    report = doctor([], fail=False, app=app)
    assert report.ok is False
    assert any("violation" in d.lower() for d in report.diagnostics)
    assert any("CekHostCapService" in d or "cek-runtime" in d for d in report.diagnostics)


def test_doctor_ok_when_identity_is_cek_runtime():
    app = _app(caps_name="CekHostCapService", kernel_ssot="cek-runtime", cek="require")
    report = doctor([], fail=False, app=app)
    assert report.ok is True
    assert not any("Cap Host" in d for d in report.diagnostics)


def test_doctor_skips_cek_check_when_off_or_no_channel():
    assert doctor([], fail=False, app=_app(caps_name="CapService", cek="require", channel=False)).ok is True
    assert doctor([], fail=False, app=_app(caps_name="CapService", cek="off")).ok is True
    assert doctor([], fail=False, app=_app(caps_name="CapService", cek="adapt")).ok is True


def test_doctor_treats_unset_cek_as_require_when_channel_live():
    """Swallowed require must not look healthy: _cek is None, Channel still live."""
    report = doctor([], fail=False, app=_app(caps_name="CapService", cek=None))
    assert report.ok is False
    assert any("violation" in d.lower() for d in report.diagnostics)


def test_doctor_fail_loud_when_stack_incomplete(monkeypatch):
    """Missing specialists are hard diagnostics (unless --no-fail / fail=False)."""
    import importlib

    doctor_mod = importlib.import_module("ux_compose.doctor")
    monkeypatch.setattr(
        doctor_mod,
        "_detect_capabilities",
        lambda: {
            "ux_dom": False,
            "ux_behavior": True,
            "ux_motion": True,
            "ux_channel": True,
            "directory_routes": True,
        },
    )
    report = doctor([], fail=False)
    assert report.ok is False
    assert any("incomplete stack" in d.lower() for d in report.diagnostics)
    assert any("ux-dom" in d for d in report.diagnostics)
    assert any("Complete install first" in t for t in report.teaching)
    teaching = " ".join(report.teaching)
    assert 'pip install -e ".[dev]"' in teaching
    assert "pip install -r requirements.txt" in teaching
    assert "pip install ux-compose" not in teaching


def test_scan_store_clone_flags_file_state_store():
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "serve_state.py"
        bad.write_text(
            "class FileStateStore:\n    def get(self, key):\n        return None\n",
            encoding="utf-8",
        )
        diags = scan_store_clone([bad])
        assert diags
        assert any("FileStateStore" in d and "Ownership" in d for d in diags)


def test_scan_store_clone_clean_on_package():
    root = Path(__file__).resolve().parents[1] / "src" / "ux_compose"
    files = [p for p in root.rglob("*.py")]
    assert scan_store_clone(files) == []


def test_scan_store_precedence_flags_both_envs(monkeypatch):
    monkeypatch.setenv("UXCOMPOSE_STATE_STORE", "/tmp/compose.state")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    diags = scan_store_precedence()
    assert diags
    assert any("REDIS_URL" in d and "UXCOMPOSE_STATE_STORE" in d for d in diags)
    assert any("violation" in d.lower() for d in diags)


def test_scan_store_precedence_ok_when_only_one(monkeypatch):
    monkeypatch.setenv("UXCOMPOSE_STATE_STORE", "/tmp/compose.state")
    monkeypatch.delenv("REDIS_URL", raising=False)
    assert scan_store_precedence() == []
    monkeypatch.delenv("UXCOMPOSE_STATE_STORE", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    assert scan_store_precedence() == []
