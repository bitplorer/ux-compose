# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- **Product FastAPI host (Clock A).** `routing/host.py` owns process order
  (`open` then `bind`). `routing/fastapi.py` owns page GET. DirectoryASGI is
  the no-Starlette degrade. ADR:
  [docs/adr/0002-product-host.md](docs/adr/0002-product-host.md).
- **Host spec.** Payload law, path law, created-app layout, file map, CSP
  layers, wrap-vs-mount, and future protocol:
  [docs/reference/host.md](docs/reference/host.md). Author recipes:
  [docs/guides/HOST.md](docs/guides/HOST.md).


### Changed

- `App.boot("auto")` is Level 1. Channel attaches in `build()` on the real
  ASGI process; `use_channel(asgi_app=)` rebinds if a headless wire landed
  first. `Behavior.attach` is no longer passed a nonexistent `channel_config=`.
- Page units have no HTTP verbs. One path law (`http_path`): `index.py` /
  `route.py` → `/`, `[param]` → `{param}`. Scaffold `Hello` is `render()` only.
- `host="batteries"` (leftover ux-dom DirectoryRouter) fails closed.
- FastAPI is not given an HTML `default_response_class` — author JSON routes
  stay JSON. Page `render()` that returns a `dict` is JSON automatically;
  a generator / async generator is `StreamingResponse` automatically
  (payload type picks media type; HTML strings stay buffered HTML).
  Leftover `StreamingRoute` is not the product path.
- GET wrap uses the author `document=` only. A synthesized Document is
  mount-only (CSP/static). HTML strings go through `apply_html_document`
  (`raw()`), so a positional str is never treated as a script `src`.
- `attach_motion()` returns instances (`Motion()`, `MotionChannel()`).
  Passing the class made `document.mount` call `served_files()` unbound.
- `App.mount` / `attach_page_router` pass `wrap=` (author Document) the same
  way `build()` does. A synthesized Document never wraps GET.
- `App.dispatch("x", args={...})` unpacks Channel-style Intent payloads
  (also in ux-behavior `bind_action_args`, which binds the @action function
  not `BoundAction.__call__(*args)`). Clock A tests speak ASGI (no
  Starlette TestClient / httpx2).
- `materialize(route_class=)` / `mount(route_class=)` fail closed.
- Scaffold no longer emits leftover `page()`. Host wraps `render()` with the
  author Document. Motion Scene IR becomes `transition.play`.
- `_is_response` recognizes FileResponse / RedirectResponse / body_iterator.
- **Docs:** teaching pages no longer name leftover `uxdom build` / DirectoryRouter /
  `host=batteries` as something to run. Stub cites (`docs/CLI.md`, `docs/DX.md`,
  `docs/TESTING.md`) point at `docs/guides/`. Product path is the only path taught.
- CI pins ux-behavior / ux-motion / ux-channel / ux-dom to origin/main SHAs;
  leftover `httpx2` is gone. Teaching is `create-app` + `build()` (`App.mount`
  is a secondary door). Clock A GET asserts `Content-Security-Policy` when
  Document mounts Csp.


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
