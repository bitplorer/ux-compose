# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- `uxcompose build --check` verifies without writing anything (no CSS,
  no bundle, no Tailwind cache change, no `__pycache__`; it passes on a
  read-only tree): `app.py`; `tailwind` compiles to a temp file and FAILs
  when `output.css` differs from it (stale) or is missing, never
  downloading or repairing the cached CLI
  (`resolve_tailwind(read_only=True)`); the `doctor` law scan; and
  `package`, every `--package` check (file set, `doctor --prod`, import
  from the bundle alone, then ASGI lifespan startup (a failure, an
  exception or a 30 s hang FAILs) and an in-process `GET
  /ux-dom/static/x_element.js` and `/css/output.css` that must return 200
  with a JS/CSS content-type, so a library-JS 404 FAILs `--package` too;
  ux-compose pin) on a copy in the system temp dir, with the same one-line FAIL messages. Exit 1 on any FAIL. It does
  not import the source tree. `--package`, `--archive`, `--out`, `--name`
  and `--skip-import` with `--check` exit 2. Library:
  `ux_compose.cli.package.check_bundle`. The "no product app found" error
  for an `app/main.py` tree now says to start one with
  `uxcompose create-app`. A guard test keeps sources and docs on
  `uxcompose build` and on package static `/ux-dom/static/x_element.js`
  as the only library JS source.

- `uxcompose build --package` writes a runnable bundle to `dist/<name>/`
  (`--out`, `--name`) after every build step passes; `--archive` adds a
  byte-identical `dist/<name>.tar.gz` (sorted members, one `<name>/` root,
  uid/gid 0, mtime `SOURCE_DATE_EPOCH` or 0). The bundle is an allowlist:
  root `*.py`, `requirements.txt`, `README.md`, existing deploy files, and
  source/asset/config file types under `routes/`, `components/`, `assets/`
  and `deploy/`, plus every `*.py` under the app root (`lib/`, nested
  packages); every other file is left out and listed. Before the bundle
  is moved into place, `python -I -B` imports the entry from a copy of it
  alone, and a failure refuses the build. Generated:
  `run.sh` (`exec uvicorn app:asgi --app-dir .`, one-line secret refusal
  before boot), `README.RUN.txt`, `MANIFEST.json` (bundle marker,
  per-file sha256, `resolved` commits for ux-compose and the four
  specialists; no absolute path, no timestamp). Refused, with nothing
  written: an `--out` that is the app, one of its parents, inside its
  source, or a non-empty directory not made of this tool's marked bundles
  (checked on the resolved path; only a marked bundle is ever replaced,
  through a temp dir and rename); a key-shaped file (`.env*`, `id_rsa*`,
  `*.pem`, `*.key`, `*.p12`, `*.pfx`, `.netrc`, `.npmrc`, private-key
  content, …; best-effort, so secrets belong in the environment) inside
  an allowed directory; any symlink in the tree;
  a `doctor --prod` FAIL row on the bundle; a ux-compose line that is not
  the running ux-compose; `-r`/`-c` includes. A dirty editable checkout
  prints a `WARNING:` line. Library:
  `ux_compose.cli.package.write_bundle`.

