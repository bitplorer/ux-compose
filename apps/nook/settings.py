"""Environment SSoT — paths, debug, asset layout."""

from __future__ import annotations

from pathlib import Path

from ux_behavior.wire import debug_requests_dev
from ux_compose import WebAssets

BASE_DIR = Path(__file__).resolve().parent
DEBUG = debug_requests_dev()
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_CSS = "output.css"
webassets = WebAssets(base_dir=ASSETS_DIR, dry_run=False)
