"""Doctor residual scans teach. They do not fail-close."""
from __future__ import annotations

import tempfile
from pathlib import Path

from ux_compose.doctor import (
    doctor,
    scan_kit_product_imports,
    scan_leftover_aliases,
)


def test_kit_import_in_product_is_residual_not_violation():
    with tempfile.TemporaryDirectory() as td:
        product = Path(td) / "routes" / "shop.py"
        product.parent.mkdir(parents=True)
        product.write_text(
            "from ux_compose.kit import Dialog\n",
            encoding="utf-8",
        )
        diags = scan_kit_product_imports([product])
        assert diags, "expected residual teaching"
        assert any("residual" in d and "kit" in d for d in diags)
        report = doctor([product], fail=False)
        assert report.ok is True
        assert any("residual" in d for d in report.diagnostics)


def test_kit_import_in_tests_is_silent():
    with tempfile.TemporaryDirectory() as td:
        tests = Path(td) / "tests" / "test_kit.py"
        tests.parent.mkdir(parents=True)
        tests.write_text(
            "from ux_compose.kit import Dialog\n",
            encoding="utf-8",
        )
        assert scan_kit_product_imports([tests]) == []


def test_leftover_batteries_keyword_is_residual():
    with tempfile.TemporaryDirectory() as td:
        product = Path(td) / "app.py"
        product.write_text(
            'build(PACKAGE, host="batteries")\n',
            encoding="utf-8",
        )
        diags = scan_leftover_aliases([product])
        assert diags
        assert any("batteries" in d for d in diags)


def test_leftover_use_host_batteries_is_residual():
    with tempfile.TemporaryDirectory() as td:
        product = Path(td) / "app.py"
        product.write_text(
            'app.use_host("batteries")\n',
            encoding="utf-8",
        )
        diags = scan_leftover_aliases([product])
        assert diags
        assert any("batteries" in d for d in diags)


def test_leftover_degrade_module_is_residual():
    with tempfile.TemporaryDirectory() as td:
        product = Path(td) / "app.py"
        product.write_text(
            "from ux_compose.degrade import AttachNote\n",
            encoding="utf-8",
        )
        diags = scan_leftover_aliases([product])
        assert diags
        assert any("ux_compose.degrade" in d for d in diags)
