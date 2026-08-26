# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- **Product FastAPI host (Clock A).** `routing/host.py` owns process order
  (`open` then `bind`). `routing/fastapi.py` owns page GET:
  resolve → render → `document()` → `HTMLResponse`. DirectoryASGI is the
  no-Starlette degrade (still wraps `document()`). ADR:
  [docs/adr/0002-product-host.md](docs/adr/0002-product-host.md).

### Changed

- `App.boot("auto")` is Level 1. Channel attaches in `build()` on the real
  ASGI process; `use_channel(asgi_app=)` rebinds if a headless wire landed
  first. `Behavior.attach` is no longer passed a nonexistent `channel_config=`.
- Page units have no HTTP verbs. One path law (`http_path`): `index.py` /
  `route.py` → `/`, `[param]` → `{param}`. Scaffold `Hello` is `render()` only.
- `host="batteries"` (leftover ux-dom DirectoryRouter) fails closed.
- FastAPI is not given an HTML `default_response_class` — author JSON routes
  stay JSON. Page `render()` that returns a `dict` is JSON automatically
  (payload type picks media type; HTML strings stay HTML). Streaming is a
  return value, not a route class.
- **Docs:** teaching pages no longer name leftover `uxdom build` / DirectoryRouter /
  `host=batteries` as something to run. Stub cites (`docs/CLI.md`, `docs/DX.md`,
  `docs/TESTING.md`) point at `docs/guides/`. Product path is the only path taught.

## [0.1.0] — 2026-08-24

### Added

- Community health files: Code of Conduct, Security, Support, Governance, issue and pull-request templates.
- Standard Readme README with canonical (non-stub) doc links.
- Documentation contract: [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).
- Product `uxcompose build` — CSS minify via `ux_compose.tailwind`. App folders: `ux_compose.assets.WebAssets`. ux-dom keeps className + `<link>` + package static.
- `create-app` teaching surface: `settings.py`, `document.py`, `assets/css/input.css`, `requirements.txt`.
- Tailwind CLI finder / download / ensure moved here (`ux_compose.tailwind`). ux-dom does not compile CSS (`TailwindCommand` fail-closed).
- Product path fail-closed: `build()` honors `level` / `live=null`; `WebAssets.mount_css` wraps DirectoryASGI (no silent `/css` 404); discover CSS is pure (no leftover `app/tailwindcss.py` branch); `uxcompose doctor` prints the teaching report; browser HMR is opt-in (`--hmr`); product root is `app.py` only.
- `serve="dual_copy"` is the package-static escape hatch name (`serve="webassets"` remains a leftover alias). Not `WebAssets`.

### Changed

- Product path is `create-app → build → serve → deploy`. `uxdom build` does not compile CSS.
