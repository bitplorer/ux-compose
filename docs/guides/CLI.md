# CLI ownership (hard cut)

> **Diátaxis:** how-to · **Canonical:** `docs/guides/CLI.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

| CLI | Owns |
|-----|------|
| **`uxcompose`** | **Sole product lifecycle:** create-app, **build** (Tailwind CLI + `WebAssets` folders), serve, deploy, doctor |
| **`uxdom`** | Pure Document tooling: doctor, lint, profile, add. Package static. |

## Product path (only)

```bash
uxcompose create-app myapp --host auto --level auto
cd myapp
uxcompose serve dev
uxcompose build
uxcompose deploy --provider docker
uxcompose doctor .
```

`uxcompose build` minifies Tailwind via `ux_compose.tailwind`
(`discover_css_io` / `resolve_tailwind` / `argv_with_io`) to
`assets/static/file/css/output.css`. create-app already emits
`assets/css/input.css`, the Document `<link href="/css/output.css">`,
and the `/css` mount.

## Pure-dom tooling

```bash
uxdom doctor
uxdom lint
uxdom profile
uxdom add component Card
```

Product apps use `uxcompose build` for CSS. ux-dom does not compile CSS.
See `docs/FLOW.md`.

`uxcompose serve dev` turns every clock on: process reload (`*.py`),
browser HMR, sibling Tailwind `--watch`. `uxcompose serve prod` turns
every clock off and serves whatever `output.css` is on disk. There is
no `--hmr` / `--css-watch` flag to forget. `uxcompose serve` without a
mode exits 2. `uxcompose build` is the one-shot minify. Deploy runs
raw uvicorn, not `serve`. Full how-to: [TAILWIND.md](TAILWIND.md).
