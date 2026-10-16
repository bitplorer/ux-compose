"""routing.fastapi: a render that returns None yields an empty-body ux-dom HTMLResponse."""
from __future__ import annotations

from ux_dom.response.starlette import HTMLResponse

from ux_compose.routing.fastapi import _as_html_response


def test_none_tree_is_empty_html_response():
    resp = _as_html_response(None)
    assert isinstance(resp, HTMLResponse)
    assert resp.status_code == 200
    assert resp.body == b""
    assert resp.media_type == "text/html"
