"""Product build — production CSS minify for app.py trees.

Ownership (FLOW law):
  - Compiler resolution lives HERE (``ux_compose.tailwind``).
    Finding / downloading / invoking the Tailwind CLI is product DX.
  - Render stays on ux-dom: className, ``<link>``, package static.
  - App folders live HERE (``ux_compose.assets.WebAssets``).
  - ``uxdom build`` is Document/static verify for leftover ``app/main.py``
    trees. It does not compile CSS.

Product path::

    uxcompose create-app myapp
    cd myapp
    uxcompose serve dev      # clocks on; sibling Tailwind --watch
    uxcompose build          # minify → assets/static/file/css/output.css
    uxcompose serve prod     # clocks off; disk CSS
    uxcompose deploy --provider docker
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class BuildStep:
    name: str
    ok: bool
    detail: str


@dataclass
class ProductBuildReport:
    root: Path
    steps: list[BuildStep] = field(default_factory=list)
    output_css: Optional[Path] = None

    @property
    def ok(self) -> bool:
        return all(s.ok for s in self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "root": str(self.root),
            "output_css": str(self.output_css) if self.output_css else None,
            "steps": [
                {"name": s.name, "ok": s.ok, "detail": s.detail} for s in self.steps
            ],
        }


def find_product_root(start: Optional[Path] = None) -> Path:
    """Locate a product app root.

    Prefer ``app.py`` (uxcompose create-app). Leftover ``app/main.py``
    showcase trees are ``uxdom build`` (Document/static verify), not this CLI.
    """
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "app.py").is_file():
            return p
        if p == p.parent:
            break
    raise FileNotFoundError(
        "no product app found (expected app.py from uxcompose create-app). "
        "Leftover app/main.py trees: uxdom build (does not compile CSS)."
    )


def run_product_build(
    *,
    cwd: Optional[Path] = None,
    skip_tailwind: bool = False,
    skip_import: bool = False,
    minify: bool = True,
    watch: bool = False,
    app_ref: str = "app:asgi",
) -> ProductBuildReport:
    """Run the product production build.

    Steps:
      1. Structure (app.py from uxcompose create-app)
      2. Tailwind minify/watch via ux_compose.tailwind
      3. Soft import of the ASGI entry (default app:asgi)
      4. Soft product doctor

    ``minify`` and ``watch`` are XOR (same as argv_with_io: minify wins).
    """
    from ux_compose.tailwind import argv_with_io, discover_css_io, resolve_tailwind

    root = find_product_root(cwd)
    report = ProductBuildReport(root=root)

    app_py = root / "app.py"
    if app_py.is_file():
        report.steps.append(BuildStep("app.py", True, str(app_py.relative_to(root))))
    else:
        report.steps.append(
            BuildStep("structure", False, "expected app.py from uxcompose create-app")
        )
        return report

    if skip_tailwind:
        report.steps.append(BuildStep("tailwind", True, "skipped"))
    else:
        io = discover_css_io(root)
        if io is None:
            report.steps.append(
                BuildStep(
                    "tailwind",
                    True,
                    "no assets/css/input.css — uxcompose create-app emits one; "
                    "CSS is soft-OK without it, not a production path",
                )
            )
        else:
            input_css, output_css = io
            output_css.parent.mkdir(parents=True, exist_ok=True)
            hit = resolve_tailwind(cwd=root, ensure=True)
            if hit is None:
                report.steps.append(
                    BuildStep(
                        "tailwind",
                        False,
                        "Tailwind CLI not found. Install one of: "
                        "pip install pytailwindcss · "
                        "npm i -D @tailwindcss/cli · "
                        "or put tailwindcss on PATH.",
                    )
                )
            else:
                use_minify = bool(minify) and not watch
                cmd = argv_with_io(
                    hit.argv,
                    input_css=input_css,
                    output_css=output_css,
                    minify=use_minify,
                    watch=bool(watch) and not use_minify,
                )
                env = os.environ.copy()
                env["PYTHONPATH"] = os.pathsep.join(
                    [str(root), env.get("PYTHONPATH", "")]
                )
                env["UXDOM_TAILWIND_OWNED"] = "1"
                if watch and not use_minify:
                    print(
                        f"tailwind --watch  ({hit.source})\n"
                        f"  in  {input_css.relative_to(root)}\n"
                        f"  out {output_css.relative_to(root)}\n"
                        "  Ctrl-C to stop",
                        flush=True,
                    )
                    proc = subprocess.run(cmd, cwd=str(root), env=env)
                    report.steps.append(
                        BuildStep(
                            "tailwind",
                            proc.returncode == 0,
                            f"{hit.source} watch exit {proc.returncode}",
                        )
                    )
                else:
                    proc = subprocess.run(
                        cmd,
                        cwd=str(root),
                        capture_output=True,
                        text=True,
                        timeout=180,
                        env=env,
                    )
                    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
                    ok = proc.returncode == 0
                    detail = f"{hit.source} exit {proc.returncode}"
                    if out:
                        detail += f" · {out[:200]}"
                    if ok and output_css.is_file():
                        detail += f" · wrote {output_css.relative_to(root)}"
                        report.output_css = output_css
                    report.steps.append(BuildStep("tailwind", ok, detail))

    if skip_import:
        report.steps.append(BuildStep("import", True, "skipped"))
    else:
        if ":" not in app_ref:
            report.steps.append(
                BuildStep(
                    "import",
                    False,
                    f"ASGI path must be module:attr, got {app_ref!r}",
                )
            )
        else:
            mod_name, _, attr = app_ref.partition(":")
            code = (
                f"import importlib, sys\n"
                f"sys.path.insert(0, {str(root)!r})\n"
                f"m = importlib.import_module({mod_name!r})\n"
                f"obj = getattr(m, {attr!r}, None)\n"
                f"assert obj is not None, 'attr missing'\n"
                f"print(type(obj).__name__)\n"
            )
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "PYTHONPATH": str(root)},
            )
            detail = (proc.stdout or proc.stderr or "").strip()[:200]
            report.steps.append(
                BuildStep(
                    f"import:{app_ref}",
                    proc.returncode == 0,
                    detail or f"exit {proc.returncode}",
                )
            )

    try:
        from ux_compose.doctor import doctor

        doc = doctor([root], fail=False)
        ok_flag = bool(getattr(doc, "ok", True))
        report.steps.append(
            BuildStep(
                "doctor",
                ok_flag,
                f"ok={ok_flag} surfaces={getattr(doc, 'surfaces', None)}",
            )
        )
    except Exception as e:
        report.steps.append(BuildStep("doctor", False, f"doctor failed: {e}"))

    return report


def format_product_build_report(report: ProductBuildReport) -> str:
    lines = ["uxcompose build", f"root: {report.root}", "=" * 48]
    for s in report.steps:
        mark = "OK" if s.ok else "FAIL"
        lines.append(f"  [{mark:4}] {s.name}: {s.detail}")
    if report.output_css:
        lines.append(f"  css → {report.output_css}")
    lines.append("=" * 48)
    lines.append("BUILD OK" if report.ok else "BUILD FAILED")
    if report.ok:
        lines.append("Next: uxcompose serve prod")
        if report.output_css:
            lines.append(
                f"CSS linked as /css/output.css "
                f"(file {report.output_css.name} under assets/static/file/css)"
            )
    return "\n".join(lines)


__all__ = [
    "BuildStep",
    "ProductBuildReport",
    "find_product_root",
    "format_product_build_report",
    "run_product_build",
]