- `uxcompose doctor --prod` checks product readiness after the law scans:
  `product` (`app.py` at the root; an empty dir fails), `dep:uvicorn` and
  `dep:fastapi` (importable in the running interpreter), `requirements`
  (`scaffold.scan_requirements` reads the file as pip does: continuations,
  comments, option lines, `-e`, local `-r` includes; one line per
  distribution, ux-compose named, no specialist beside it; a remote `-r`
  is WARN), `secret`
  (`secret_readiness`), `DEBUG` (ux-behavior's `debug_requests_dev`),
  `.env` (WARN when present; FAIL when a Dockerfile exists and
  `.dockerignore`, read the way Docker reads it, does not exclude it), `deploy:render` and `deploy:vps` (the
  generated file declares `UX_CHANNEL_SECRET`), and with `--port N` a
  `SO_REUSEADDR` bind test on `--host` (default `0.0.0.0`; WARN). A FAIL row exits 1 unless `--no-fail`. The
  check is static: no app import, no network. `doctor` without `--prod`
  prints the same report and exit code as before. Library:
  `ux_compose.doctor.scan_product_readiness(root, *, env=None, port=None,
  host="0.0.0.0")`. `packaging` is now a declared dependency.

- CI PyPI installs use `uv pip install --exclude-newer`, set to 14 days
  before the run. `ci/check_dependency_cooldown.py` fails the job when a
  resolved distribution is younger than that. Git SHA siblings stay pinned;
  their PyPI dependencies use the same cutoff. There is no override: a
  newer dependency waits out the 14 days, or it gets an explicit pin in a
  reviewed pull request. The cutoff is CI-only. Makefile `pip install`
  targets are not under it.

- Trust now comes from `dispatch_verified(name, payload)` (one wire call after Channel accepts a Cap) or `app.trust()`, and the `_trusted` keyword is gone. `async_dispatch_verified` is the async twin. Developer-authored server code uses `app.trust()`. A bool no longer grants trust (ux-behavior #20, pin `09a9a65`).
- Outside dev, a live FastAPI attach failure fails the boot. `wire/boot.py` sets `strict_attach=True`. `use_channel` raises when attach returns no channel, and a `TypeError` from attach is not retried. A missing secret raises `RuntimeError` (`attach() requires UX_CHANNEL_SECRET or UX_BEHAVIOR_SECRET outside dev`). A 13-character secret raises `RuntimeError` from attach itself (`[ATTACH_SECRET_REQUIRED] ux_channel refuses the channel secret: capability secret must be at least 16 characters`), with or without `strict_attach`: attach checks the secret with ux-behavior's `attach_secret_problem` (pin `f12321f`, ux-behavior #22) before `Channel.boot`. A `REDIS_URL` that `Channel.boot` refuses, or anything else `attach` raises, stops the process instead of continuing without Caps. Atelier shop and studio fail at boot the same way.
- `App.dispatch` takes the action name positionally (`dispatch(self, action, /, **kwargs)`). A payload key named `action` passes through as a normal keyword.
- A posted key a named signature does not declare is a validation error (ux-behavior pin `09a9a65`), including a payload key named `self` and a host field such as `csrf`. The action does not run. The result is the ordinary validation result, never a 500. The component instance stays the component. A `**kwargs` signature does not receive that key either.
- Kit `set_field` stays on `**kwargs`, matching main. The posted control name is not stored. Restoring those fields waits on a per-visitor state decision.
- `FilterBar.choose` names `q` and does not store it, so a chip inside the query form still applies.
- `Otp.verify` clears the posted code after a successful check and on every refusal, including a code rejected for its length. The page says the secret is cleared. The refused code is not left on the shared instance. The input stays `value=""`.
- `Login.submit` uses only the password posted in that request. A missing password (`""`) is refused with "Enter your password." and does not keep a previous visitor's password. A whitespace password is a password: under 8 characters gets the length error, and 8 or more reaches `authenticate` unchanged, including leading or trailing spaces. A short password still gets the length error. A posted password, a posted OTP code, and PasswordField's secret (the lede and the type=text input, including after Reveal) are not painted back into the page. The lede is eight bullets when a secret is stored, and `empty` when it is not, so the length is not painted.
- `scripts/chrome_floor.py` is the Chrome 155 check. CI and the Login and PasswordField browser tests call that script. A major below 155, a version with no digits, a broken binary, and a missing binary exit non-zero.
- Login's password input carries `data-ux-keep-value`. The server still paints `value=""`. ux-channel @ `0ffe8e9907cd1a0701ffc8cb2e5414d6b39d2996` (#64 merge) copies the live value in that browser after Show and Hide. Password and text are one class, so Show keeps the typed password. PasswordField's secret input does not carry the mark: Hold and Hide clear the plain-text field, because Reveal is what puts the secret on screen and this field is always `type="text"`.
- `App.control` and `App.mint_cap` take the action name positionally. A payload key named `action` passes through, as it does for `App.dispatch`.

### Fixed

- The Tailwind standalone download (#120) removes its temp file on every
  exit (Ctrl-C and `SystemExit` included, not only `OSError`); on Windows,
  an `os.replace` refused because a parallel build runs the binary
  succeeds when a verified file is already in place; musl is detected only
  from this machine's loader (`ld-musl-x86_64.so.1` / `ld-musl-aarch64.so.1`),
  not another arch's on a hybrid image. `docs/guides/TAILWIND.md`
  documents `UXCOMPOSE_TAILWIND` as the override when detection still
  picks the wrong asset.

- `ux_compose.components`' docstring, ADR 0004 §3 and the doctor teaching
  line describe the catalog as it is (import a component, or
  `uxcompose add` copies it to own) instead of the removed
  `ux_compose.kit` package (#134). A regression test keeps `src/` and
  `docs/adr/` free of `ux_compose.kit`.

- `doctor --prod`'s requirements scan (#129) reads three more cases the way
  pip does: a missing `-c`/`--constraint` file FAILs; lines pip installs as
  one distribution (different environment markers on both, or one pin
  with different extras) are not "listed twice"; a requirement with no
  name (bare VCS URL without `#egg=`, sdist URL, path) is a WARN naming
  it, since it could be a second ux-dom, and a wheel URL is named by its
  filename.

- The stdlib-shadow check (#136) counts every importable top-level file
  (`importlib.machinery.all_suffixes()`), so a sourceless root
  `secrets.pyc` or an extension `secrets.so` FAILs like `secrets.py`.
  `uxcompose doctor <subdir>` checks the app root's names (nearest
  directory with `app.py`, else the first directory above the regular
  packages) instead of the subdirectory's: `doctor routes` no longer flags
  `routes/email.py`.

- An app module named like a standard library module (`secrets.py`,
  `email/`, `types.py`, …) at the app root shadowed it for every library
  in the process: ux-dom's `import secrets` got the app's file and every
  library JS URL returned 404 (#131). `uxcompose doctor` (plain and
  `--prod`), `build` (all modes) and `serve dev` / `serve prod` now FAIL
  first with one line naming every top-level offender from
  `sys.stdlib_module_names`: "app module `secrets.py` shadows the Python
  standard library module `secrets`; rename it". Library:
  `ux_compose.doctor.stdlib_shadows`. The `--package` library-JS GET stays
  as the backstop.
- `build --package` / `--check` follow-ups from the #130 review (#131): a
  blocking import or sync ASGI startup FAILs in one line after 120 s, not
  a `TimeoutExpired` traceback; a planted `pyvenv.cfg` + `bin/python` no
  longer hides `routes/` (or `components/`, `assets/`, `deploy/`) from the
  bundle and `doctor`; a bundle holding files uxcompose did not write is
  refused naming them (`dist/demo holds .env, .venv/ …`), even when an
  earlier step failed, and `doctor` notes it; a copied file with more than
  one hardlink is refused; `--package` no longer also imports the source
  tree, so import side effects run once. `README.RUN.txt` no longer
  suggests a `./.venv` inside the output dir. `test_cli_package.py` stubs
  the smoke import except where it is the subject (60 s → 14 s).

- `doctor(paths)` skips, when it walks a directory, a bundle written by
  `uxcompose build --package` (its `MANIFEST.json` marker, file list and
  hashes all match the dir, whatever `--out` was), a venv (`pyvenv.cfg`
  and an interpreter), and `__pycache__/`, `.git/`,
  `node_modules/`, `.pytest_cache/`, `.mypy_cache/`
  (`ux_compose.doctor.is_skipped_dir`). A stray `pyvenv.cfg` or marker does not
  hide a dir. A bundle inside the app no longer
  reads as a second Document, so the next `uxcompose build` passes.

- `uxcompose serve dev` stops all of its processes on SIGTERM and SIGHUP,
  not only on Ctrl-C. Before, uvicorn re-raised SIGTERM after the origin
  shut down, the default handler killed the origin, and the Tailwind
  watcher and the ui and channel workers kept running with their ports.
  Each child now leads its own process group. On SIGINT, SIGTERM or SIGHUP
  the origin sends SIGTERM to each group, waits up to 3 s, then sends
  SIGKILL to what is left. The exit status is unchanged: Ctrl-C exits 0,
  and SIGTERM or SIGHUP end the origin by that signal. A channel respawn
  from `serve restart-channel` that races the stop is stopped too, or it
  does not start. A stop signal the parent ignores (SIGHUP under `nohup`)
  stays ignored. POSIX only; `serve dev` already needs `--fd`. SIGKILL to
  the origin still leaves its children running.
- The `serve dev` WebSocket proxy ends the pair when either side closes,
  and the other side gets the same close code and reason. Before, a ui
  reload's 1012 never reached the browser through origin, so the HMR
  clock did not fire. A closed tab also kept its upstream socket. An
  open HMR or Channel socket held the origin's shutdown forever.
  `tests/feature/test_hmr_browser_reload.py` (Chrome 155+) locks the
  save → morph path: the text changes with no navigation.
- create-app's `requirements.txt` resolves. It listed ux-compose at
  `24a182f` (which pins ux-dom `e8be99a`) and ux-dom `8422b9a` beside it,
  so `uv pip install -r` failed with conflicting URLs and `pip install -r`
  with ResolutionImpossible, the Dockerfile too. It now has one
  ux-compose line and no specialist lines; the specialists come with that
  commit's pins. The line is the running ux-compose: the git commit from
  `direct_url.json`, the `HEAD` of an editable checkout (with a note, and a `WARNING` when
  HEAD is on no remote branch), or a remote archive URL. Any other
  install (no `direct_url.json`, such as `PYTHONPATH=src` with a stale
  egg-info, or a local wheel) makes create-app exit 1 with
  `ComposeRefError` and write nothing; ux-compose is on no index. `COMPOSE_VCS_PIN`
  and the specialist `*_VCS_PIN` constants are gone.
  `test_pins_agree_in_all_four_places` reads the specialist pins from the
  `pyproject.toml` of the commit create-app pins. `apps/nook` and
  `apps/pulseboard` lose their `requirements.txt` (same conflict; the apps
  run from the repo on `pip install -e ".[dev]"`). CI resolves the
  scaffold's file with `uv pip compile`.
- The `uxcompose deploy` Dockerfile is two stages. `python:3.14` (has
  git) builds a venv from `requirements.txt`; `python:3.14-slim` copies the
  venv and the app. The one-stage slim image had no git, so the git-pinned
  ux-compose line failed with "Cannot find command 'git'".
- The standalone Tailwind CLI runs only after its SHA256 matches
  `TAILWIND_STANDALONE_SHA256` (v4.1.12, from the release's
  `sha256sums.txt`). A download that does not match is deleted and the build
  fails with `TailwindIntegrityError`. The cached binary is checked on
  every use and downloaded again when it does not match. Another
  `UXCOMPOSE_TAILWIND_VERSION` needs `UXCOMPOSE_TAILWIND_SHA256`; `latest`
  is refused. pytailwindcss counts only when its v4.1.12 binary matches;
  `python -m pytailwindcss` (which downloads `latest`) is no longer run.
- The npx last resort is removed: it never compiled `@import "tailwindcss"`
  and could not be verified. With no CLI (downloads off, a failed download,
  or a platform outside the digest table) `uxcompose build` fails with one
  error naming the platform and `UXCOMPOSE_TAILWIND`. `ensure_tailwind` is
  removed; `resolve_tailwind(ensure=True)` raises instead. A failed
  download names the URL, the requested version and the cause. Parallel
  cold-cache builds each download into their own temp file and
  `os.replace` a verified binary into the cache. musl Linux gets the
  upstream `-musl` assets. `TAILWINDCSS` is no longer read
  (`UXCOMPOSE_TAILWIND` is the one knob), and an unusable
  `UXCOMPOSE_TAILWIND` is an error.
- A secret config that attach would refuse (missing outside dev, under 16
  characters, the published dev secret, or `REDIS_URL` without one) gets
  one line, not a traceback: `Channel secret refused: <reason>`. `build`
  adds "for a local build, set DEBUG=1 or set UX_CHANNEL_SECRET" only when
  dev mode would be accepted; `doctor --prod` adds "set UX_CHANNEL_SECRET
  on the host" and never suggests DEBUG=1.
  `uxcompose build` exits 1 and `uxcompose serve prod` exits 2.
  `ux_compose.doctor.secret_readiness` calls ux-behavior's
  `attach_secret_problem` (pin `f12321f`, #22), the check `attach()` runs,
  so no rule is copied here.
  `serve dev` gives its ui and channel workers `DEBUG=1` and one secret per
  session (minted when the env has none, never written or printed), so it
  serves `/` without `DEBUG` set. Scaffold `settings.py` and the apps read
  `DEBUG` with ux-behavior's `debug_requests_dev()`: unset is prod, as it is
  for Channel attach. `uxcompose deploy` declares `UX_CHANNEL_SECRET` for
  every target without a value; render.yaml uses `generateValue: true` and
  drops `DEBUG=false`. Outside dev a missing secret still fails boot (#114).
  ux-behavior pin `938832d` (#21, public `DEBUG_TRUTHY` /
  `debug_requests_dev`).

- `uxcompose serve prod` imports `app:asgi` from the current directory
  without `PYTHONPATH=.`. It passes the cwd as uvicorn's `app_dir`, the
  same default the `uvicorn` CLI uses. Before, the installed console script
  failed with `Could not import module "app"`.
- Same-name `build()` calls import one package at a time, pinned to that
  directory, so one app cannot serve another app's helper. A second thread
  that waits too long gets `BuildLockTimeout` naming the package instead of
  blocking on the import lock.
- A folder's route module stays in `sys.modules` after `build()`, so
  `import` returns the served module and `typing.get_type_hints` can read
  it. The file runs again only when its bytes change. A different directory
  with the same package name is what replaces it. If another thread is
  still importing that name, `build()` waits for the import to release,
  bounded by the same timeout as the build lock, then loads this folder.
  The package-name lock is not held during that wait. Holding it
  deadlocks when that import calls `build()` for the same name, so the
  lock is released and taken again. If the importer is blocked on the
  lock, or the folder is still the other one after that `build()`,
  `build()` raises `PackageImportConflict` and names both folders. It
  also raises `PackageImportConflict` when a module this folder also has
  is still the other folder's copy. If that wait runs out, `build()`
  raises `BuildLockTimeout` and does not serve the other folder. Main
  silently served that other folder's code. This is a security fix.
- The import pin does not make an off-path package importable. When
  that name is not on `sys.path`, `build()` raises `ModuleNotFoundError`,
  the same as an ordinary import.
- Known limitation: a shared `sys.modules['myapp']` means a thread that
  isn't building can see the building folder's helpers. Its `__path__`
  points at the folder being built, so the meta_path finder isn't involved.
- Helper packages stay imported. `models/__init__.py` is not dropped after
  `build()`, so `typing.get_type_hints` can still see its names and a later
  import is the module the route captured.
- `UX_COMPOSE_BUILD_LOCK_TIMEOUT` and `build(lock_timeout=...)` are new
  in this release. `build()`, `App.mount`, and `DirectoryRoutes.discover`
  share one parser. Unset or blank is 60 seconds. `0` tries once and
  raises `BuildLockTimeout` with no wait. `none` and `inf`, any case,
  wait until the other import ends (`infinite` is `inf`). `abc`, `-1`,
  and `nan` raise `ValueError` naming `UX_COMPOSE_BUILD_LOCK_TIMEOUT`
  (`-1` does not wait forever). `BuildLockTimeout` names the package
  and the setting.
- Security: two folders with the same package name keep their own
  component HTML. While one folder is building, the other folder's
  `main.py` calling `build()` does not make the in-progress build serve
  that other folder's HTML. The in-progress build raises
  `PackageImportConflict` and reports its own folder. Main served the
  other folder's component.
- `build()` does not pop a package out of `sys.modules` while another
  thread is importing a child of that package, so that import does not
  raise `KeyError`.

### Changed

- ux-dom pin `0440ccb` → `8422b9a` (ux-dom main) in `pyproject.toml`,
  `Makefile`, `scaffold.py` (`DOM_VCS_PIN`, so create-app's
  `requirements.txt`), `apps/nook` and `apps/pulseboard`. No compose code
  changed: every ux-dom import compose uses works at that commit.
  `test_pins_agree_in_all_four_places` fails when `pyproject.toml`,
  `Makefile`, `scaffold.py` and `test_hard_deps.py` disagree on any
  specialist SHA.
- `component.py`, `dom.py` and `routing/core.py` import `Component`,
  `dom_tag` and `raw` from ux-dom's public `ux_dom.dom`, not the private
  `ux_dom.dom.src.*` modules. `tests/regression/test_no_tombstones.py`
  fails on any `ux_dom.*.src` or underscore-module import of a specialist
  from `src/`.

### Removed

- The `host="batteries"` / `"directory_router"` tombstone
  (`ProductBatteriesRejected`, `_BATTERIES_TEACH`) in `routing/host.py`
  and `surfaces_host.py`. Every host name other than `auto` | `fastapi` |
  `asgi` gets the one `ValueError("unknown host … use auto|fastapi|asgi")`.
- Doctor's teaching scanners for names that never shipped:
  `scan_leftover_aliases` (`_LEFTOVER_TOKENS`: `host="batteries"`,
  `DirectoryRouter`, `serve="webassets"`, `routing.adapters`,
  `host="starlette"`) and `scan_kit_product_imports`
  (`from ux_compose.kit import`, which is an `ImportError` anyway). The law
  scans and `scan_render_chrome` are unchanged.
- The `UXDOM_TAILWIND*` / `UXDOM_CACHE` tombstone (`LEGACY_ENV`,
  `LegacyTailwindEnvError`, `_reject_legacy_env`, the CLI's
  `_legacy_env_guard`). Only `UXCOMPOSE_*` is read; a `UXDOM_*` variable
  is ignored like any other unknown variable. `UXDOM_TAILWIND_DOWNLOAD=0`
  no longer blocks the download: use `UXCOMPOSE_TAILWIND_DOWNLOAD=0`.
  Every download is SHA256-verified before it runs (UC5).
- `wire.boot.attach_channel(..., **_ignored)`: an unknown keyword (a typo
  such as `use_channel(asgi=...)`) is a `TypeError` instead of being
  swallowed.
- Kit synonyms: `Drawer` (`Drawer = Sheet`, `components/drawer.py`, the
  `drawer` catalog entry, `OverlayEdge` `kind="drawer"`) and the
  `treeview` → `tree` alias in `uxcompose add`. Use `Sheet` /
  `uxcompose add sheet` and `uxcompose add tree`. `examples/presence.py`
  and `examples/catalog.py` use `Sheet`.
- Tombstone prose for names that never shipped: argv `create`,
  `development` / `production` / `restart_channel` and
  `start_css_watcher=` in `cli/__init__.py`, `cli/serve.py`,
  `cli/serve_dev.py`, `AGENTS.md`, `START_HERE.md`, `docs/OWNERSHIP.md`,
  `docs/guides/CLI.md`, `docs/guides/serve-hmr-tunnel.md` and
  `docs/internals/hmr.md` (its "Dead names" list). `docs/ARCHITECTURE.md`
  "Leftovers that expire by teaching" becomes "Doctor residual"
  (`scan_render_chrome`) plus "Design rules (do not recreate)". ADR 0004
  point 4 ("leftovers expire by teaching") is amended to "removed names are
  gone", and ADR 0005's dead-names list drops the same names. Unknown
  verbs and serve modes already get the one generic error; the tests that
  pinned the prose now assert the names are absent.

## 0.2.0 — remove deprecations and bloat cleanup

ux-compose and its ux-* specialists are not on PyPI, so these are removed
outright, with no shims. Call sites, docs and tests are updated.

### Removed — bloat cleanup (no shims)

- Empty extras `[dom]`, `[behavior]`, `[motion]`, `[channel]`, `[full]`.
  They installed nothing. Use `pip install -e .` (or `.[serve]` / `.[dev]`).
- `Component.dirty_fields()` / `Component.clear_dirty()`: a best-effort
  half-feature that read an attribute nothing set. Use `ux_compose.author.mark_dirty`.
- `ProbeResult.summary_lines()` (no callers) and the ignored
  `requested_level=` argument of `ProbeResult.incomplete_stack_messages()`.
- The ignored `channel_scripts=` argument of
  `ux_compose.wire.boot.attach_document_runtimes()`.
- `SurfaceBundle.action_names()` (no callers), the ignored
  `route_file_name` argument of `surfaces._file_url`, and the dead
  `cli.copy_component._wire_css_import` helper.
- 368 unused imports / locals across `src/` (mostly the ported
  `ux_compose.components` modules, which carried the example modules'
  full import lists).

### Changed — examples dedupe (components/ is canonical)

- `src/ux_compose/components/` is the single source of every component class.
  `examples/*.py` are thin usage demos that import from `ux_compose.components`.
  70 duplicated classes were removed from `examples/` (54 byte-identical ports,
  16 older clashing designs and the example `Drawer`).
- The 16 clashes resolve to the kit class. No example copy carried a fix for the
  kit class, so nothing was merged back. Demo behaviours that only the old copies
  had are gone: the quantity `Stepper` (`stepper.inc`/`dec`), the booking
  `Calendar` (`calendar.book`, Cap `bookings.create`), the counting `Badge`
  (`badge.inc`), `Popover.pin_to`, `Timeline.filter`, `Rating.set`,
  `Combobox.type`, `Carousel.go` and the example `Drawer.open_drawer`.
  Use the kit verbs.
- Atelier Studio refuses `stepper.finish` without a Cap (was `calendar.book`).

### Added — bloat cleanup

- `tests/unit/test_bloat_cleanup.py` keeps the removals gone and gates
  `src/`, `tests/`, `apps/` and `examples/` on ruff pyflakes (`--select F`).
- `tests/unit/test_fastapi_none_tree.py`: a render returning `None` yields an
  empty-body ux-dom `HTMLResponse`.
- `tests/unit/test_examples_import_components.py`: fails if `examples/`
  redefines a component class, or if a catalogued demo class does not come
  from `ux_compose.components`.

### Added

- ``tests/unit/test_version_gate.py`` (ux-dom pattern): the version is read
  from ``pyproject.toml``. A fixed list of files must state only that version
  (with required forms for the README row, ``__version__``, the
  ``SECURITY.md`` supported row and this heading). A repo-wide scan fails on
  any "ux-compose X.Y" brand line naming another version. ``pyproject.toml``
  is the source of the version and is not in the file list, because its
  ``cek-host`` / ``cek-surface`` ``>=0.2.0`` floors would break the next bump.
  ``CHANGELOG.md``, ``CRITIC.md`` (the 0.1.0 critic pass), ``docs/plans`` and
  ``docs/adr`` are history. ``SECURITY.md`` now lists 0.2.x as supported.

### Changed (breaking) — fail closed by default

- ``morph_play(target, plan, *, component)``: ``component`` is required. The
  deprecated no-component path (an empty patch that cleared the node, with a
  DeprecationWarning) is removed. An explicit ``component=None`` raises
  ``TypeError`` too.
- ``examples/form_validation.py``, ``list_stagger.py``, ``page_transition.py``
  and ``optimistic_list.py`` (back-compat aliases) are removed. Use
  ``examples/forms.py``, ``lists.py`` and ``navigation.py``.
- Tailwind: the ``UXDOM_TAILWIND`` / ``UXDOM_TAILWIND_DOWNLOAD`` /
  ``UXDOM_TAILWIND_VERSION`` / ``UXDOM_CACHE`` aliases and the leftover
  ``$XDG_CACHE_HOME/ux-dom/`` binary lookup are removed (use ``UXCOMPOSE_*``).
  The ``UXDOM_TAILWIND_OWNED`` env write is dropped too: no ux-dom,
  ux-behavior, ux-channel or ux-motion code reads it.
  **Fail closed:** if any removed variable is still set, ``resolve_tailwind``
  and ``cache_dir`` raise ``LegacyTailwindEnvError`` and name the
  ``UXCOMPOSE_*`` replacement. Silently ignoring it would fail open: for
  example, ``UXDOM_TAILWIND_DOWNLOAD=0`` forbade network downloads, and
  dropping it would let the tool download and execute a binary.
- ``examples/live_caps.py`` ``place_minted`` is gated with ``orders.place``,
  the same as ``place`` and the component copy.

- **Pins:** ux-compose needs ux-behavior **0.4.0** (no Channel-attach
  cap bypass, single-use continuations, per-context ``trust()``), pinned at
  the bitplorer/ux-behavior#17 merge commit ``2ae5c3d`` on ``main``; and
  ux-dom **0.2.0**, pinned at ``0440ccb`` on ``main`` (escapes ``'`` as
  ``&#39;`` in text and attributes; asserts compare ``html.unescape``d
  output). Pins move in lockstep across ``pyproject.toml``, ``Makefile``,
  ``scaffold.py`` and ``apps/*/requirements.txt``.

- ``App(...)`` / ``App.boot(...)`` now default to ``strict_caps=True``
  (best-practice default; matches ux-behavior). A capped ``@action`` dispatched
  with no authority raises ``AuthorityError`` instead of running. ``build()``
  boots strict too. Opt out only for an unchecked sandbox:
  ``App.boot(name, strict_caps=False)``. Public actions (``caps=()``) are
  unaffected; examples and docs no longer pass ``strict_caps=False``.
- ``LiveOrder.place_minted`` now needs ``orders.place`` (same Cap as
  ``place``); it was an ungated copy of ``place``.
- ``Login.logout`` now needs ``auth.logout`` (same as ``UserMenu.sign_out`` /
  ``Command.sign_out``).
  **Breaks:** on a Level-1 page with no Channel, the Login "Log out" button is
  now refused (``AuthorityError``). Migrate one of three ways: (a) attach the
  Channel (``app.use_channel()`` / ``build(live="auto")``) so ``control()``
  mints the Cap; (b) call it from trusted host code with ``app.trust()``,
  or after a verified Cap with ``dispatch_verified``; (c) in your own copy
  (``uxcompose add login``) set ``@action(caps=())`` on ``logout`` if sign-out
  is purely local in your app.
- Gated (server state / user content): ``StockBadge.sell`` / ``restock`` →
  ``stock.adjust``; ``SignupForm.submit`` → ``account.create``;
  ``Comments.post`` → ``comments.post``; ``Chat.send`` → ``chat.send``. Same
  in the teaching copies under ``examples/``; Atelier Studio routes them via
  its ``MINT`` set. Same migration as above.
- ``build(..., strict_caps=True)``: new keyword, default fail-closed.
- Scaffold ``hello.pulse`` cap renamed ``pulse`` → ``pulse.refresh``
  (``namespace.verb``).
- Cap-policy test: the namespace allow-list is replaced by a cap-shape check
  plus a runtime fail-closed check; Cap names are labels, not policy.

### Removed

- ``ux_compose.kit`` package (re-export shim, ``kit.catalog``, ``kit.copy``)
  and the 79 stale widget copies left under ``src/ux_compose/kit/``. Import
  from ``ux_compose.components``, ``ux_compose.cli.registry`` and
  ``ux_compose.cli.copy_component``.
- ``ux_compose.kit_construct`` (``apply_slots`` / ``kit_shell``). Use
  ``ux_compose.arrange.arrange_slots`` / ``wrap_in_card``. All components and
  ``apps/pulseboard`` now import ``ux_compose.arrange`` directly.
- ``ux_compose.routing.DirectoryRouterError`` alias. Use ``DirectoryRoutesError``.
- ``include_directory_router=`` on ``App.mount`` / ``mount_surfaces``. Use ``bind_pages=``.
- ``uxcompose add`` no longer rewrites ``ux_compose.kit`` imports.


### Added

- L5 httpx locks on existing Pulse rooms (home / lab / shop /
  settings + ``/ux-channel/action``) in
  ``tests/integration/test_pulse_feature_matrix.py``. No new Pulse
  room or MATRIX.md teaching surface. Cap / ``Channel.boot`` /
  ``mount_channel`` KEEP. Walker escape KEEP.

### Changed

- Depend on `cek-host>=0.2.0` and `cek-surface>=0.2.0`, and pin
  ux-channel @ `f1a93fcf298c97a59fa6538697731e19aac8586d`.
  Versions before 0.2.0 teach `cek_host.legal`. Do not pin them.
  `0.1.0`, `0.1.2`, and `0.1.3` are yanked. An exact pin still installs them.
  Makefile / scaffold / nook /
  pulseboard lockstep. Cut C floor ``985e58a`` stays.
- Pin ux-channel @ `9e43bb4e1da5ea2a1aadfeee1c99b59d1ced67a9` and
  cek-host / cek-surface @ cek-python `0626a10b36535942f9687dbe2eb298742263a780`.
  A clean install of channel `a6ab159` plus PyPI `cek-host` 0.1.3
  still speaks `legal` / `to_s` and does not consume a once-Cap before
  side-effects. The pin is the catalog Host (CORE 08, 11, 14, 26).
  Makefile / scaffold / nook / pulseboard lockstep. Cut C floor
  ``985e58a`` stays. Cap door ``Channel.boot`` unchanged.
- Pin ux-dom @ `cdb0dd1486e58746c51e98aa51f5fd4d26841196`
  (ux-dom [#22](https://github.com/bitplorer/ux-dom/pull/22)). A clean
  install of `2e894cd` has no `style-src-attr`. Dev CSP now emits
  `style-src-attr 'unsafe-inline'` so element `style=""` is not blocked
  by the style-src nonce. Makefile / scaffold / nook / pulseboard
  lockstep. Cap door ``Channel.boot`` unchanged.
- Pin lockstep to Python ≥3.14 tips: ux-channel @
  `a6ab1594959b287b4754afe09d8aced5504edd8f` (channel
  [#39](https://github.com/bitplorer/ux-channel/pull/39)), ux-behavior @
  `7d46979f59f284bc2d6d961ed372ec849e851dfc` (behavior
  [#12](https://github.com/bitplorer/ux-behavior/pull/12)), ux-motion @
  `bbe7d73466a6c1eccb47e711568c80ce3b4d5487` (motion
  [#8](https://github.com/bitplorer/ux-motion/pull/8)). Makefile /
  scaffold / nook lockstep. ux-dom stays `2e894cd` (docs-only tip
  KEEP). ``COMPOSE_VCS_PIN`` / #56 chicken-egg lag stays. Cap door
  ``Channel.boot`` unchanged. HOLD compose #30. Valio out of scope.
- Pin ux-dom @ `2e894cd7bca66e1da6c2f9d42b2d1a8bb937c92c`
  (ux-dom Soft extract-by-id [#20](https://github.com/bitplorer/ux-dom/pull/20)
  / plan [#19](https://github.com/bitplorer/ux-dom/pull/19); compose
  [#80](https://github.com/bitplorer/ux-compose/pull/80) C2 owner gap
  closed on tip). Makefile / scaffold / nook lockstep. Cap door
  ``Channel.boot`` unchanged. Soft USE of ``extract_by_id`` is a
  separate PR.
- Pin ux-channel @ `d0412c62b5180f69e76d16c913809f6c34dee269`
  (channel Soft 3 kit leftover-teach + Soft 4 ``render/response.py``
  prefers ux-dom). Makefile / scaffold / nook lockstep. Cut C floor
  ``985e58a`` stays. Cap door ``Channel.boot`` unchanged. No Soft
  relaunch.
- scaffold/nook: ``COMPOSE_VCS_PIN`` tracks main tip ``24a182f`` so cold
  ``pip -r`` installs pin-aligned compose (includes channel Soft 1+2 #78;
  same #56/#75 honesty).
- Pin ux-channel @ `ae5a675991db5c168d0b6df018e929d808c7511f`
  (channel Soft 1 HTML→ux-dom + Soft 2 create-app lab honesty).
  Makefile / scaffold / nook lockstep. Cut C floor ``985e58a`` stays.
  Soft 3 kit teaching and Soft 4 ``render/response.py`` are not this PR.
- Pin ux-channel @ `985e58aee76ca683774c4d4d58ab30a1d3b6efee`
  (channel Cut C: empty Content-Type on HTTP ``/action`` is
  ``bad_request``). Makefile / scaffold / nook lockstep. Compose does
  not POST without a declared type. Plan: #73.
- scaffold/nook: ``COMPOSE_VCS_PIN`` tracks main tip ``957f81f`` so cold
  ``pip -r`` installs pin-aligned compose (includes channel Cut C #74;
  same #56 residual). Plan: #73.

### Fixed

- Soft USE: ``helpers._fragment_for_target`` prefers
  ``ux_dom.response.serialize.extract_by_id`` when importable
  (ux-dom [#20](https://github.com/bitplorer/ux-dom/pull/20) /
  plan [#19](https://github.com/bitplorer/ux-dom/pull/19); compose
  [#80](https://github.com/bitplorer/ux-compose/pull/80) C2). Homemade
  walker KEEP as escape if absent. No ``fragment.py``. Cap door
  ``Channel.boot`` / ``mount_channel`` KEEP. Leftover teaching + locks
  in the same commit. Pin lockstep landed
  [#82](https://github.com/bitplorer/ux-compose/pull/82).
- Cut B leftover teaching: homemade ``helpers.py`` fragment walker
  (``_fragment_for_target``) stays until ux-dom owns extract. Serialize
  remains ``to_html_bytes``. No ``fragment.py``. Same-commit source locks.
  Kit Cut 2 stretch skipped — no evidenced leftover dual door / shadow
  export in kit vs channel ``15cb1ed`` / compose locks.

### Changed

- Pin ux-channel @ `15cb1ed9dd03dbee8826823a7ab46efd4f215b5c`
  (channel Cuts 1–2: CLI script honesty, ``ops/`` ``enhance/`` mapped,
  region CLI → scaffold). Makefile / scaffold / nook lockstep. Cap /
  Isolation / store doors from #69 stay (``Channel.boot``, Redis wins,
  wire/ frozen imports).

### Fixed

- Cut 4 encyclopedia honesty after Cut 3 dual-door locks: START_HERE /
  AGENTS / OWNERSHIP / CLI / ADRs / package docs name leftover
  ``start_css_watcher=``, serve argv synonyms, ghost ``cli/`` /
  ``serve/`` / ``services/``, Cap door ``Channel.boot``, and channel pin
  ``15cb1ed``. ADR 0004 attach fail-loud. CONTRIBUTING pulse serve needs
  a mode. Compose has no FEATURES.md / ONTOLOGY.md — ARCHITECTURE +
  OWNERSHIP are the encyclopedia.

- Cut 3 leftover dual doors: ``cli.py`` is argv only. ``serve_dev.py``
  starts sibling Tailwind ``--watch`` and tunnel (clock body). Leftover
  ``start_css_watcher=`` hook is gone.
- Serve argv synonyms ``development`` / ``production`` / ``restart_channel``
  fail closed (frozen names: ``dev`` / ``prod`` / ``restart-channel``).
- Console script ``uxcompose = ux_compose.cli:main`` is import-resolve
  locked. On-disk packages (``dx`` ``kit`` ``routing`` ``wire``) stay on
  the concern table — no ghost dirs, no ``cli/`` / ``serve/`` /
  ``services/``. Channel ``ops/`` / ``enhance/`` are not compose doors.

### Changed

- Pin ux-channel @ `b0cc17d87348fa65578f41e95879b35c43b0ecfa`
  (channel #27: ``from_config`` applies the Cap adapter; health
  ``formats`` vs ``codecs``). Makefile / scaffold / nook lockstep.

### Fixed

- Cap door honesty after channel #27: ``Channel.boot`` is the compose
  door (same machine as ``ActionRegistry.from_config``). ``attach_cek``
  still calls ``apply_host_adapter`` (idempotent). Do not assume classic
  ``CapService`` when ``cek=require``. wire/ stays on frozen imports
  (``Channel``, ``ChannelConfig``, ``apply_host_adapter``, ``Intent``).
- serve-dev / doctor do not set ``UXCOMPOSE_STATE_STORE`` and
  ``REDIS_URL`` as if both were the session. Channel prefers Redis;
  ``prepare_shared_state`` skips the sqlite env when Redis is set.
  ``scan_store_precedence`` fails closed if both remain.
- Product host spec notes Channel ``/ux-channel/health`` ``formats``
  (HTTP today) vs ``codecs`` (library), matching the Rust peer.
  Clock A ``/health`` is still ``dict`` JSON.
- Public ``__all__`` lock now covers host / surface / motion names
  (``WebAssets``, ``Directory*``, ``Surface*``, ``DoctorResult``,
  ``scene`` / ``fade`` / ``rise`` / ``slide``) (LOCK-1).
- Concern table names delivery files that already exist: ``tunnel.py``,
  ``deploy.py``, ``serve_restart.py``, ``author.py``, ``progressive.py``,
  ``dom.py``, ``attach_notes.py``. Still no ``docs/MODULE_MAP.md`` (MAP-2).
- Cold-import isolation test no longer asserts ``or True``. ``__init__.py``
  is AST + text locked against ``wire`` / ``ux_channel`` imports (ISO-2).
- ``AGENTS.md`` public-name paragraph matches ``__all__`` in three bands.
  Kit is ``uxcompose add``, not a product import path (DOC-4).
- ``CRITIC.md`` names four product apps (``atelier_shop``,
  ``atelier_studio``, ``nook``, ``pulse``). Walker residual stays (CRIT-2).

### Changed

- Folder law locked in ``docs/ARCHITECTURE.md`` / ``AGENTS.md``: ``kit/``
  is the ownable-copy prefix, ``kit_construct.py`` stays next to
  ``Component``, CLI verbs stay as library modules not a ``cli/`` package.
  Do not add ``cli/`` or ``kit/kit_construct.py``.
- serve-dev shared session store is Channel's ``FileStateStore``
  (JSON sqlite). ``serve_state.py`` is lifecycle only: env, path,
  prepare / clear / drop (ADR 0006). Isolation unchanged (``wire/``
  remains the only ``ux_channel`` door). ``Channel.boot`` honors
  ``UXCOMPOSE_STATE_STORE``; compose no longer duck-assigns
  ``channel.state``. Doctor ``scan_store_clone`` fails closed if a
  store class reappears in this tree.
- Pin ux-channel @ `d0fe7169e687d2935f8b74d40b990b1ee63ef3d4`
  (FileStateStore). Makefile / scaffold / nook lockstep with pyproject.

### Fixed

- Leftover table in ``docs/ARCHITECTURE.md`` splits doctor-scanned
  tokens from agent-only locks (cli/ package, kit_construct placement,
  argv ``create``, MODULE_MAP). Doctor is not credited for names it
  does not scan (LEFTOVER-split).
- ``build()`` catalog scan (``App.mount`` / ``scan_surfaces``) and HTTP
  path law (``DirectoryRoutes.discover``) are two walkers. ADR 0004 no
  longer claims one filesystem implementation (SURF-1-claim). Both
  walks stay. Product door is still ``build()``.
- Command palette no longer imports OverlayChrome. Local ``{id}-scrim`` /
  ``{id}-panel`` / ``{id}-dismiss`` and ``click keydown.escape`` (KIT-1).
  Dialog / Sheet / ActionSheet / AlertDialog stay on the primitive.
- ``insert_live_client`` leaves HTML fragments unwrapped. No synthesized
  ``<!DOCTYPE html>`` shell (HMR-shell). Complete documents still get
  Channel scripts before ``</body>``.
- Sibling Tailwind ``--watch`` spawn lives in ``tailwind.py``
  (``start_tailwind_watch``). ``cli.py`` dispatches; ``hmr.py`` still
  does not ``Popen`` (CSS-spawn).
- ``helpers._live_channel`` swallows ``ImportError`` only. Other errors
  fail loud so live ``control()`` cannot emit no-cap dual attrs (SWALLOW-1).
- ``ChannelConfig(secret=)`` and ``Channel.boot`` in ``wire/boot.py`` fail
  closed (no silent ``cfg=None`` / ``ch=None``). ``App.use_channel`` stamps
  L2 only when a Channel instance exists (SWALLOW-boot).
- Brand tables no longer claim PyPI. Install is git clone +
  ``pip install -e ".[serve]"`` (PYPI-1).
- ``App.mount`` is taught as a page-unit scan step, not a second
  product path. The method stays (DOOR-1).
- ``CRITIC.md`` thin-root row names the homemade fragment walker
  residual. Walker stays (CRIT-1).
- ``docs/ARCHITECTURE.md`` holds the concern→file table. Do not add
  ``docs/MODULE_MAP.md`` (MAP-1).
- Deleted ``routing/adapters/`` shims. Import ``routing.asgi`` /
  ``routing.fastapi``. Doctor leftover-teaches the old path (SHIM-1).
- CLI argv ``create`` is gone. Frozen verb is ``create-app`` (DOOR-2).
- Doctor leftover scan reports every leftover token in a file, not the
  first hit (SCAN-1).
- Doctor render-chrome scan reports every ``render()`` hit, not the
  first (SCAN-2).
- ``uxcompose add`` copies keep ``from ux_compose.kit_construct import``
  (COPY-1).
- Cite OWNERSHIP, not FLOW, as the ownership law. ``docs/FLOW.md`` stub
  stays (DOC-3).
- ``docs/internals/OWNERSHIP.md`` is a Moved stub. Canonical is
  ``docs/OWNERSHIP.md`` (OWN-1).
- ``docs/START_HERE.md`` is not a second ``create-app`` recipe.
  CONTRIBUTING no longer syncs the two START_HERE files (DOC-1).
- Makefile / TESTING.md no longer name a missing ``tests/property``
  tree (MAKE-1).
- ``wire/boot.py`` names the package door (three files), not a single
  module (ISO-1).
- Unknown ``host=`` names (including leftover ``starlette``) fail closed
  instead of degrading to DirectoryASGI (HOST-1-allow).
- serve-dev no longer pickle-serializes MorphState into a cwd file.
  JSON matches the Redis production domain.
- Kit Batch A APG holds: menubar submenu ids ``{id}-m-{key}`` stay in the
  tree with ``hidden`` when closed (no dangling ``aria-controls``). Toolbar
  one-shot commands use ``aria-current``, not ``aria-pressed``. Filterbar
  radios rove ``tabindex``.
- Kit Batch D APG holds: FAB menu id ``{id}-menu`` stays in the tree with
  ``hidden`` when closed (no dangling ``aria-controls``). Resizable split
  chips are ``role=radio`` ``aria-checked`` inside the radiogroup.

### Added

- Kit Cut 1: render slots + ``shell=False`` usable units. Kits stay
  ``Component`` subclasses (no ``Kit`` base). ``render(*, shell=None, **slots)``
  writes documented seams through to instance attrs (``actions``→``ACTIONS``,
  ``links``, ``title`` / ``body``, ``items``, …) so later morph keeps them;
  omitted slots leave class const / current instance; unknown slots fail
  closed per file. ``shell=False`` drops the Atelier kicker/title/lede card.
  Helpers are ``apply_slots`` / ``kit_shell`` in ``ux_compose.kit_construct``
  (not under ``kit/``, so ``uxcompose add`` is unchanged). Zero-arg
  ``Behavior.add(cls)`` still greens. Soft-parked work (open-mint blurbs,
  navbar menuitem, flat tree, chart legend) and stretch stems stay out.
- Kit Batch A chrome P1: `menubar`, `toolbar`, `togglegroup`, `spinbutton`,
  `themeswitch`, `filterbar`. APG roles (menubar/menu, toolbar+separator,
  radiogroup, spinbutton valuemin/now/max, theme radiogroup ≠ switch).
  Spinbutton magnitude is RefState. Caps stay off chrome. Isolation: kit
  still never imports `ux_channel`.
- Kit Batch B product: `chat`, `questionnaire`. Chat log is `role=log`;
  composer label↔id; send is public. Questionnaire is fieldset radiogroups;
  submit spends `form.submit`.
- Kit Batch C marketing: `pricingsection`, `logocloud`, `timeline`, `rating`.
  Pricing is a comparison table (choose on the button, not the row). Rating
  stars are named keys. Caps stay off.
- Kit Batch D P2: `chart`, `resizable`, `tree` (`treeview` alias),
  `colorpicker`, `fab`, `diff`, `countdown`, `mockup`, `attachment`,
  `scrollarea`, `feed`. APG tree/feed/timer; magnitudes on RefState.
  Caps stay off. Isolation: kit still never imports `ux_channel`.
- Kit expansion: harden existing widgets (ARIA APG, label↔id, Escape dismiss,
  table row-select vs header select-all, overlay focus attrs) and add P0 +
  cheap P1 cards (`navbar`, `navmenu`, `usermenu`, `popover`, `tooltip`,
  `alertdialog`, `formlayout`, `fieldset`, `datepicker`, `switch`, `card`,
  `emptystate`, `stats`, `alert`, `banner`, `progress`, `skeleton`, `hero`,
  `footer`, `cta`, plus `avatar`, `badge`, `hovercard`, `searchbar`,
  `fileupload`, `tagsinput`, `multiselect`, `descriptionlist`, `featuregrid`,
  `testimonials`, `newsletter`, `bottomnav`, `separator`, `slider`).
  `drawer` is a Sheet alias (same Host). OverlayChrome `dismiss_on()` adds
  Escape. Isolation: kit still never imports `ux_channel`.
- FastAPI product host disables Swagger by default (`docs_url=None`,
  `redoc_url=None`, `openapi_url=None`) so `routes/docs.py` owns GET
  `/docs` (Document wrap, including `brand_wrap`). Opt in with
  `build(openapi=True)` or `settings.OPENAPI = True`. Doctor residual
  warns when a surface path collides with `/docs` `/redoc`
  `/openapi.json` and recommends `/about`.
- `uxcompose create-app` rejects reserved dest basenames (`site`,
  `test`, `email`, other stdlib modules and keywords) that would shadow
  `import site.routes`. Error suggests `fullsite`, `app`, or `web`.

### Changed

- Kit APG residuals after #59: namespaced tabs/login tabpanels (`{id}-tab-{k}` /
  `{id}-p-{k}`, inactive `hidden`); calendar/datepicker `role=grid` + `row` /
  `gridcell` + `aria-selected`; alertdialog Escape/scrim do not dismiss;
  table row select binds the checkbox, not the `<tr>`; actionsheet autofocus
  on open; navbar builds two link trees. Ride-along: fileupload demo names
  `sketch.png`; combobox/accordion ids follow the instance id; select
  `label for`; plans radio APG; contextmenu `aria-controls`; command Sign out
  spends `auth.logout`.
- scaffold/nook: `COMPOSE_VCS_PIN` tracks main tip `6d61c9e` so cold `pip -r` installs pin-aligned compose (soft residual after #55).
- pin-align: specialist tips (ux-dom `e8be99a`, ux-behavior `793f120`; channel/motion kept) + cold `pip -r` VCS honesty; Python ≥3.14 floor unchanged.
- apps: Bucket B host sync (Document path + Cap Host require; kill HAS_DOM/HTML-string soft shells) after #52.
- examples: kill residual Document-absent / unlock soft after #52/#53.

### BREAKING

- **Python floor is ≥3.14.** ux-compose hard-depends on pinned ux-dom,
  ux-channel, ux-behavior, and ux-motion (plus `cek-host>=0.1.3` /
  `cek-surface>=0.1.3`). Day-one install is the full stack. Missing
  specialists fail loud — no optional L1 / `HAS_DOM=False` / Document-absent
  product path.
- Kit HTML-string fallbacks (`_render_html`, `html_fallback`) and
  `create-app` dual-floor (`document=None`, `shell.py` / `wrap_get_chrome`)
  are gone. Scaffold emits Document-only `render()` trees.
- `doctor` exits non-zero when the stack is incomplete (unless `--no-fail`).
  Progressive Superpower is additive levels on a complete install, not an
  unlock ladder of optional packages.
- Product extras `[dom]` / `[behavior]` / `[motion]` / `[channel]` / `[full]`
  are empty aliases. Specialists live in `[project].dependencies`.
- CI product-green is full-stack py3.14 only. The py3.12 offline-shim job
  is retired.

### Removed

- `ux_compose.chrome.wrap_get_chrome` / `shell.py` Document-absent primary.
- Kit HTML-string fallbacks (`_render_html`, catalog `html_fallback`).
- CI py3.12 offline-shim job and Makefile `test312`.
- Optional `_LocalBehavior` / specialist soft-import shims on the product path.
- `build()` / `surfaces` auto-attach of live-client when no Document is given.
- Parallel HTML-string helpers (`html_escape` / `html_attrs`) and dict-Op
  fallbacks. Morph HTML serializes through ux-dom; Ops are ux-behavior.
- Optional motion swallows (`optional_*` returning None / `scene is None`).
  Those names still exist; they import and use ux-motion.

### Fixed

- `uxcompose add dialog|sheet|actionsheet` copies rewritten kit siblings
  (``components/overlay.py``) so `add --page` can `import routes.dialog`
  without a manual overlay copy. Overlay stays out of the catalog.

### Added

- `ux_compose.chrome.brand_wrap(document, brand=…)` — Document-path GET
  nav brand (`wrap(child)`). Clock A GET includes brand once; Clock B morph
  HTML has brand=0. `Component.render()` stays a fragment. Optional
  `uxcompose create-app --brand LABEL` wires `wrap=`. Not a
  `wrap_get_chrome` / `shell.py` Document-absent string shell.
- `create-app` `requirements.txt` pins the full specialist stack (CI SHAs)
  plus `cek-host>=0.1.3` / `cek-surface>=0.1.3`. Doctor fail-loud when
  `cek=require` and Channel is live but `registry._caps` is not
  `CekHostCapService` / `kernel_ssot=cek-runtime`.
- `build(cek="require")` (default): after `use_channel`, attach product Cap
  Host through `App.use_cek` (cek-runtime). Skip when `live="null"` / no
  Channel. Scaffold emits `cek="require"` so authors never hand-wire.
- `create-app` emits `routes/index.py` so GET `/` is not 404; `/hello` stays.
- `uxcompose build` names the cwd in `FileNotFoundError` and finds the app
  root from `--app path/to/app:asgi` when not already in the app directory.
- Cap Law demos/tests show `mint_cap(action, {}, once=True)` where once
  matters (checkout/place). Default remains `once=False`.
- `uxcompose serve restart-channel`: one-shot Channel RAM drop for a
  running `serve dev` (pidfile + SIGUSR1). Not a sticky flag.
- Ownable kit (`uxcompose add`): login, tabs, accordion, dropdown, dialog, sheet,
  toast, command, table, pagination, combobox, sidebar, breadcrumb, stepper,
  carousel, calendar, select, otp, plans.
- Kit Wave 1 (Signal grammar): `actionsheet`, `contextmenu`, `typeahead`, `pullrefresh`.
  Tailwind `class_*` only. `data-channel-on` for swipe.vertical / longpress / input delay:.

### Changed

- Docs/docstrings honesty scrub after #48: kill residual optional-deps /
  unlock-ladder / `HAS_DOM` soft speech. Hard-deps fail loud (Python ≥3.14,
  pinned specialists). Levels 0–3 are additive attach APIs on a complete
  install — not an optional-package unlock ladder. No Document-absent L1
  / HTML-string fallback product speech.

- Vocab: `@action(caps=())` is **open mint / no Cap predicate** (Intent still
  requires the control-minted cap under Cap Host require). Scaffold
  `ROUTES_HELLO_PY`, PATH, and HOST no longer call `caps=()` "public".
- `uxcompose add toast`: page docstring + catalog blurb teach sealed-args
  (Intent POST with `{}` is 401; replay html-unescaped `data-channel-args`).
- Channel pin: `31a60bdd40a1b52aea1fd13159ad09c293c63fd6` (Makefile + CI).
  Soft Cap install: `cek-host>=0.1.3`.
- Nomen cut: `maybe_*` → `optional_*`; MorphState `stamp` / helper `tick` →
  `dirty` / `mark_dirty`; kit Cap `flow.finish` → `stepper.finish`;
  `docs/FLOW.md` → `docs/OWNERSHIP.md`.
- `serve dev` soft-morphs page units after a `.py` save
  (`softReload` / `morphLive`). `location.reload()` is the fallback only.
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
- Accordion open uses `optional_plan`; Confirm overlay open uses rise.
- `act(..., on=)` and `optional_slide` in `examples/_common.py` (already on main).


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
- Package static `/ux-dom/static/x_element.js` is the only library JS source (the `serve="webassets"` alias was removed in ux-dom 0.2.0 and now raises; doctor still flags it). Not `WebAssets`.

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
- **Docs:** teaching pages no longer name leftover DirectoryRouter /
  `host=batteries` as something to run. Stub cites (`docs/CLI.md`, `docs/DX.md`,
  `docs/TESTING.md`) point at `docs/guides/`. Product path is the only path taught.
- CI pins ux-behavior / ux-motion / ux-channel / ux-dom to origin/main SHAs;
  leftover `httpx2` is gone. Teaching is `create-app` + `build()` (`App.mount`
  is a secondary door). Clock A GET asserts `Content-Security-Policy` when
  Document mounts Csp.
- Product path is `create-app → build → serve → deploy`. `uxcompose build` compiles CSS.
