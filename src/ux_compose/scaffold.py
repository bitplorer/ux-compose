"""Progressive scaffold — create-app [--level=N|auto] [--host=auto|fastapi|asgi].

Emits the locked product path:

- settings.py          environment SSoT (BASE_DIR, DEBUG, WebAssets)
- document.py          Document SSoT + .use(XElement, Csp, Channel.optional)
- app.py               composition root via build(host=, live=, level=, document=, cek=)
- routes/index.py      GET / alias so the app root is not 404
- routes/hello.py      page unit (module stem == class name)
- assets/css/input.css Tailwind tokens + @source
- requirements.txt     the running ux-compose commit; specialists come with it

Laws: Isolation (no ux_channel in product files). Progressive Superpower
(complete install first; Level 1 page units stay correct when Channel or
Motion attach).
"""
from __future__ import annotations

from importlib import metadata
from pathlib import Path
from textwrap import dedent
from urllib.parse import urlparse
from urllib.request import url2pathname
import json
import keyword
import re
import subprocess
import sys


APP_PY = dedent('''\
    """Progressive ux-compose app (level={level_repr}, host={host}).

    Composition root: host + live set only in build().
    Document SSoT lives in document.py.
    Environment in settings.py.
    """
    from __future__ import annotations

    from pathlib import Path

    from ux_compose.build import build
    from ux_compose import doctor
    {chrome_import}from document import document
    from settings import webassets

    PACKAGE = Path(__file__).resolve().parent


    def _mount_css(asgi):
        """Serve compiled CSS at /css/output.css. Returns asgi (maybe wrapped)."""
        if asgi is None or webassets is None:
            return asgi
        mount = getattr(webassets, "mount_css", None)
        if callable(mount):
            return mount(asgi)
        css_dir = getattr(getattr(webassets, "static", None), "css", None)
        if css_dir is None:
            return asgi
        from pathlib import Path as _P
        from starlette.staticfiles import StaticFiles

        _P(str(css_dir)).mkdir(parents=True, exist_ok=True)
        asgi.mount(
            "/css",
            StaticFiles(directory=str(css_dir), check_dir=False),
            name="css",
        )
        return asgi


    def main(*, use_htmx: bool = False):
        app, asgi, bundle = build(
            PACKAGE,
            name="{name}",
            host="{host}",
            live="auto",
            level={level_boot},
            base="routes",
            use_htmx=use_htmx,
            document=document,
            wrap={wrap_expr},
            cek="require",
        )
        asgi = _mount_css(asgi)
        return app, asgi, bundle


    if __name__ == "__main__":
        app, asgi, bundle = main()
        print("Level:", int(app.level), f"({{app.level.label}})")
        print("Host ASGI:", type(asgi).__name__ if asgi is not None else None)
        print("Surfaces:", list(bundle.surfaces.keys()) if bundle else [])
        print("Routes:", [r.get("path") for r in (bundle.route_table or [])] if bundle else [])
        try:
            ops = app.dispatch("hello.inc")
            for op in ops:
                print(" ", op)
        except Exception as exc:
            print(" dispatch:", exc)
        report = doctor([], fail=False, bundle=bundle, app=app)
        print("Doctor surfaces:", report.surfaces)
        print("Doctor routes:", report.routes)
        if asgi is not None:
            print("Path: uxcompose serve dev")

    # ASGI attribute for uvicorn app:asgi
    _app, asgi, _bundle = main()
''')


SETTINGS_PY = dedent('''\
    """Environment SSoT — paths, debug, app asset layout.

    Document emits ``<link href=\"/css/output.css\">``. This module owns the
    disk folders. Isolation Law: Channel stays behind compose wire/.
    """
    from __future__ import annotations

    from pathlib import Path

    from ux_behavior.wire import debug_requests_dev
    from ux_compose import WebAssets

    BASE_DIR = Path(__file__).resolve().parent
    # Same switch as Channel attach: DEBUG=1/true/yes/on is dev, unset is prod.
    # uxcompose serve dev sets DEBUG=1 for its workers.
    DEBUG = debug_requests_dev()

    # FastAPI Swagger / ReDoc / OpenAPI JSON. Off so routes/docs.py can own GET /docs.
    # Opt in: OPENAPI = True, or build(openapi=True).
    OPENAPI = False

    ASSETS_DIR = BASE_DIR / "assets"
    OUTPUT_CSS = "output.css"

    # dry_run=False creates assets/static/file/css (compiler output dir)
    webassets = WebAssets(base_dir=ASSETS_DIR, dry_run=False)
''')


