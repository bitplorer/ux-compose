"""Doctor residual scans teach. They do not fail-close."""
from __future__ import annotations

import tempfile
from pathlib import Path

from ux_compose.doctor import (
    doctor,
    scan_kit_product_imports,
    scan_leftover_aliases,
    scan_render_chrome,
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


def test_render_stunning_root_is_residual_not_violation():
    with tempfile.TemporaryDirectory() as td:
        product = Path(td) / "routes" / "hello.py"
        product.parent.mkdir(parents=True)
        product.write_text(
            "class Hello:\n"
            "    def render(self):\n"
            "        return '<div id=\"stunning-root\">x</div>'\n",
            encoding="utf-8",
        )
        diags = scan_render_chrome([product])
        assert diags, "expected residual teaching"
        assert any("stunning-root" in d and "residual" in d for d in diags)
        report = doctor([product], fail=False)
        assert report.ok is True
        assert any("stunning-root" in d for d in report.diagnostics)


def test_render_nav_brand_is_residual():
    with tempfile.TemporaryDirectory() as td:
        product = Path(td) / "routes" / "hello.py"
        product.parent.mkdir(parents=True)
        product.write_text(
            "class Hello:\n"
            "    def render(self):\n"
            "        return '<nav class=\"nav\"><span class=\"brand\">Acme</span></nav>'\n",
            encoding="utf-8",
        )
        diags = scan_render_chrome([product])
        assert diags
        assert any('class="nav"' in d and "brand" in d for d in diags)


def test_render_chrome_skips_non_routes():
    with tempfile.TemporaryDirectory() as td:
        other = Path(td) / "shell.py"
        other.write_text(
            "def render():\n"
            "    return '<div id=\"stunning-root\" class=\"nav\"></div>'\n",
            encoding="utf-8",
        )
        assert scan_render_chrome([other]) == []


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
