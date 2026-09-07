"""Morph payload inspectors + fragment-law assertions.

HTML-string path only. Do not treat this as Morph/L3 DOM coverage.
"""
from __future__ import annotations

import re
from typing import Any

# Chrome that belongs on GET Document, never inside a morph targeting #hello.
SHELL_ROOT_ID = "stunning-root"
SHELL_BRAND = "StunningCek"
KERNEL_SSOT_ID = "kernel_ssot"

_FIRST_ID = re.compile(r"""id\s*=\s*['\"]([^'\"]+)['\"]""", re.I)
_DOC_CHROME = re.compile(r"<(html|head|body)\b", re.I)


def morph_html_and_target(ops: Any) -> tuple[str, str]:
    """Extract (html, target) from update_with / dispatch morph ops."""
    if ops is None:
        return "", ""
    seq = list(ops) if not isinstance(ops, (str, bytes)) else [ops]
    if not seq:
        return "", ""
    op = seq[0]
    html, target = _from_op(op)
    if not html:
        html = str(getattr(op, "html", "") or "")
    if not target:
        target = str(getattr(op, "target", "") or "")
    return str(html or ""), str(target or "")


def _from_op(op: Any) -> tuple[str, str]:
    html = ""
    target = ""
    if isinstance(op, dict):
        html = op.get("html") or op.get("patch") or op.get("innerHTML") or ""
        target = op.get("target") or op.get("selector") or ""
        payload = op.get("payload")
        if isinstance(payload, dict):
            html = html or payload.get("html") or payload.get("patch") or payload.get("innerHTML") or ""
            target = target or payload.get("target") or payload.get("selector") or ""
        return str(html or ""), str(target or "")
    payload = getattr(op, "payload", None)
    if isinstance(payload, dict):
        html = payload.get("html") or payload.get("patch") or payload.get("innerHTML") or ""
        target = payload.get("target") or payload.get("selector") or ""
    elif payload is not None:
        html = getattr(payload, "html", None) or getattr(payload, "patch", None) or ""
        target = getattr(payload, "target", None) or getattr(payload, "selector", None) or ""
    if not html:
        html = getattr(op, "html", None) or getattr(op, "patch", None) or ""
    if not target:
        target = getattr(op, "target", None) or getattr(op, "selector", None) or ""
    return str(html or ""), str(target or "")


def first_id(html: str) -> str | None:
    m = _FIRST_ID.search(html or "")
    return m.group(1) if m else None


def assert_html_is_fragment(html: str, *, target_id: str) -> None:
    """Fragment law: morph/render HTML for #target_id is not a document shell.

    Outer brand chrome (stunning-root, StunningCek, kernel_ssot, <html>/<head>/<body>)
    must not appear. The first id= in the payload is the morph target root.
    """
    blob = html or ""
    lower = blob.lower()
    assert SHELL_ROOT_ID not in blob, (
        f"fragment law: morph HTML must not embed outer shell #{SHELL_ROOT_ID}:\n{blob[:800]}"
    )
    assert SHELL_BRAND not in blob, (
        f"fragment law: morph HTML must not embed brand chrome {SHELL_BRAND!r}:\n{blob[:800]}"
    )
    assert f'id="{KERNEL_SSOT_ID}"' not in blob and f"id='{KERNEL_SSOT_ID}'" not in blob, (
        f"fragment law: morph HTML must not nest #{KERNEL_SSOT_ID} badge chrome:\n{blob[:800]}"
    )
    assert _DOC_CHROME.search(blob) is None, (
        f"fragment law: morph HTML must not include document chrome:\n{blob[:800]}"
    )
    assert "stylesheet" not in lower, (
        f"fragment law: morph HTML must not include stylesheet chrome:\n{blob[:800]}"
    )
    rid = first_id(blob)
    assert rid == target_id, (
        f"fragment law: first id must be {target_id!r} (morph target root), got {rid!r}:\n{blob[:800]}"
    )
    assert blob.lower().count(f'id="{target_id}"') + blob.lower().count(f"id='{target_id}'") <= 1


def assert_morph_fragment(ops: Any, *, target_id: str) -> str:
    html, target = morph_html_and_target(ops)
    tid = target_id if str(target_id).startswith("#") else f"#{target_id}"
    if target:
        got = target if str(target).startswith("#") else f"#{target}"
        assert got == tid, f"morph target must be {tid}, got {target!r}"
    assert html.strip(), f"morph HTML missing for {tid}: ops={ops!r}"
    assert_html_is_fragment(html, target_id=target_id.lstrip("#"))
    return html