DOCUMENT_PY = dedent('''\
    """Document SSoT — one HTML shell for every GET.

    Document.use(XElement(), Csp.auto(), Channel.optional()) is the full
    shell (CSP + Channel client tags). Channel is the ux_dom Document-plugin
    alias — never ux_channel.Channel. Isolation: this module never imports
    ux_channel.

    HTMX is opt-in via build(use_htmx=True). Component.render() stays a
    fragment (the morph payload) — never put the stylesheet link inside render().
    """
    from __future__ import annotations

    from ux_dom import Channel, Csp, Document, XElement
    from ux_dom.dom import link, meta, title

    from settings import OUTPUT_CSS

    _plugins = (XElement(), Csp.auto(), Channel.optional())
    document = Document(
        head=[
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Hello"),
            link(href=f"/css/{OUTPUT_CSS}", rel="stylesheet"),
        ],
        body=[],
        ensure_csrf_token=False,
    ).use(*[p for p in _plugins if p is not None])
''')


ROUTES_HELLO_PY = dedent('''\
    """Page unit — module stem matches class name (hello.py → Hello).

    Author contract: return ux-dom tag trees with Tailwind className.
    control() emits data-ux-action + data-channel-action (live click bind)
    and mints a Cap when Cap Host is live. hello.inc is open mint / no Cap
    predicate (Intent still requires the control-minted cap under Cap Host
    require). hello.pulse is fail-closed (caps=("pulse.refresh",)). HTMX is opt-in at
    Document layer. render() stays a #hello fragment (the morph payload).
    Host wraps Document — never the brand bar inside render().
    """
    from __future__ import annotations

    from ux_compose import Component, MorphState, action, control, notify, update_with
    from ux_compose import div, span, button


    class Hello(Component):
        id = "hello"
        n = MorphState(0)
        pulses = MorphState(0)

        def render(self):
            n = int(self.n or 0)
            pulses = int(self.pulses or 0)
            inc_attrs = control("hello.inc")
            pulse_attrs = control("hello.pulse")
            btn = (
                "rounded-full bg-stone-900 text-stone-50 "
                "px-4 py-2 text-sm font-medium hover:bg-stone-800"
            )
            return div(
                span(str(n), className="text-2xl font-semibold tabular-nums"),
                button("+1", type="button", className=btn, **inc_attrs),
                span(str(pulses), className="text-2xl font-semibold tabular-nums"),
                button("pulse", type="button", className=btn, **pulse_attrs),
                id=self.id,
                className="flex items-center gap-3 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm",
            )

        @action(caps=())
        def inc(self):
            self.n = int(self.n or 0) + 1
            return update_with(self, extra_ops=[notify("incremented")])

        @action(caps=("pulse.refresh",))
        def pulse(self):
            self.pulses = int(self.pulses or 0) + 1
            return update_with(self, extra_ops=[notify("pulsed")])
''')


ROUTES_INDEX_PY = dedent('''\
    """Page unit — index.py → GET /. Keep /hello; the app root is not 404.

    Path law: index.py / route.py map to the folder prefix (here ``/``).
    Isolation: this module never imports ux_channel.
    """
    from __future__ import annotations

    from ux_compose import Component, a, div, p


    class Index(Component):
        id = "index"

        def render(self):
            href = "/hello"
            return div(
                p("Hello lives at /hello."),
                a("Open hello", href=href),
                id=self.id,
                className="flex flex-col gap-2 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm",
            )
''')


