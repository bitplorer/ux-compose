"""Atelier shop host — FastAPI + Document SSoT + Channel via wire/.

Isolation Law: this module never imports ux_channel or CEK.
Channel attaches only through App.use_channel(asgi_app=...).
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional
from urllib.parse import parse_qs

from pathlib import Path

from ux_compose import (
    App,
    doctor,
    HAS_DOM as COMPOSE_HAS_DOM,
    html,
    head,
    body,
    title,
    meta,
    link,
    script,
    header,
    main,
    footer,
    section,
    a,
    h1,
    p,
    span,
    div,
    aside,
)
from ux_compose.helpers import _serialize_tree

from apps.atelier_shop.shop import Cart, ConfirmModal, catalog_grid

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
    HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    HAS_FASTAPI = False
    FastAPI = None  # type: ignore

try:
    from ux_dom import Document
    from ux_dom.runtime import XElement, Htmx
    HAS_DOM = True
except ImportError:
    HAS_DOM = False
    Document = None  # type: ignore


_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

