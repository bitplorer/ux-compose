# CLI ownership (hard cut)

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
