"""Copy kit sources into an app (shadcn-style ownable Components).

Mirrors ``ux_dom.ui.copy``: the library holds the source of truth; ``add``
drops an editable copy into the product tree. Isolation Law: this module
never imports ux_channel.
"""

from __future__ import annotations

import re
from importlib import import_module
from pathlib import Path
from typing import Optional

from ux_compose.dom import HAS_DOM, require_dom
from ux_compose.kit.catalog import CATALOG, list_components, resolve


class KitCopyError(RuntimeError):
    pass


_KIT_MODULE_IMPORT = re.compile(r"from ux_compose\.kit\.([a-zA-Z0-9_]+) import")
_IMPORT_REWRITES = [
    (_KIT_MODULE_IMPORT, r"from .\1 import"),
    (re.compile(r"from ux_compose\.kit import"), "from . import"),
]
# catalog/copy are CLI internals, not ownable widgets.
_TOOLING_STEMS = frozenset({"catalog", "copy"})


def find_app_root(start: Optional[Path] = None) -> Path:
    """Walk up from cwd until ``app.py`` + ``routes/`` (create-app layout)."""
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "app.py").is_file() and (p / "routes").is_dir():
            return p
        nested = p / "app"
        if (nested / "app.py").is_file() and (nested / "routes").is_dir():
            return nested
        if p == p.parent:
            break
    raise KitCopyError(
        "not inside a ux-compose app (expected app.py + routes/). "
        "Run from a tree created by uxcompose create-app."
    )


def _rewrite(text: str) -> str:
    for pat, repl in _IMPORT_REWRITES:
        text = pat.sub(repl, text)
    return text


def _sibling_stems(text: str) -> tuple[str, ...]:
    """Kit modules whose imports ``_rewrite`` turns into ``from .<stem>``."""
    seen: set[str] = set()
    stems: list[str] = []
    for match in _KIT_MODULE_IMPORT.finditer(text):
        stem = match.group(1)
        if stem in _TOOLING_STEMS or stem in seen:
            continue
        seen.add(stem)
        stems.append(stem)
    return tuple(stems)


def _apply_ownable_banner(text: str, module: str, stem: str) -> str:
    banner = (
        f'"""Ownable copy of {module} — edit freely.\n\n'
        f"Copied by ``uxcompose add {stem}``. "
        f"Regenerate with ``uxcompose add {stem} --force``.\n"
    )
    if text.startswith('"""'):
        end = text.find('"""', 3)
        if end != -1:
            original = text[3:end].strip()
            rest = text[end + 3 :].lstrip("\n")
            return banner + "\n" + original + '\n"""\n\n' + rest
    return text


def _write_ownable_copy(src: Path, dest: Path, *, module: str, stem: str) -> None:
    dest.write_text(
        _apply_ownable_banner(_rewrite(src.read_text(encoding="utf-8")), module, stem),
        encoding="utf-8",
    )


def _copy_rewritten_siblings(
    text: str,
    *,
    kit_dir: Path,
    dest_dir: Path,
    force: bool,
    seen: set[str],
    written: dict[str, Path | None],
    parent_stem: str,
) -> None:
    """Copy kit modules that rewritten relative imports need (transitive)."""
    for stem in _sibling_stems(text):
        if stem in seen:
            continue
        seen.add(stem)
        src = kit_dir / f"{stem}.py"
        if not src.is_file():
            raise KitCopyError(
                f"rewrote import of ux_compose.kit.{stem} but "
                f"{src.name} is not a kit module"
            )
        original = src.read_text(encoding="utf-8")
        dest = dest_dir / f"{stem}.py"
        if not dest.exists() or force:
            _write_ownable_copy(
                src,
                dest,
                module=f"ux_compose.kit.{stem}",
                stem=parent_stem,
            )
            written[stem] = dest
        _copy_rewritten_siblings(
            original,
            kit_dir=kit_dir,
            dest_dir=dest_dir,
            force=force,
            seen=seen,
            written=written,
            parent_stem=parent_stem,
        )


