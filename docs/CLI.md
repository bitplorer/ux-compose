# CLI ownership (residual-free)

| CLI | Owns | Does not own |
|-----|------|----------------|
| **`uxcompose`** | Product scaffold, serve, product doctor | DOM serialize / pure Document tooling |
| **`uxdom`** | Pure-dom doctor/lint/build/profile, optional legacy scaffold | Product app path |

## Product path (only)

```bash
uxcompose create-app myapp --host auto --level auto
cd myapp
uxcompose serve app:asgi --port 8080
uxcompose doctor .
```

## Pure-dom tooling

```bash
uxdom doctor
uxdom lint
uxdom build
# uxdom create-app  → not the product path; prefer uxcompose create-app
```

See `docs/FLOW.md`.