INPUT_CSS = dedent('''\
    @import "tailwindcss";
    @source "../../**/*.{py,html,js}";

    @layer base {
      :root {
        --bg: #f3efe6;
        --surface: #fffdf8;
        --fg: #161513;
        --accent: #2f3b38;
        --font-display: "Fraunces", Georgia, serif;
        --font-body: "Source Sans 3", system-ui, sans-serif;
      }
      html { background: var(--bg); color: var(--fg); }
      body { margin: 0; font-family: var(--font-body); }
    }

    @layer components {
    }
''')


# One ux-compose line and no specialist lines: ux-dom, ux-channel,
# ux-behavior and ux-motion arrive with the pins that ux-compose commit
# declares in its pyproject.toml, so the file cannot pin a specialist twice.
COMPOSE_GIT = "https://github.com/bitplorer/ux-compose.git"

REQUIREMENTS = dedent('''\
    {compose}
    cek-host>=0.2.0
    cek-surface>=0.2.0
    fastapi
    uvicorn[standard]
''')


SPECIALISTS = ("ux-dom", "ux-channel", "ux-behavior", "ux-motion")
# pip's own comment rule: '#' at line start or after whitespace (not in a URL fragment).
_COMMENT = re.compile(r"(^|\s+)#.*$")


def requirements_problem(text: str) -> str | None:
    """Why ``requirements.txt`` breaks create-app's one-line rule, else None.

    Each line is a PEP 508 requirement (``packaging``), one line per
    distribution, ux-compose is named, and no specialist is pinned beside
    it: a second ux-dom line is the "conflicting URLs" file pip and uv refuse.
    """
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.utils import canonicalize_name

    seen: dict[str, int] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = _COMMENT.sub("", raw).strip()
        if not line:
            continue
        try:
            name = canonicalize_name(Requirement(line).name)
        except InvalidRequirement:
            return f"line {number} is not a requirement: {line!r}"
        if name in seen:
            return f"lists {name} twice (lines {seen[name]} and {number}); one line per distribution"
        seen[name] = number
    if "ux-compose" not in seen:
        return "does not name ux-compose"
    pinned = [name for name in SPECIALISTS if name in seen]
    if pinned:
        return (
            f"pins {', '.join(pinned)} beside ux-compose; "
            "specialists come with the ux-compose line"
        )
    return None


class ComposeRefError(RuntimeError):
    """create-app cannot tell which ux-compose the requirements should pin."""


def _git(checkout: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(checkout), *args],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


_SUPPORTED_INSTALLS = (
    "create-app supports two ux-compose installs: git at a commit "
    f"(pip install 'ux-compose @ git+{COMPOSE_GIT}@<sha>') or an editable git "
    "checkout (pip install -e <checkout>). Install one, then rerun."
)


def compose_requirement() -> tuple[str, str | None]:
    """The requirement line for the running ux-compose, and a note to print.

    - VCS install: the ``direct_url.json`` commit (PEP 610).
    - Editable or local-directory install: that checkout's ``HEAD``.
    - Remote archive: its URL.

    No ux-* package is on an index, so a record without ``direct_url.json``
    (an index install, or ``PYTHONPATH=src`` finding a stale egg-info) and
    everything else raise ``ComposeRefError``.
    """
    # PYTHONPATH=src also finds the checkout's egg-info, which has no
    # direct_url.json; the installed record is the one that says where from.
    raw = next(
        (
            text
            for d in metadata.distributions(name="ux-compose")
            if (text := d.read_text("direct_url.json"))
        ),
        None,
    )
    if raw is None:
        raise ComposeRefError(
            "create-app: ux-compose has no install record (direct_url.json), so "
            "requirements.txt has nothing to pin. " + _SUPPORTED_INSTALLS
        )
    info = json.loads(raw)
    url = info.get("url", "")
    vcs = info.get("vcs_info") or {}
    if vcs.get("commit_id"):
        line = f"ux-compose @ {vcs['vcs']}+{url}@{vcs['commit_id']}"
        if info.get("subdirectory"):
            line += f"#subdirectory={info['subdirectory']}"
        return line, None
    if "dir_info" in info and url.startswith("file:"):
        checkout = Path(url2pathname(urlparse(url).path))
        sha = _git(checkout, "rev-parse", "HEAD")
        if sha:
            dirty = bool(_git(checkout, "status", "--porcelain", "--untracked-files=no"))
            note = (
                f"create-app: ux-compose is a local checkout ({checkout}); "
                f"requirements.txt pins its HEAD {sha}"
                + (" (uncommitted changes are not in it)" if dirty else "")
                + ". Push that commit before you install from requirements.txt."
            )
            # Warn, not refuse: scaffolding from an unpushed checkout is the
            # normal dev and CI loop, and the file resolves once HEAD is pushed.
            if not _git(checkout, "branch", "-r", "--contains", sha):
                note = (
                    f"WARNING: create-app: {sha} is on no remote branch, so "
                    "requirements.txt will not resolve anywhere until you push it.\n"
                    + note
                )
            return f"ux-compose @ git+{COMPOSE_GIT}@{sha}", note
    if "archive_info" in info and not url.startswith("file:"):
        return f"ux-compose @ {url}", None
    raise ComposeRefError(
        f"create-app: ux-compose was installed from {url} with no commit, so "
        "requirements.txt has nothing to pin. " + _SUPPORTED_INSTALLS
    )


