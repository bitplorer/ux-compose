# CLI ownership (hard cut)

> **Diátaxis:** how-to · **Canonical:** `docs/guides/CLI.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

| CLI | Owns |
|-----|------|
| **`uxcompose`** | **Sole product lifecycle:** create-app, **build** (incl. Tailwind CLI finder), serve, deploy, doctor |
| **`uxdom`** | Pure Document tooling: doctor, lint, profile, add. WebAssets *paths*. |

## Product path (only)

```bash
uxcompose create-app myapp --host auto --level auto
cd myapp
uxcompose build
uxcompose serve app:asgi --port 8080
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

`uxdom create-app` / `serve` / `deploy` are **removed from the product path**.
`uxdom build` is Document/static verify for leftover `app/main.py` showcase
trees — it does **not** compile CSS. Product apps use `uxcompose build`.
See `docs/FLOW.md`.

`uxcompose serve` watches `.css` (HMR). It does not compile.
`uxcompose deploy` does not run Tailwind; run `uxcompose build` first so
`output.css` is on disk. Full how-to: [TAILWIND.md](TAILWIND.md).
