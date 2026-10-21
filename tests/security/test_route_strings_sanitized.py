"""A route that returns a plain ``str`` (or ``bytes``) is untrusted HTML.

Both hosts send it through ux-dom's one string sanitizer
(``ux_dom.response.sanitize_html``); a generator body goes through
``sanitize_html_stream``. ``Markup`` stays explicit trust and is sent as
written. A stream that holds more than ``MAX_BUFFER_CHARS`` characters
without a safe boundary fails closed: a 500 before the first byte, an
aborted response after it, and the held text is never sent.

The attack strings run through real routes in Chromium: 0 executions.
The same strings served as ``Markup`` must execute, so the oracle is live.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import pytest
from ux_dom.response import MAX_BUFFER_CHARS, HtmlStreamOverflow, sanitize_html

from tests.asgi_http import asgi_get

ATTACKS = [
    "<img src=x onerror=alert(1)>hi",
    "<svg onload=alert(1)>",
    "<details open ontoggle=alert(1)>x</details>",
    "<a href='javascript:alert(1)'>x</a>",
    "<form action='javascript:alert(1)'><button>x</button></form>",
    "<script>alert(1)</script>",
    "</title><script>alert(1)</script>",
    '<iframe src="javascript:alert(1)"></iframe>',
    '<iframe srcdoc="<script>parent.alert(1)</script>"></iframe>',
    "<body onload=alert(1)>",
    "<input autofocus onfocus=alert(1)>",
    "<video><source onerror=alert(1)></video>",
    "<div style=\"animation:x 1s\" onanimationstart=alert(1)>x</div>",
    '<a href="&#106;avascript:alert(1)">x</a>',
    '<a href="java\tscript:alert(1)">x</a>',
    '<object data="javascript:alert(1)"></object>',
    '<embed src="javascript:alert(1)">',
    '<meta http-equiv="refresh" content="0;url=javascript:alert(1)">',
    '<base href="javascript:alert(1)//"><a href="x">x</a>',
    '<form><button formaction="javascript:alert(1)">x</button></form>',
    "<math><mtext><table><mglyph><style><img src=x onerror=alert(1)>",
    '<noscript><p title="</noscript><img src=x onerror=alert(1)>"></noscript>',
    "<svg><style><img src=x onerror=alert(1)></style></svg>",
    "<!--><img src=x onerror=alert(1)>-->",
    "<template><img src=x onerror=alert(1)></template><img src=x onerror=alert(1)>",
    "<svg><animate onbegin=alert(1) attributeName=x dur=1s></svg>",
    (
        '<svg><a><animate attributeName="href" to="javascript:alert(1)" dur="0.05s" '
        'fill="freeze"/><rect width="50" height="50"/></a></svg>'
    ),
    "<marquee onstart=alert(1)>x</marquee>",
]
# Raw strings that execute in Chromium: the oracle must count each of them.
CONTROLS = [*range(15), 19, *range(21, 26)]
LEGIT = [
    '<div id="hello">hi</div>',
    '<div class="p-4" id="hello"><p>a &amp; b</p><a href="/x">x</a></div>',
    "<ul><li>caf\u00e9</li><li>\u2615 \U0001f600</li></ul>",
    '<button aria-label="y" data-ux-action="x" type="button">go</button>',
    "<div>\n  <p>x</p>\n</div>",
    "plain text",
]
TEXTS = ATTACKS + LEGIT
SEEDS = range(4)

_HEADER = f'''
import random

from markupsafe import Markup
from ux_dom.dom import div

TEXTS = {TEXTS!r}


def chunks(text, seed):
    if seed == 0 or len(text) < 2:
        return list(text)
    rng = random.Random(seed)
    cuts = sorted(rng.sample(range(1, len(text)), min(len(text) - 1, rng.randint(1, 6))))
    return [text[a:b] for a, b in zip([0, *cuts], [*cuts, len(text)])]


def pick(n):
    index, _, seed = str(n).partition("_")
    if not index.isdigit():  # a relative URL in a raw control page, e.g. src=x
        return "", 0
    return TEXTS[int(index)], int(seed or 0)
'''

_ROUTES = {
    "page/[n].py": "class N:\n    def render(self, n='0'):\n        return pick(n)[0]\n",
    "bytes/[n].py": (
        "class N:\n    def render(self, n='0'):\n        return pick(n)[0].encode('utf-8')\n"
    ),
    "trusted/[n].py": (
        "class N:\n    def render(self, n='0'):\n        return Markup(pick(n)[0])\n"
    ),
    "stream/[n].py": (
        "class N:\n"
        "    def render(self, n='0'):\n"
        "        text, seed = pick(n)\n"
        "        def gen():\n"
        "            yield from chunks(text, seed)\n"
        "        return gen()\n"
    ),
    "astream/[n].py": (
        "class N:\n"
        "    def render(self, n='0'):\n"
        "        text, seed = pick(n)\n"
        "        async def gen():\n"
        "            for piece in chunks(text, seed):\n"
        "                yield piece\n"
        "        return gen()\n"
    ),
    # Byte chunks split anywhere, inside a UTF-8 sequence too.
    "bstream/[n].py": (
        "class N:\n"
        "    def render(self, n='0'):\n"
        "        text, seed = pick(n)\n"
        "        data = text.encode('utf-8')\n"
        "        def gen():\n"
        "            for piece in chunks(data.decode('latin-1'), seed):\n"
        "                yield piece.encode('latin-1')\n"
        "        return gen()\n"
    ),
    "mixed.py": (
        "class Mixed:\n"
        "    def render(self):\n"
        "        def gen():\n"
        "            yield '<p>a<img src=x onerror=alert(1)>'\n"
        "            yield Markup('<b onclick=\"go()\">kept</b>')\n"
        "            yield div('tree', id='t')\n"
        "            yield '<i>z</i>'\n"
        "        return gen()\n"
    ),
    "flood.py": (
        "class Flood:\n"
        "    def render(self):\n"
        "        def gen():\n"
        "            yield '<div>secret'\n"
        f"            yield 'x' * {MAX_BUFFER_CHARS + 10}\n"
        "        return gen()\n"
    ),
    "lateflood.py": (
        "class Lateflood:\n"
        "    def render(self):\n"
        "        async def gen():\n"
        "            yield '<p>ok</p>'\n"
        "            yield '<div>secret'\n"
        f"            yield 'x' * {MAX_BUFFER_CHARS + 10}\n"
        "        return gen()\n"
    ),
}

HOSTS = ("fastapi", "asgi")


def _pkg(root: Path, name: str) -> Path:
    pkg = root / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    for rel, src in _ROUTES.items():
        dest = pkg / "routes" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_HEADER + "\n\n" + src, encoding="utf-8")
    return pkg


def _build(root: Path, host: str, **kw):
    from ux_compose.build import build

    pkg = _pkg(root, f"sanitize_{host}_{len(kw)}")
    _app, asgi, _bundle = build(pkg, name="Sanitize", host=host, live="null", level=1, **kw)
    return asgi


@pytest.fixture(scope="module", params=HOSTS)
def host_app(request, tmp_path_factory):
    if request.param == "fastapi":
        pytest.importorskip("fastapi")
    return request.param, _build(tmp_path_factory.mktemp(request.param), request.param)


# --- whole strings ---------------------------------------------------------


def test_string_route_renders_inert(host_app):
    _host, asgi = host_app
    r = asgi_get(asgi, "/page/0")
    assert r.status_code == 200
    assert r.text == '<img src="x">hi'


@pytest.mark.parametrize("index", range(len(TEXTS)))
def test_string_and_bytes_routes_are_sanitize_html(host_app, index):
    _host, asgi = host_app
    want = sanitize_html(TEXTS[index])
    for kind in ("page", "bytes"):
        r = asgi_get(asgi, f"/{kind}/{index}")
        assert r.status_code == 200, (kind, r.text)
        assert "text/html" in r.headers["content-type"]
        assert r.text == want, kind


def test_legit_html_is_unchanged_and_gains_no_newline(host_app):
    _host, asgi = host_app
    for index, text in enumerate(LEGIT, start=len(ATTACKS)):
        r = asgi_get(asgi, f"/page/{index}")
        assert r.text == text
        assert not r.text.endswith("\n")


def test_markup_route_is_explicit_trust(host_app):
    _host, asgi = host_app
    r = asgi_get(asgi, "/trusted/0")
    assert r.text == ATTACKS[0]


@pytest.mark.parametrize("host", HOSTS)
def test_document_and_brand_wrap_get_the_sanitized_fragment(tmp_path, host):
    if host == "fastapi":
        pytest.importorskip("fastapi")
    from ux_dom import Document

    from ux_compose.brand import brand_wrap

    document = Document(head=[], body=[], ensure_csrf_token=False)
    for kw in ({"document": document}, {"document": document, "wrap": brand_wrap(document)}):
        asgi = _build(tmp_path / str(len(kw)), host, **kw)
        r = asgi_get(asgi, "/page/0")
        assert r.status_code == 200
        assert "<body" in r.text
        assert '<img src="x">hi' in r.text
        assert "onerror" not in r.text


def test_brand_wrap_called_with_a_string_sanitizes_it():
    from ux_dom import Document
    from ux_dom.response import to_html_bytes

    from ux_compose.brand import brand_wrap

    document = Document(head=[], body=[], ensure_csrf_token=False)
    html = to_html_bytes(brand_wrap(document)(ATTACKS[0])).decode("utf-8")
    assert '<img src="x">hi' in html
    assert "onerror" not in html


def test_component_string_render_is_sanitized():
    from ux_compose import Component
    from ux_compose.helpers import update_with

    class Card(Component):
        id = "card"

        def render(self):
            return '<div id="card"><img src=x onerror=alert(1)>hi</div>'

    card = Card()
    assert card.__render__() == '<div id="card"><img src="x">hi</div>'
    morph = update_with(card)[0]
    assert "onerror" not in json.dumps(getattr(morph, "__dict__", str(morph)), default=str)
    assert "onerror" not in str(morph)


# --- streams ---------------------------------------------------------------


@pytest.mark.parametrize("kind", ("stream", "astream", "bstream"))
def test_streamed_routes_equal_sanitize_html_at_any_split(host_app, kind):
    _host, asgi = host_app
    for index, text in enumerate(TEXTS):
        want = sanitize_html(text)
        for seed in SEEDS:
            r = asgi_get(asgi, f"/{kind}/{index}_{seed}")
            assert r.status_code == 200, (kind, index, seed, r.text)
            assert "text/html" in r.headers["content-type"]
            assert r.text == want, (kind, index, seed)


def test_stream_keeps_markup_and_trees_verbatim(host_app):
    _host, asgi = host_app
    r = asgi_get(asgi, "/mixed")
    assert r.status_code == 200
    from ux_dom.dom import div
    from ux_dom.response import to_html_bytes

    tree = to_html_bytes(div("tree", id="t")).decode("utf-8")
    assert r.text == f'<p>a<img src="x"></p><b onclick="go()">kept</b>{tree}<i>z</i>'



def test_stream_overflow_before_first_byte_is_a_logged_500(host_app, caplog):
    _host, asgi = host_app
    with caplog.at_level(logging.ERROR):
        r = asgi_get(asgi, "/flood")
    assert r.status_code == 500
    assert r.text == "Internal Server Error"
    assert "secret" not in r.text
    logged = [rec.exc_info[0] for rec in caplog.records if rec.exc_info]
    assert HtmlStreamOverflow in logged, caplog.records


def _raw_asgi(app, path: str) -> tuple[list[dict], BaseException | None]:
    sent: list[dict] = []

    async def receive():
        await asyncio.sleep(3600)

    async def send(msg):
        sent.append(msg)

    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "GET", "scheme": "http", "path": path, "raw_path": path.encode(),
        "query_string": b"", "headers": [(b"host", b"test")], "server": ("test", 80),
        "client": ("test", 1), "root_path": "",
    }
    try:
        asyncio.run(asyncio.wait_for(app(scope, receive, send), 30))
    except Exception as exc:  # noqa: BLE001 - the abort is the result
        return sent, exc
    return sent, None


def test_stream_overflow_after_first_byte_aborts_the_response(host_app):
    _host, asgi = host_app
    sent, exc = _raw_asgi(asgi, "/lateflood")
    assert isinstance(exc, HtmlStreamOverflow), repr(exc)
    assert sent[0]["type"] == "http.response.start" and sent[0]["status"] == 200
    bodies = [m for m in sent if m["type"] == "http.response.body"]
    assert b"".join(m.get("body", b"") for m in bodies) == b"<p>ok</p>"
    # No final empty chunk: the client sees a cut-off response, not a whole one.
    assert all(m.get("more_body", False) for m in bodies)


# --- Chromium --------------------------------------------------------------

_HOOK = (
    'for (const n of ["alert", "confirm", "prompt", "print"])'
    " window[n] = () => window.__uxHit(n);"
)
_FIRE = r"""
(async () => {
  const types = ["click", "dblclick", "mousedown", "mouseup", "mouseover", "mouseenter",
    "mousemove", "pointerdown", "pointerup", "pointerover", "pointerenter", "focus",
    "focusin", "blur", "load", "error", "toggle", "beforetoggle", "animationstart",
    "animationend", "transitionend", "begin", "end", "start", "finish", "input",
    "change", "submit", "keydown", "contextmenu", "invalid", "play", "loadstart"];
  const els = [...document.querySelectorAll("*")];
  for (const el of els) {
    for (const t of types) { try { el.dispatchEvent(new Event(t, {bubbles: true})); } catch (e) {} }
    try { el.focus && el.focus(); } catch (e) {}
  }
  for (const f of document.querySelectorAll("form")) {
    try { f.requestSubmit(); } catch (e) {}
  }
  for (const el of document.querySelectorAll("a, area, button, input, [href]")) {
    try { el.click(); } catch (e) {}
  }
  await new Promise(r => setTimeout(r, 150));
  return els.length;
})()
"""


def _chrome_bin() -> str:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    pytest.fail("Chrome is not on PATH")


class _Chrome:
    """Headless Chrome over CDP, CSP bypassed. Counts every ``alert`` call."""

    def __init__(self) -> None:
        from websockets.sync.client import connect

        self.profile = tempfile.mkdtemp(prefix="ux-sanitize-")
        self.proc = subprocess.Popen(
            [_chrome_bin(), "--headless=new", "--disable-gpu", "--no-sandbox",
             "--disable-dev-shm-usage", "--no-first-run", "--remote-debugging-port=0",
             f"--user-data-dir={self.profile}", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        self.ws = connect(self._devtools_ws(), max_size=8_000_000)
        self._n = 0
        self.hits = 0
        target = self.call("Target.createTarget", {"url": "about:blank"})
        self.session = self.call(
            "Target.attachToTarget",
            {"targetId": target["result"]["targetId"], "flatten": True},
        )["result"]["sessionId"]
        self.call("Page.enable", session=self.session)
        # The fastapi host sends a CSP that would block inline handlers by
        # itself. Bypass it so this measures the sanitizer alone.
        self.call("Page.setBypassCSP", {"enabled": True}, self.session)
        # A hit is a call to alert/confirm/prompt in any frame. The hook does
        # not open a dialog, so an onfocus alert cannot loop on refocus.
        self.call("Runtime.enable", session=self.session)
        self.call("Runtime.addBinding", {"name": "__uxHit"}, self.session)
        self.call("Page.addScriptToEvaluateOnNewDocument", {"source": _HOOK}, self.session)

    def _devtools_ws(self) -> str:
        assert self.proc.stderr is not None
        deadline = time.time() + 15
        while time.time() < deadline:
            line = self.proc.stderr.readline()
            if "DevTools listening on" in line:
                return line.split("DevTools listening on", 1)[1].strip()
            if not line and self.proc.poll() is not None:
                break
        raise RuntimeError("chrome did not open a DevTools port")

    def _send(self, method: str, params: dict, session: str | None) -> int:
        self._n += 1
        message = {"id": self._n, "method": method, "params": params}
        if session:
            message["sessionId"] = session
        self.ws.send(json.dumps(message))
        return self._n

    def call(self, method: str, params: dict | None = None, session: str | None = None):
        want = self._send(method, params or {}, session)
        while True:
            raw = json.loads(self.ws.recv())
            if raw.get("method") == "Runtime.bindingCalled":
                self.hits += 1
            elif raw.get("method") == "Page.javascriptDialogOpening":
                self.hits += 1
                self._send("Page.handleJavaScriptDialog", {"accept": False}, raw.get("sessionId"))
            elif raw.get("id") == want:
                return raw

    def visit(self, url: str) -> int:
        """Load ``url``, fire every handler it can, return the hits it caused."""
        before = self.hits
        self.call("Page.navigate", {"url": url}, self.session)
        deadline = time.time() + 10
        while time.time() < deadline:
            ready = self.call(
                "Runtime.evaluate", {"expression": "document.readyState", "returnByValue": True},
                self.session,
            )
            if ready.get("result", {}).get("result", {}).get("value") == "complete":
                break
            time.sleep(0.02)
        self.call(
            "Runtime.evaluate",
            {"expression": _FIRE, "awaitPromise": True, "returnByValue": True},
            self.session,
        )
        time.sleep(0.1)
        self.call("Runtime.evaluate", {"expression": "1"}, self.session)
        return self.hits - before

    def close(self) -> None:
        self.ws.close()
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)


def _serve(asgi):
    import uvicorn

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(asgi, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not getattr(server, "started", False):
        if time.time() > deadline:
            raise RuntimeError("server did not start")
        time.sleep(0.05)
    return server, thread, f"http://127.0.0.1:{port}"


@pytest.fixture(scope="module")
def served(host_app):
    server, thread, origin = _serve(host_app[1])
    browser = _Chrome()
    try:
        yield browser, origin
    finally:
        browser.close()
        server.should_exit = True
        thread.join(timeout=5)


def test_chromium_oracle_is_live(served):
    browser, origin = served
    hits = {i: browser.visit(f"{origin}/trusted/{i}") for i in CONTROLS}
    assert all(hits.values()), hits


def test_chromium_runs_no_script_from_string_or_streamed_routes(served):
    browser, origin = served
    rng = random.Random(7)
    ran = []
    for index in range(len(ATTACKS)):
        for path in (
            f"page/{index}",
            f"bytes/{index}",
            f"stream/{index}_{rng.randint(1, 99)}",
            f"astream/{index}_0",
            f"bstream/{index}_{rng.randint(1, 99)}",
        ):
            if browser.visit(f"{origin}/{path}"):
                ran.append(path)
    assert ran == []


def test_chromium_runs_no_script_in_a_brand_wrapped_document(tmp_path):
    pytest.importorskip("fastapi")
    from ux_dom import Document

    from ux_compose.brand import brand_wrap

    document = Document(head=[], body=[], ensure_csrf_token=False)
    asgi = _build(tmp_path, "fastapi", document=document, wrap=brand_wrap(document))
    server, thread, origin = _serve(asgi)
    browser = _Chrome()
    try:
        ran = [
            path
            for index in range(len(ATTACKS))
            for path in (f"page/{index}", f"bytes/{index}")
            if browser.visit(f"{origin}/{path}")
        ]
    finally:
        browser.close()
        server.should_exit = True
        thread.join(timeout=5)
    assert ran == []
