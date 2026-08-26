# Production CSS — Tailwind

> **Diátaxis:** how-to · **Layer:** ux-compose (`ux_compose.tailwind` owns the compiler)
> Map: [../INDEX.md](../INDEX.md) · Tutorial: [PATH.md](PATH.md) §5
> Assets contract: [../../assets/README.md](../../assets/README.md)

**Job:** ship a minified stylesheet that contains only the utilities your Python
trees use, then serve that file. The browser never talks to a Tailwind CDN.

If code and this page disagree, **code wins**.

---

## Laws

1. Author utilities on the tree: `className="rounded-2xl border …"`.
2. Tokens and `@layer components` live in `assets/css/input.css`. Never CSS or
   client JS inside Python strings. Never `style(raw(CSS))`.
3. The Document **links** the generated file. It does not inline it.
4. Production compiles with `--minify`. Dev watches. Those flags are XOR.
5. `cdn.tailwindcss.com` is not the product path (`apps/pulse` is a demo).

`uxcompose create-app` stamps Tailwind `className` on Hello **and** emits
`assets/css/input.css`, a Document stylesheet link (`/css/output.css`), and
a `/css` mount from WebAssets. Compile with `uxcompose build`.

---

## Pipeline

| Step | Who | Artifact |
|------|-----|----------|
| 1. Author | you, on the tag tree | `className="…"` in `routes/*.py` |
| 2. Tokens | you, in CSS | `assets/css/input.css` |
| 3. Compile | Tailwind CLI via **uxcompose build** | `assets/static/file/css/output.css` (minified) |
| 4. Link | one Document | `link rel=stylesheet href=/css/output.css` |
| 5. Mount | FastAPI / ASGI host | `/css` → that directory |
| 6. Deploy | you, before or in the image | the minified file is on disk when uvicorn starts |

```text
className on trees
        |
        v
assets/css/input.css     <- tokens, @source / content globs
        |
        v
Tailwind CLI --minify    <- uxcompose build (ux_compose.tailwind finder + ensure)
        |
        v
assets/static/file/css/output.css
        |
        +-- Document links  /css/output.css
        +-- host mounts     /css  ->  that folder
```

`uxcompose serve --hmr` watches `.css` and reloads the browser. It does **not**
compile Tailwind. `uxcompose deploy` writes a Dockerfile that copies the tree
and runs uvicorn. It does **not** run the compiler. Production CSS is
`uxcompose build`, not a side effect of serve or deploy.

---

## 1. Author on the tree

Same classes FastAPI authors put on templates. The tree is Python.

```python
from ux_compose import div, button, control

tree = div(
    button(
        "+1",
        type="button",
        className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50",
        **control("hello.inc"),
    ),
    id="hello",
    className="rounded-2xl border border-stone-200 bg-white p-6",
)
```

`Component.render()` stays a **fragment** (the morph payload). Do not put the
stylesheet link inside `render()`.

---

## 2. Tokens and scan roots

Create `assets/css/input.css`. `uxcompose create-app` already writes this
v4 CSS-first entry. Compose pins the standalone CLI at **v4.1.12**
(`ux_compose.tailwind.TAILWIND_STANDALONE_VERSION`):

```css
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
}

@layer components {
  /* named pieces that are not one-off utilities */
}
```

`@source` is how v4 sees `className` in Python. For a `create-app` tree, keep
the glob covering `app.py` and `routes/`. A `tailwind.config.js` is optional on
v4; if you add one, scan the product files, not the library's demo globs:

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app.py", "./routes/**/*.{py,html,js}"],
  theme: { extend: {} },
  plugins: [],
};
```

v3 `@tailwind base/components/utilities` still compiles. Prefer the v4 entry
above so you match the CLI compose downloads.

---

## 3. Compile for production

**Output path is fixed** by `ux_compose.tailwind.discover_css_io`
(matches `ux_compose.assets.WebAssets.static.css`):

| Role | Path |
|------|------|
| Input | `assets/css/input.css` (fallback `assets/input.css`) |
| Output | `assets/static/file/css/output.css` |

`--minify` in production. `--watch` in dev. Not both
(`argv_with_io`: minify wins, else watch).

### Product command

```bash
uxcompose build
# --watch for dev (XOR with minify)
# --skip-tailwind / --skip-import for structure-only checks
```

Runs `ux_compose.tailwind` (`discover_css_io` / `resolve_tailwind` /
`argv_with_io`). Output is always `assets/static/file/css/output.css`.
create-app already emits `assets/css/input.css`.

Same argv, if you want the raw CLI:

```bash
python -m pytailwindcss \
  -i assets/css/input.css \
  -o assets/static/file/css/output.css \
  --minify
```

### How the CLI is found

`ux_compose.tailwind.resolve_tailwind` (first hit wins):

1. `UXCOMPOSE_TAILWIND` (alias `UXDOM_TAILWIND`) or `TAILWINDCSS`
2. `tailwindcss` on PATH
3. `pytailwindcss` (`pip install pytailwindcss`)
4. local `node_modules/.bin` / `@tailwindcss/cli` (never implicit npx here)
5. cached official standalone under `$XDG_CACHE_HOME/ux-compose/` (v4.1.12)
   (also reads leftover `$XDG_CACHE_HOME/ux-dom/` binaries)
6. download that standalone (`ensure=True`; `UXCOMPOSE_TAILWIND_DOWNLOAD=0` disables)
7. last resort: `npx --yes @tailwindcss/cli`

`uxcompose build` uses `ensure=True`. A missing CLI is a real error, not a skip.
Product compile is here.

Dev watch (do not ship this process):

```bash
python -m pytailwindcss \
  -i assets/css/input.css \
  -o assets/static/file/css/output.css \
  --watch
