"""Doctor enforces Isolation + dual-Document heuristics (fail-closed, teaching)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ux_compose.doctor import doctor, scan_isolation, scan_dual_document, IsolationViolation


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
