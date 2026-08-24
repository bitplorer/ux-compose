# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