README = dedent('''\
    # {name}

    Progressive ux-compose app (level={level_repr}, host={host}).

    ## Mental model

    - `settings.py` — environment (BASE_DIR, DEBUG, WebAssets on ux-compose)
    - `document.py` — Document SSoT + `.use(XElement, Csp, Channel.optional)`
    - `app.py` — composition root: `build(host=, live=, level=, document=, wrap=, cek=)`
    - `routes/index.py` — GET `/` (index alias; keep `/hello`)
    - `routes/hello.py` — page unit (`render()` is a fragment; host wraps Document)
    - `assets/css/input.css` — Tailwind tokens; compile with `uxcompose build`

    ## Composition root

    ```python
    from ux_compose.build import build
    {readme_chrome_import}from document import document
    app, asgi, bundle = build(
        Path(__file__).parent,
        host="{host}",   # auto | fastapi | asgi
        live="auto",     # auto | channel | null
        level={level_repr_py},
        document=document,
        wrap={wrap_expr},
        cek="require",   # product Cap Host via App.use_cek (skip if live=null)
    )
    ```

    Host is set **only** in `build(host=...)` — swap without rewriting page units.

    Brand bar (optional): `wrap=brand_wrap(document, brand="Acme")`
    from `ux_compose.brand`. Keep `render()` a fragment — never put nav brand
    inside `routes/*.py`.

    ## Product path

    One Product. Python ≥ 3.14 with the pinned specialist stack.
    `pip install -r requirements.txt` is enough.

    Isolation: never import `ux_channel`.

    ```bash
    pip install -r requirements.txt
    uxcompose serve dev
    uxcompose build
    uxcompose serve prod
    uxcompose deploy --provider docker
    uxcompose doctor .
    ```

    `uxcompose serve dev` sets dev mode (`DEBUG=1`) and one channel secret
    for its workers. Unset `DEBUG` is prod: `uxcompose build`, `serve prod`
    and deploys need `UX_CHANNEL_SECRET` (≥16 chars, never commit it), or
    `DEBUG=1` for a local build.

    `uxcompose build` finds and runs the Tailwind CLI (`ux_compose.tailwind`).
    Output: `assets/static/file/css/output.css`, linked as `/css/output.css`.

    ## Laws

    - Isolation: product modules never import `ux_channel` or CEK
    - Cap Law: protected actions fail closed (`strict_caps=True` is the default)
    - HTMX is opt-in (`use_htmx=True` in main)
    - Progressive Superpower: complete install first; this Level 1 page unit
      stays correct at L2/L3 (levels are additive)
''')


class ReservedDestError(ValueError):
    """create-app dest basename collides with a stdlib module or keyword."""


