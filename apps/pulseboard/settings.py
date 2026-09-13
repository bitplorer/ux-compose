"""Environment SSoT — paths, debug, asset layout."""

from __future__ import annotations

import os
from pathlib import Path

from ux_compose import WebAssets

BASE_DIR = Path(__file__).resolve().parent
DEBUG = os.environ.get("DEBUG", "1") not in ("0", "false", "False")
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_CSS = "output.css"
webassets = WebAssets(base_dir=ASSETS_DIR, dry_run=False)
