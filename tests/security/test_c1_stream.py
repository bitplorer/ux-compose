"""Streamed HTML chunks: each plain str is its own sanitized fragment.

A tag split across two plain-str chunks is not reassembled. Authors who
need a verbatim chunk use ``markupsafe.Markup`` or ux-dom ``raw()``.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import pytest
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
    """A bytes chunk is HTML, same door as a str chunk."""

    def gen():
        yield BYTES

    assert _fastapi_body(gen) == BYTES_SANITIZED


def test_asgi_stream_bytes_chunks_drop_script_and_onclick(tmp_path: Path):
    """A bytes chunk is HTML, same door as a str chunk."""

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


# é is U+00E9, UTF-8 c3 a9, split after the lead byte.
CAFE = (b"<p>caf\xc3", b"\xa9</p>")
# Each decoded piece is its own fragment, so the paragraph closes before é.
CAFE_BODY = b"<p>\n  caf\n</p>\xc3\xa9\n"
# The stream ends on the lead byte. The final flush is U+FFFD.
MID = (b"<p>caf\xc3",)
MID_BODY = b"<p>\n  caf\n</p>\xef\xbf\xbd\n"
# Two invalid chunks. One warning for the response, and the tail stays.
BAD = (b"<p>BEFORE\xff", b"\xfeAFTER</p>")
BAD_BODY = b"<p>\n  BEFORE\xef\xbf\xbd\n</p>\xef\xbf\xbdAFTER\n"


def _factory(mode: str, chunks: tuple[bytes, ...]):
    if mode == "sync":

        def gen():
            yield from chunks

        return gen

    async def gen():
        for chunk in chunks:
            yield chunk

    return gen


def _stream_body(tmp_path: Path, host: str, mode: str, chunks: tuple[bytes, ...]) -> bytes:
    factory = _factory(mode, chunks)
    if host == "fastapi":
        return _fastapi_body(factory)
    return _asgi_body(tmp_path, factory)


@pytest.mark.parametrize("host", ["fastapi", "asgi"])
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_split_multibyte_character_is_kept(tmp_path: Path, host: str, mode: str):
    """A UTF-8 character split across chunks must not drop the response."""
    assert _stream_body(tmp_path, host, mode, CAFE) == CAFE_BODY


@pytest.mark.parametrize("host", ["fastapi", "asgi"])
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_stream_ending_mid_character_flushes_replacement(
    tmp_path: Path, host: str, mode: str
):
    """final=True turns a held lead byte into U+FFFD instead of truncating."""
    assert _stream_body(tmp_path, host, mode, MID) == MID_BODY


# The bytes chunk emits 'caf' immediately. The held lead byte is flushed
# as its own U+FFFD fragment before the str, and b'\xa9' is U+FFFD after it.
ORDER = (b"caf\xc3", "<i>S</i>", b"\xa9")
ORDER_BODY = b"caf\n\xef\xbf\xbd\n<i>\n  S\n</i>\xef\xbf\xbd\n"
ORDER_MARKUP = (b"caf\xc3", Markup("<i>S</i>"), b"\xa9")
ORDER_MARKUP_BODY = b"caf\n\xef\xbf\xbd\n<i>S</i>\xef\xbf\xbd\n"


@pytest.mark.parametrize("host", ["fastapi", "asgi"])
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_str_chunk_flushes_pending_bytes_in_order(tmp_path: Path, host: str, mode: str):
    """b'caf\\xc3', '<i>S</i>', b'\\xa9' stays in that order, with U+FFFD."""
    assert _stream_body(tmp_path, host, mode, ORDER) == ORDER_BODY


@pytest.mark.parametrize("host", ["fastapi", "asgi"])
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_markup_chunk_flushes_pending_bytes_in_order(
    tmp_path: Path, host: str, mode: str
):
    """A Markup chunk flushes the same way, and stays verbatim."""
    assert _stream_body(tmp_path, host, mode, ORDER_MARKUP) == ORDER_MARKUP_BODY


@pytest.mark.parametrize("host", ["fastapi", "asgi"])
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_invalid_bytes_are_replaced_with_one_warning(
    tmp_path: Path, host: str, mode: str, caplog
):
    """Invalid bytes become U+FFFD. One warning per response, and the tail stays."""
    with caplog.at_level(logging.WARNING, logger="ux_compose.routing.core"):
        body = _stream_body(tmp_path, host, mode, BAD)
    assert body == BAD_BODY
    replaced = [r for r in caplog.records if "U+FFFD" in r.getMessage()]
    assert len(replaced) == 1


async def _drain_pair(left: Any, right: Any) -> tuple[bytes, bytes]:
    """Pull one chunk from each stream before either continues.

    A module-level decoder still holds the first response's lead byte when
    the second response decodes, so the bodies stop matching.
    """
    out_l: list[bytes] = []
    out_r: list[bytes] = []
    alive_l = True
    alive_r = True
    while alive_l or alive_r:
        if alive_l:
            try:
                out_l.append(bytes(await left.__anext__()))
            except StopAsyncIteration:
                alive_l = False
        if alive_r:
            try:
                out_r.append(bytes(await right.__anext__()))
            except StopAsyncIteration:
                alive_r = False
    return b"".join(out_l), b"".join(out_r)


def test_interleaved_streams_keep_a_decoder_per_response(tmp_path: Path):
    """Two in-flight streams must not share UTF-8 state. Both hosts."""

    async def fastapi_pair() -> tuple[bytes, bytes]:
        def gen():
            yield from CAFE

        left = _as_http_response(gen()).body_iterator
        right = _as_http_response(gen()).body_iterator
        return await _drain_pair(left, right)

    async def asgi_pair() -> tuple[bytes, bytes]:
        held = [asyncio.Event(), asyncio.Event()]
        release = [asyncio.Event(), asyncio.Event()]

        def factory(index: int):
            async def gen():
                yield CAFE[0]
                held[index].set()
                await release[index].wait()
                yield CAFE[1]

            return gen

        apps = [_page(tmp_path / f"interleave-{i}", factory(i)) for i in (0, 1)]
        tasks = [
            asyncio.create_task(_collect_asgi(apps[i], "/g")) for i in (0, 1)
        ]
        await asyncio.wait_for(held[0].wait(), timeout=5)
        await asyncio.wait_for(held[1].wait(), timeout=5)
        release[0].set()
        release[1].set()
        return tuple(await asyncio.wait_for(asyncio.gather(*tasks), timeout=5))

    async def run() -> tuple[bytes, bytes, bytes, bytes]:
        fa, fb = await fastapi_pair()
        aa, ab = await asgi_pair()
        return fa, fb, aa, ab

    fa, fb, aa, ab = asyncio.run(run())
    assert (fa, fb, aa, ab) == (CAFE_BODY, CAFE_BODY, CAFE_BODY, CAFE_BODY)


async def _collect_asgi(app: Any, path: str) -> bytes:
    chunks: list[bytes] = []
    received = {"http": False}
    finished = asyncio.Event()

    async def receive():
        if not received["http"]:
            received["http"] = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.wait_for(finished.wait(), timeout=5)
        return {"type": "http.disconnect"}

    async def send(msg):
        if msg["type"] == "http.response.body":
            chunks.append(bytes(msg.get("body") or b""))
            if not msg.get("more_body", False):
                finished.set()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [(b"host", b"test")],
        "server": ("test", 80),
        "client": ("test", 123),
        "root_path": "",
    }
    await app(scope, receive, send)
    return b"".join(chunks)