_DEST_SUGGEST = "fullsite, app, or web"
# CPython omits ``test`` from ``sys.stdlib_module_names`` (the regression
# package is optional), but ``import test.routes`` still shadows it.
_ALWAYS_RESERVED = frozenset({"test"})


def _dest_basename(dest: str | Path) -> str:
    return Path(dest).name


def reserved_dest_reason(basename: str) -> str | None:
    """Return a teaching message when ``basename`` would shadow stdlib / keywords."""
    name = (basename or "").strip()
    if not name:
        return None
    key = name.lower()
    stdlib = {m.lower() for m in getattr(sys, "stdlib_module_names", ())}
    reserved = key in _ALWAYS_RESERVED or key in stdlib
    reserved = reserved or keyword.iskeyword(name) or keyword.iskeyword(key)
    if reserved:
        return (
            f"create-app destination {name!r} is a reserved Python name "
            f"(stdlib module or keyword). Importing {name}.routes would hit "
            f"the standard library. Use a different folder, for example {_DEST_SUGGEST}."
        )
    return None


def create_app(
    dest: str | Path,
    *,
    name: str = "myapp",
    level: int | str = "auto",
    host: str = "auto",
    brand: str | None = None,
) -> Path:
    """Create a progressive app with locked product path.

    host: ``auto`` | ``fastapi`` | ``asgi`` — gateway at composition root only.
    level: ``auto`` or 0..3 attach level (complete install; hard-deps).
    brand: optional GET-only nav label via ``brand_wrap`` (Document path).
      ``None`` keeps ``wrap=document``. Never embeds the brand bar in ``render()``.
    """
    reason = reserved_dest_reason(_dest_basename(dest))
    if reason:
        raise ReservedDestError(reason)

    compose, note = compose_requirement()
    if note:
        print(note, file=sys.stderr)

    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)

    host_l = (host or "auto").lower()
    if host_l not in ("auto", "fastapi", "asgi"):
        host_l = "auto"

    if isinstance(level, str) and level.lower() == "auto":
        level_repr = "auto"
        level_boot = '"auto"'
        level_repr_py = '"auto"'
    else:
        lv = max(0, min(3, int(level)))
        level_repr = str(lv)
        level_boot = str(lv)
        level_repr_py = str(lv)

    brand_label = str(brand).strip() if brand else ""
    if brand_label:
        chrome_import = "from ux_compose.brand import brand_wrap\n"
        wrap_expr = f"brand_wrap(document, brand={brand_label!r})"
        readme_chrome_import = "from ux_compose.brand import brand_wrap\n"
    else:
        chrome_import = ""
        wrap_expr = "document"
        readme_chrome_import = ""

    (root / "app.py").write_text(
        APP_PY.format(
            name=name,
            level_repr=level_repr,
            level_boot=level_boot,
            host=host_l,
            chrome_import=chrome_import,
            wrap_expr=wrap_expr,
        ),
        encoding="utf-8",
    )
    (root / "settings.py").write_text(SETTINGS_PY, encoding="utf-8")
    (root / "document.py").write_text(DOCUMENT_PY, encoding="utf-8")
    (root / "README.md").write_text(
        README.format(
            name=name,
            level_repr=level_repr,
            level_repr_py=level_repr_py,
            host=host_l,
            wrap_expr=wrap_expr,
            readme_chrome_import=readme_chrome_import,
        ),
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text(
        REQUIREMENTS.format(compose=compose), encoding="utf-8"
    )

    routes = root / "routes"
    routes.mkdir(exist_ok=True)
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "index.py").write_text(ROUTES_INDEX_PY, encoding="utf-8")
    (routes / "hello.py").write_text(ROUTES_HELLO_PY, encoding="utf-8")

    css_dir = root / "assets" / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    (css_dir / "input.css").write_text(INPUT_CSS, encoding="utf-8")
    from ux_compose.assets import WebAssets

    WebAssets.from_app_root(root, dry_run=False)

    return root


__all__ = [
    "ComposeRefError",
    "ReservedDestError",
    "SPECIALISTS",
    "compose_requirement",
    "create_app",
    "requirements_problem",
    "reserved_dest_reason",
]