def _ensure_pkg(path: Path) -> None:
    init = path / "__init__.py"
    if not init.exists():
        init.write_text(
            '"""App-local kit (copied from ux_compose.kit — edit freely)."""\n',
            encoding="utf-8",
        )


def _wire_css_import(input_css: Path, stem: str) -> bool:
    """Ensure ``@import "./{stem}.css";`` is in input.css. Returns True if wrote."""
    if not input_css.is_file():
        return False
    needle = f'@import "./{stem}.css"'
    text = input_css.read_text(encoding="utf-8")
    if needle in text:
        return False
    # After the tailwind import if present, else at the top.
    lines = text.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("@import ") or line.startswith("@source "):
            insert_at = i + 1
    lines.insert(insert_at, f'{needle};\n')
    input_css.write_text("".join(lines), encoding="utf-8")
    return True


def _page_unit_source(stem: str, cls: str) -> str:
    """Ownable routes/{stem}.py wrapping the copied card."""
    extra = ""
    if stem == "toast":
        extra = (
            "\n"
            "toast.push seals ``message=`` into the control Cap. Intent POST with\n"
            "``args={}`` is 401 (sealed-args mismatch) under Cap Host require.\n"
            "Replay html-unescaped ``data-channel-args`` with the minted\n"
            "``data-channel-cap``.\n"
        )
    return (
        f'"""GET /{stem} — page unit wrapping the copied {cls} card.\n\n'
        f"Generated by ``uxcompose add {stem} --page``. Edit freely.\n"
        f"{extra}"
        '"""\n'
        "from __future__ import annotations\n\n"
        f"from components.{stem} import {cls} as {cls}Card\n\n\n"
        f"class {cls}({cls}Card):\n"
        f'    id = "{stem}"\n'
    )


def copy_component(
    name: str,
    *,
    root: Optional[Path] = None,
    force: bool = False,
    as_page: bool = False,
) -> dict[str, Path | None]:
    """Copy a kit module into ``components/`` of the current app.

    Markup is Tailwind on the class. No companion CSS is copied —
    ``uxcompose build`` scans ``**/*.py``. ``as_page=True`` also writes
    ``routes/{stem}.py``.
    """
    try:
        meta = resolve(name)
    except KeyError as exc:
        known = ", ".join(sorted(CATALOG))
        raise KitCopyError(
            f"unknown kit component {name!r}; choose from {known}"
        ) from exc

    app_root = find_app_root(root)
    stem = meta["stem"]
    cls = meta["name"]
    if not HAS_DOM:
        raise KitCopyError(f"{cls} requires ux-dom (Python ≥3.14)")
    require_dom()

    mod = import_module(meta["module"])
    src = Path(mod.__file__).resolve()  # type: ignore[arg-type]

    dest_dir = app_root / "components"
    dest_dir.mkdir(parents=True, exist_ok=True)
    _ensure_pkg(dest_dir)

    dest = dest_dir / f"{stem}.py"
    if dest.exists() and not force:
        raise KitCopyError(f"{dest} exists (use --force)")

    original = src.read_text(encoding="utf-8")
    _write_ownable_copy(src, dest, module=meta["module"], stem=stem)

    written: dict[str, Path | None] = {"py": dest, "css": None, "page": None, "base": None}
    _copy_rewritten_siblings(
        original,
        kit_dir=src.parent,
        dest_dir=dest_dir,
        force=force,
        seen={stem},
        written=written,
        parent_stem=stem,
    )

    if as_page or meta.get("page"):
        routes = app_root / "routes"
        routes.mkdir(parents=True, exist_ok=True)
        page = routes / f"{stem}.py"
        if page.exists() and not force:
            written["page"] = page  # leave the product page unit
        elif as_page:
            # Avoid `class Login(Login)` — alias the card.
            page.write_text(_page_unit_source(stem, cls), encoding="utf-8")
            written["page"] = page

    return written


__all__ = [
    "KitCopyError",
    "copy_component",
    "find_app_root",
    "list_components",
]
