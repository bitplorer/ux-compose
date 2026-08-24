"""Product app asset layout — this package owns it.

Disk convention (locked with create-app / build / ``/css`` mount)::

    assets/css/input.css                 # author source
    assets/static/file/css/output.css    # compiler output
    URL: /css/output.css

Does **not** mkdir database / upload / cache / templates — those are not
the CSS/JS product tree. Does **not** emit ``<link>`` tags (Document does).
Does **not** serve library JS (``/ux-dom/static/x_element.js`` stays on ux-dom).

``WebAssets.static.css`` keeps the historical nested folder so existing
trees and the compiler write the same place. Flatten later as one cut,
not a second SSoT.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

__all__ = [
    "CSS_URL_PREFIX",
    "OUTPUT_CSS_NAME",
    "WebAssets",
]

CSS_URL_PREFIX = "/css"
OUTPUT_CSS_NAME = "output.css"
_INPUT_REL = Path("css") / "input.css"
_STATIC_CSS_REL = Path("static") / "file" / "css"
_STATIC_JS_REL = Path("static") / "file" / "js"


@dataclass(frozen=True)
class _Static:
    css: Path
    js: Path


class WebAssets:
    """App-local CSS/JS folders. Author API matches the old constructor.

    ::

        from ux_compose import WebAssets
        webassets = WebAssets(base_dir=ASSETS_DIR, dry_run=False)
        webassets.static.css   # assets/static/file/css
        webassets.output_css   # .../output.css
        webassets.css_href     # /css/output.css
    """

    def __init__(
        self,
        base_dir: Union[str, Path],
        sub_dir: Union[str, Path] = "",
        *,
        dry_run: bool = True,
    ) -> None:
        base = Path(base_dir)
        if base.is_file():
            base = base.parent
        if sub_dir:
            base = base / Path(sub_dir)
        self.dir = base.resolve()
        self.static = _Static(
            css=self.dir / _STATIC_CSS_REL,
            js=self.dir / _STATIC_JS_REL,
        )
        self.input_css = self.dir / _INPUT_REL
        self.output_css = self.static.css / OUTPUT_CSS_NAME
        self.css_href = f"{CSS_URL_PREFIX}/{OUTPUT_CSS_NAME}"
        if not dry_run:
            self.ensure()

    def ensure(self) -> "WebAssets":
        self.static.css.mkdir(parents=True, exist_ok=True)
        self.static.js.mkdir(parents=True, exist_ok=True)
        self.input_css.parent.mkdir(parents=True, exist_ok=True)
        return self

    def mount_css(self, asgi: Any, *, url: str = CSS_URL_PREFIX) -> bool:
        """Mount compiler output at ``/css``. Soft-skip if FastAPI is missing."""
        if asgi is None:
            return False
        self.ensure()
        try:
            from fastapi.staticfiles import StaticFiles
        except Exception:
            return False
        try:
            asgi.mount(
                url,
                StaticFiles(directory=str(self.static.css), check_dir=False),
                name="css",
            )
            return True
        except Exception:
            return False

    @classmethod
    def from_app_root(
        cls, root: Union[str, Path], *, dry_run: bool = True
    ) -> "WebAssets":
        """Layout under ``<root>/assets`` (create-app tree)."""
        return cls(base_dir=Path(root) / "assets", dry_run=dry_run)