```

`uxcompose build --watch` in dev, `uxcompose build` (minify) in production.
Not both. `TailwindStyle` on ux-dom fails closed — do not compile from
Document lifespan. The CLI is the only compiler.

---

## 4. Link and mount

The generated file is served as **`/css/output.css`**.

Product apps mount `WebAssets.static.css` (`assets/static/file/css`) at `/css`
and link it from the Document. `href` is a string — Document does not take a
`webassets=` field.

```python
from pathlib import Path
from ux_compose import WebAssets
from ux_dom import Document
from ux_dom.dom import link, meta, title

ROOT = Path(__file__).resolve().parent
webassets = WebAssets(base_dir=ROOT / "assets", dry_run=False)

document = Document(
    head=[
        meta(charset="utf-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1"),
        title("Shop"),
        link(href="/css/output.css", rel="stylesheet"),
    ],
    body=[],
    ensure_csrf_token=False,
)

# after build() / FastAPI()
webassets.mount_css(asgi)  # /css → assets/static/file/css
# document.mount(asgi) is host.bind — do not call it from app.py
```

`create-app`'s `build(document=)` attaches the Document from `document.py`
(head already has the `/css/output.css` link). `host.bind` calls
`document.mount(asgi)` (CSP + package static). `app.py` only needs
`webassets.mount_css(asgi)` for `/css`.

Atelier demos link a **static snapshot** (`/static/css/atelier.css`) until
those hosts are full product apps. Prefer `input.css` → `output.css`.

---

## 5. First paint vs morph

| Call | Must return | Why |
|------|-------------|-----|
| `Component.render()` | fragment with `id=` | morph payload; XOR with motion HTML |
| HTTP GET | Document wrapping the fragment | browser needs the stylesheet |

Proven hosts:

- **ux-dom showcase** — `page(*body)` is `Document(head=[link...])(*body)` from
  the route, not from `render()`.
- **atelier_*** — the ASGI host builds `html(head(link(...)), body(unit.render()))`.

Do **not** add `link(...)` inside `render()`. `update_with` republishes
`render()` HTML; the morph target is `#hello`, not the shell.

`uxcompose create-app` GET wraps `render()` with the author Document (host.bind `wrap=`).
The morph payload remains `render()` — never put `link(...)` inside it.

---

## 6. Deploy

Default `uxcompose deploy --provider docker` writes:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "uvicorn[standard]" fastapi ux-compose ux-dom ux-behavior
COPY . .
CMD ["sh", "-c", "uvicorn app:asgi --host 0.0.0.0 --port ${PORT:-8080}"]
```

No Tailwind in that image. Pick one:

### A. Compile before the image (simplest)

```bash
uxcompose build
```

Commit `output.css` (or copy it in CI). `COPY . .` ships the bytes. The
running image does not need a Tailwind binary. Fly / Render / Railway / VPS
templates from `uxcompose deploy` are the same: they start uvicorn, they do
not compile CSS. `uxcompose deploy` prints this reminder.

### B. Compile in the image

Add a build step **after** `COPY . .` so `@source` / content globs still see
`routes/*.py`:

```dockerfile
RUN pip install --no-cache-dir pytailwindcss \
 && python -m pytailwindcss \
      -i assets/css/input.css \
      -o assets/static/file/css/output.css \
      --minify
```

Do not run `--watch` in the image. Do not install Node only to compile CSS;
`pytailwindcss` is the Python-native binary the resolver already prefers
after PATH.

### C. CI artifact

Same minify command in GitHub Actions (or equivalent). Upload `output.css`.
The deploy job copies it next to the app. Image stays slim.

Set `DEBUG=false` on the host either way (`uxdom` doctor warns if it stays
true). Tailwind minify is independent of that flag. Prefer a file on disk
so workers do not race the compiler. `TailwindStyle` on ux-dom fails closed.

---

## What not to do

| Tempting | Why not |
|----------|---------|
| `script src="https://cdn.tailwindcss.com"` | Playground. Ships the compiler to every visitor. Pulse demo only. |
| `style(raw("..."))` / CSS in Python strings | Assets contract. Dual palette, no minify, CSP pain. |
| `assets/css/output.css` as the **served** file without a mount | `uxcompose build` writes `assets/static/file/css/output.css`. Link `/css/output.css` to that folder. |
| `uxcompose serve` as the production compiler | HMR reloads on `.css` mtime. It never runs Tailwind. |
| `uxcompose deploy` as a CSS build | Prepares Dockerfile / fly / render / railway / vps. Run `uxcompose build` first. |
| Compiling inside `Component.render()` | Render is the morph payload. |

---

## File map (product app after this how-to)

```text
myapp/
  settings.py                    # WebAssets
  document.py                    # Document SSoT; host wraps GET + /css/output.css link
  app.py                         # build(document=) + /css mount
  routes/hello.py                # className on the fragment; host wraps Document
  assets/css/input.css           # tokens + @source
  assets/static/file/css/
    output.css                   # minified; commit or CI/image emit
  requirements.txt
```

Verify the sheet is what the browser gets: open `/css/output.css` on the
running app. It should be minified in production (one line, utilities you
used, not the full Tailwind set).
