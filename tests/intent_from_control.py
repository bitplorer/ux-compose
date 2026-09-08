"""Extract Intent POST payload from rendered control attrs.

Isolation: no ``ux_channel`` import. HTML-unescape ``data-channel-args``
so sealed JSON survives attribute encoding (``&quot;`` → ``"``).
"""
from __future__ import annotations

import html as html_lib
import json
import re
from typing import Any

_TAG_RE = re.compile(r"<[^>]+>")
_ATTR_DQ = re.compile(r'([A-Za-z_:][\w:.-]*)\s*=\s*"([^"]*)"')
_ATTR_SQ = re.compile(r"([A-Za-z_:][\w:.-]*)\s*=\s*'([^']*)'")


def _tag_attrs(tag: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for m in _ATTR_DQ.finditer(tag):
        attrs[m.group(1)] = html_lib.unescape(m.group(2))
    for m in _ATTR_SQ.finditer(tag):
        attrs.setdefault(m.group(1), html_lib.unescape(m.group(2)))
    return attrs


def intent_from_control(html: str, action: str) -> dict[str, Any]:
    """Read ``data-channel-cap`` + html-unescaped ``data-channel-args`` for Intent POST.

    Returns ``{"action", "cap", "args"}``. Missing ``data-channel-args`` → ``{}``.
    """
    want = str(action)
    for tag in _TAG_RE.findall(html or ""):
        attrs = _tag_attrs(tag)
        found = attrs.get("data-channel-action") or attrs.get("data-ux-action")
        if found != want:
            continue
        raw_args = attrs.get("data-channel-args") or "{}"
        try:
            parsed = json.loads(raw_args)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"data-channel-args for {want!r} is not JSON after html-unescape: {raw_args!r}"
            ) from exc
        args = parsed if isinstance(parsed, dict) else {}
        return {
            "action": want,
            "cap": str(attrs.get("data-channel-cap") or ""),
            "args": args,
        }
    raise LookupError(f"no control for {want!r} in html")


__all__ = ["intent_from_control"]
