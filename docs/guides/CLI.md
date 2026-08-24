# CLI ownership (hard cut)

> **Diátaxis:** how-to · **Canonical:** `docs/guides/CLI.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

| CLI | Owns |
|-----|------|
| **`uxcompose`** | **Sole product lifecycle:** create-app, serve, deploy, doctor |
| **`uxdom`** | Pure Document tooling only: doctor, lint, build, profile |

## Product path (only)

```bash
uxcompose create-app myapp --host auto --level auto
cd myapp
uxcompose serve app:asgi --port 8080
uxcompose deploy --provider docker
uxcompose doctor .
```

## Pure-dom tooling

```bash
uxdom doctor
uxdom lint
uxdom build
uxdom profile
```

`uxdom create-app` / `serve` / `deploy` are **removed from the product path**.
See `docs/FLOW.md`.

## Production CSS

`uxdom build` minifies Tailwind when the tree has `app/main.py` and
`assets/css/input.css` → `assets/static/file/css/output.css`. Product apps from
`uxcompose create-app` have `app.py` at the root — compile with the CLI
directly, then deploy the file:

```bash
python -m pytailwindcss \
  -i assets/css/input.css \
  -o assets/static/file/css/output.css \
  --minify
uxcompose deploy --provider docker
```

`uxcompose serve` watches `.css` (HMR). It does not compile.
`uxcompose deploy` does not run Tailwind. Full how-to: [TAILWIND.md](TAILWIND.md).
