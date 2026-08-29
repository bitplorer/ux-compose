# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Ownable kit (`uxcompose add`): login, tabs, accordion, dropdown, dialog, sheet,
  toast, command, table, pagination, combobox, sidebar, breadcrumb, stepper,
  carousel, calendar, select, otp, plans.
- Kit Wave 1 (Signal grammar): `actionsheet`, `contextmenu`, `typeahead`, `pullrefresh`.
  Tailwind `class_*` only. `data-channel-on` for swipe.vertical / longpress / input delay:.
- Kit Wave 2 (product surfaces): `rating`, `kanban`, `timeline`, `kpi`, `slider`,
  `lightbox`, `wishlist`, `progress`, `empty`, `presence`, `chips`, `skeleton`.
  Named MorphState / silent RefState. Caps on `kanban.archive` and `kpi.reset`.
  Overlay lightbox has no containing-block card. Motion is additive. Play in
  Atelier `/p/rating` … `/p/skeleton`.

### Changed

- Wave-2 kit chrome: paper card (`bg-[#fdfcf8]`, `rounded-[1.85rem]`, layered
  shadow) on rating, kanban, timeline, kpi, slider, lightbox, wishlist,
  progress, empty, presence, chips, skeleton. Inner composition is distinct
  per unit (gold rating well, lane-color kanban rails, KPI ink tile, slider
  thumb, lightbox hero + film-strip ring, filled wishlist heart, pulsing
  progress dot, phase wells, overlapping presence stack, material chip
  tokens, skeleton that matches the ready card). Overlay lightbox card still
  has no `relative` / overflow. Encoding, ids, Caps, and action names
  unchanged.

- Typeahead: `input delay:300`. Later `input`/`change` of the same
  control aborts the in-flight Intent (Channel AbortController on
  `postIntent`). Live Results morph `#typeahead-hits` only — the field
  (`#typeahead-q`) is not in that HTML, so a pause-fired Result cannot
  rewrite what is still being typed. Pick still morphs the card so the
  name can land in the field. No kit JS. No companion CSS.

- Dialog: card drops `relative` / overflow so a `fixed` overlay is not remapped
  or clipped on a narrow stage. Swipe lives on Keep it
  (`click swipe.down`), not a root swipe and not Delete (Cap). Panel, scrim,
  dismiss and confirm keep stable ids. Open composes a Motion enter plan
  (fade scrim, rise panel) — selectors only, no Channel attr, no kit JS.
  Cancel / confirm are morph-only: after apply the panel is gone.
- Sheet: card drops `relative` / overflow so a `fixed` overlay is not remapped
  or clipped on a narrow stage. Swipe lives on Close / Done
  (`click swipe.right`), not a root `swipe.horizontal`. Panel, scrim,
  dismiss and done keep stable ids. Open composes a Motion enter plan
  (fade scrim, slide panel) — selectors only, no Channel attr, no kit JS.
  Close is morph-only: after apply the panel is gone.
- ContextMenu: floating panel (`list-none`, no native ul tab), overlays the
  canvas, card no longer `overflow-hidden` (that clipped the menu). Rows are
  `menuitem`. Root stamps `data-channel-id`.
- Pagination: windowed numbers, not one button per page. Host seam `WINDOW`
  (neighbors each side, default 1). Sliding core is always visible. First /
  last + gaps are `max-sm:hidden` so page 1 cannot sit on Prev on a phone.
  Prev is one named page back (p6 → p5), disabled on the first page. 44px
  chevrons on one nowrap row. Demo has 12 named pages.
- ActionSheet: 3-door. Card drops `relative` / overflow so a `fixed`
  overlay is not remapped or clipped. Swipe lives on the handle and
  Cancel (`click swipe.down`), not a root `swipe.vertical` (that swallowed
  row clicks). Panel, scrim, dismiss and cancel keep stable ids. Open
  composes a Motion enter plan (fade scrim, slide panel) — selectors
  only, no Channel attr, no kit JS. Close / pick are morph-only: after
  apply the panel is gone.
- Carousel chrome: Prev / Next overlay the stage (44px chevrons, left / right).
  Dots overlay a locked `h-72` stage so unequal title wrap cannot
  translate the rail. One `#id-thumb` pip translates across equal slots
  (`transition-transform` / `translate3d`), so the active indicator
  coalesces into the next instead of jumping. Root stamps
  `data-channel-id` so the slot is `#id` and `[data-channel-id]` together.
  No wrapping text bar — that stacked the buttons on a narrow card.
  Copy is the live region (chrome is not). Dots label the slide title.
  Prev / next / dots keep stable ids across morph.
- Carousel / Lightbox / Drawer: `data-channel-on` swipe + directional slide/rise/fade.
- Accordion open uses `maybe_plan`; Confirm overlay open uses rise.
- `act(..., on=)` and `maybe_slide` in `examples/_common.py` (already on main).


## [0.1.0] — 2026-08-26

This is **0.1**. Clock A is the product host for this version, not a rewrite
and not a 0.2 line.

### Added

- **Product FastAPI host (Clock A).** `routing/host.py` owns process order
  (`open` then `bind`). `routing/fastapi.py` owns page GET. DirectoryASGI is
  the no-Starlette degrade. ADR:
  [docs/adr/0002-product-host.md](docs/adr/0002-product-host.md).
- **Host spec.** Payload law, path law, created-app layout, file map, CSP
  layers, wrap-vs-mount, and future protocol:
  [docs/reference/host.md](docs/reference/host.md). Author recipes:
  [docs/guides/HOST.md](docs/guides/HOST.md).
- Community health files: Code of Conduct, Security, Support, Governance, issue and pull-request templates.
- Standard Readme README with canonical (non-stub) doc links.
- Documentation contract: [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).
- Product `uxcompose build` — CSS minify via `ux_compose.tailwind`. App folders: `ux_compose.assets.WebAssets`. ux-dom keeps className + `<link>` + package static.
- `create-app` teaching surface: `settings.py`, `document.py`, `assets/css/input.css`, `requirements.txt`.
- Tailwind CLI finder / download / ensure moved here (`ux_compose.tailwind`). ux-dom does not compile CSS (`TailwindCommand` fail-closed).
- Product path fail-closed: `build()` honors `level` / `live=null`; `WebAssets.mount_css` wraps DirectoryASGI (no silent `/css` 404); discover CSS is pure (no leftover `app/tailwindcss.py` branch); `uxcompose doctor` prints the teaching report; browser HMR is opt-in (`--hmr`); product root is `app.py` only.
- `serve="dual_copy"` is the package-static escape hatch name (`serve="webassets"` remains a leftover alias). Not `WebAssets`.

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
- Product path is `create-app → build → serve → deploy`. `uxdom build` does not compile CSS.
