"""Streamed HTML chunks: each plain str is its own sanitized fragment.

A tag split across two plain-str chunks is not reassembled. Authors who
need a verbatim chunk use ``markupsafe.Markup`` or ux-dom ``raw()``.
"""
from __future__ import annotations

from pathlib import Path

from markupsafe import Markup

from ux_compose import raw
from ux_compose.routing.asgi import DirectoryASGI
from ux_compose.routing.core import DirectoryRoutes, RouteRecord
from ux_compose.routing.fastapi import _as_http_response

from tests.asgi_http import asgi_http

SCRIPT = "<script>alert(1)</script>"
CLICK = '<div onclick="alert(1)">x</div>'
# What defHTML keeps of CLICK. The script chunk contributes nothing.
SANITIZED = b"<div>\n  x\n</div>"
MARKED = Markup(SCRIPT)
# Live bytes chunk: onclick and script must not survive either host.
BYTES = b'<u onclick="b()">B</u><script>b()</script>'
BYTES_SANITIZED = b"<u>\n  B\n</u>"


def _page(tmp_path: Path, render):
    class StreamPage:
        def render(self):
            return render()

    core = DirectoryRoutes(tmp_path)
    core.records = [
        RouteRecord(
            method="GET",
            path="/g",
            name="StreamPage",
            page_cls=StreamPage,
            kind="page",
        )
    ]
    return DirectoryASGI(core)


def _fastapi_body(gen) -> bytes:
    _status, _headers, body = asgi_http(_as_http_response(gen()), "/")
    return body


def _asgi_body(tmp_path: Path, gen) -> bytes:
    _status, _headers, body = asgi_http(_page(tmp_path, gen), "/g")
    return body


def test_fastapi_stream_str_chunks_drop_script_and_onclick():
    def gen():
        yield SCRIPT
        yield CLICK

    assert _fastapi_body(gen) == SANITIZED


def test_asgi_stream_str_chunks_drop_script_and_onclick(tmp_path: Path):
    def gen():
        yield SCRIPT
        yield CLICK

    assert _asgi_body(tmp_path, gen) == SANITIZED


def test_fastapi_stream_bytes_chunks_drop_script_and_onclick():
    """A bytes chunk is strict-UTF-8 HTML, same door as a str chunk."""

    def gen():
        yield BYTES

    assert _fastapi_body(gen) == BYTES_SANITIZED


def test_asgi_stream_bytes_chunks_drop_script_and_onclick(tmp_path: Path):
    """A bytes chunk is strict-UTF-8 HTML, same door as a str chunk."""

    def gen():
        yield BYTES

    assert _asgi_body(tmp_path, gen) == BYTES_SANITIZED


def test_fastapi_stream_markup_chunk_is_byte_identical():
    def gen():
        yield MARKED

    assert _fastapi_body(gen) == MARKED.encode("utf-8")


def test_asgi_stream_markup_chunk_is_byte_identical(tmp_path: Path):
    def gen():
        yield MARKED

    assert _asgi_body(tmp_path, gen) == MARKED.encode("utf-8")


def test_fastapi_stream_raw_chunk_stays_verbatim():
    def gen():
        yield raw(SCRIPT)

    assert _fastapi_body(gen) == SCRIPT.encode("utf-8")


def test_asgi_stream_raw_chunk_stays_verbatim(tmp_path: Path):
    def gen():
        yield raw(SCRIPT)

    assert _asgi_body(tmp_path, gen) == SCRIPT.encode("utf-8")


class _AsyncChunks:
    """Async iterable that is not an async generator."""

    def __init__(self, chunks):
        self._chunks = tuple(chunks)

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for chunk in self._chunks:
            yield chunk


def test_fastapi_stream_aiter_that_is_not_a_generator_is_sanitized():
    """``_sanitized_stream`` must follow ``__aiter__``, not only async gens."""
    body = _fastapi_body(lambda: _AsyncChunks((SCRIPT, CLICK)))
    assert body == SANITIZED
