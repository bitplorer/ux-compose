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
# optional GET brand (outside render()):  --brand Acme
# dest must not be a stdlib name (site, test, email, …); use fullsite / app / web
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

### `requirements.txt` from create-app

create-app writes one ux-compose line and no ux-dom, ux-channel,
ux-behavior or ux-motion lines. The specialists install with the pins in
that ux-compose commit's `pyproject.toml`, so the file cannot name a
specialist twice. The ux-compose line comes from how the running
`uxcompose` was installed (`direct_url.json`, PEP 610):

| Install | Line |
|---------|------|
| git (`pip install "ux-compose @ git+…@<sha>"`) | `ux-compose @ git+<url>@<commit_id>` |
| editable or local git checkout (`pip install -e .`) | `ux-compose @ git+https://github.com/bitplorer/ux-compose.git@<HEAD>`, plus one stderr note: push that commit; uncommitted changes are not in it. A `WARNING` line comes first when HEAD is on no remote branch (`git branch -r --contains`) |
| remote archive URL | `ux-compose @ <url>` |
| anything else: no `direct_url.json` (index install, `PYTHONPATH=src` with a stale egg-info, not installed), local wheel or sdist file | create-app exits 1, writes nothing, and names the two supported installs |

No ux-* package is on an index, so there is no `ux-compose==<version>` line.

There is no compose SHA constant to bump after a pin change.

## Pure-dom tooling

```bash
uxdom doctor
uxdom lint
uxdom profile
uxdom add component Card
```

Product apps use `uxcompose build` for CSS. ux-dom does not compile CSS.
See `docs/OWNERSHIP.md`.

`uxcompose serve dev` is origin + ui + channel, clocks on.
`uxcompose serve prod` is one process, clocks off, disk CSS.
`uxcompose serve restart-channel` drops Channel RAM once in a running `serve dev`.
Missing origin extras fail closed (`pip install -e '.[serve]'` from the clone; not on PyPI).
There is no `--one-process` / `--hmr` / `--css-watch` flag.
`uxcompose serve` without a mode exits 2. `uxcompose build` is the
one-shot minify. Deploy runs raw uvicorn, not `serve`.
`cli/__init__.py` is argv only (`uxcompose = ux_compose.cli:main`). Clock bodies
live in `cli/serve_dev.py` (sibling Tailwind `--watch` + tunnel). Leftover
`start_css_watcher=` is gone. argv `development` / `production` /
`restart_channel` fail closed — not synonyms. No `serve/` /
`services/` packages. Library modules do not import `ux_compose.cli`.

### Channel secret and `DEBUG`

Dev is ux-behavior's `debug_requests_dev()`: `DEBUG` in `1` / `true` /
`yes` / `on`. Unset `DEBUG` is prod, in the scaffold's `settings.py` too.
Outside dev, Channel attach needs `UX_CHANNEL_SECRET` (or
`UX_BEHAVIOR_SECRET`, ≥16 chars).

- `uxcompose serve dev` is dev by verb. Its ui and channel workers get
  `DEBUG=1` and one secret for the session. Without a secret in the env it
  mints one (`secrets.token_urlsafe(32)`), never written or printed, so a
  Cap minted by ui is accepted by channel. An env secret always wins.
- `uxcompose build`, `uxcompose serve prod` and `uxcompose doctor --prod`
  print one line, no traceback, when attach would refuse the secret: it is
  missing outside dev, shorter than 16 characters, the published dev
  secret, or absent while `REDIS_URL` is set. The line is `Channel secret
  refused: <reason>`. build exits 1, serve prod exits 2. When dev mode
  would be accepted (the secret is only missing), build adds "— for a
  local build, set DEBUG=1 or set UX_CHANNEL_SECRET"; doctor `--prod`
  adds "— set UX_CHANNEL_SECRET on the host" instead.
  `ux_compose.doctor.secret_readiness(env)` is that check; it calls
  ux-behavior's `attach_secret_problem`, the same function `attach()` runs,
  so the gates and the boot cannot disagree.
- `uxcompose deploy` declares `UX_CHANNEL_SECRET` for every target and
  never writes a value: render `generateValue: true`; fly `fly secrets set`;
  docker `docker run -e UX_CHANNEL_SECRET`; railway `railway variables
  --set`; vps `EnvironmentFile=/etc/<name>.env`; checklist step 3.

### `uxcompose doctor --prod`

`uxcompose doctor [paths...]` checks the isolation laws. `--prod` adds
product readiness rows for the app root (the first path, default `.`).
Each row is `[OK  |WARN|FAIL] name: detail`. Any FAIL exits 1;
`--no-fail` exits 0. Readiness is static: it reads files and the
environment, never imports the app and never opens the network.

```bash
uxcompose doctor --prod                # in the app root
uxcompose doctor --prod --port 8080    # also warn if 0.0.0.0:8080 cannot be bound
```

| Row | FAIL / WARN when |
|-----|------------------|
| `product` | FAIL: no `app.py` in the root (an empty dir fails; no other row is printed) |
| `dep:uvicorn`, `dep:fastapi` | FAIL: not importable in the interpreter running `uxcompose` |
| `requirements` | FAIL: `requirements.txt` missing, or `ux_compose.scaffold.scan_requirements` finds a problem. It reads the file the way pip does: `\` continuations are joined, comments are stripped, option lines (`--index-url`, `-f`, `-c`, `--hash=…`, …) are skipped, `-e` lines count as requirements, and local `-r` includes are followed relative to the including file (an include cycle fails, as in pip). It FAILs on a line that is not a requirement, a distribution listed twice, no ux-compose line, or a specialist (ux-dom, ux-channel, ux-behavior, ux-motion) pinned beside ux-compose. WARN: a remote `-r https://…` include, which doctor does not fetch |
| `secret` | FAIL: `secret_readiness()` returns a "Channel secret refused" line (ux-behavior's `attach_secret_problem`: missing outside dev, under 16 characters, the published dev secret, or `REDIS_URL` without one). The row adds "— set UX_CHANNEL_SECRET on the host"; it never suggests `DEBUG=1`, which the `DEBUG` row FAILs |
| `DEBUG` | FAIL: `DEBUG` is dev (`debug_requests_dev`: `1` / `true` / `yes` / `on`) |
| `.env` | WARN: present ("do not ship; set secrets on the host"). FAIL: present, a `Dockerfile` exists, and `.dockerignore` does not exclude `.env` the way Docker reads it (`*`, `?`, `[…]`, `**`, `!` re-include, last match wins, leading `/` dropped, `#` comments). A pattern with `\` before a letter or digit FAILs as "cannot be checked" |
| `deploy:render` | FAIL: `render.yaml` exists and does not declare `UX_CHANNEL_SECRET` |
| `deploy:vps` | FAIL: a `deploy/*.service` unit has neither `EnvironmentFile=` nor `Environment=UX_CHANNEL_SECRET=` |
| `port:N` | WARN: only with `--port N`, when `--host` (default `0.0.0.0`, as `serve prod` and the deploy targets) cannot bind N with `SO_REUSEADDR`, as uvicorn binds; "cannot resolve host H" when `--host` does not resolve |

`--port` without `--prod` and `--host` without `--port` exit 2. `doctor` without `--prod` prints the
same report and exit code as before.

### `uxcompose build --package` / `--archive`

A runnable bundle of the app, written only after every build step passes.

```bash
export UX_CHANNEL_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
uxcompose build --package                        # → dist/<app dir name>/
uxcompose build --archive --out out --name shop  # → out/shop/ and out/shop.tar.gz
# anywhere, in a fresh venv:
pip install -r dist/<name>/requirements.txt && dist/<name>/run.sh
```

- `--out DIR` (default `<app root>/dist`), `--name NAME` (default the app
  directory name; one plain path segment). `--archive` implies `--package`.
- `--out` safety, checked on the resolved path (symlinks followed) before
  anything is written or deleted: it is refused when it is the app
  directory or one of its parents (`.`, `..`, `/`, `~` for an app under
  home), inside `routes/` / `components/` / `assets/` / `deploy/`, or an
  existing directory holding anything but bundles this tool wrote (a
  `MANIFEST.json` with `"generator": "uxcompose build --package"` whose
  files and hashes match, holding nothing else but `__pycache__/`, or
  their `.tar.gz`). Only such a bundle is ever replaced, and it is
  re-checked just before the rename. A bundle you added files to
  (a `.venv`, an `.env`, an edit) is refused, never deleted. The bundle
  is assembled in a temp dir inside `--out` and renamed into place; a
  refused bundle leaves nothing behind, and `--package` alone removes that
  bundle's older archive.
- Allowlist (regular files only): every `*.py` under the app root, so
  `lib/`, nested and relative-import packages ship; root
  `requirements.txt`, `README.md` and existing deploy files
  (`Dockerfile`, `.dockerignore`, `fly.toml`, `render.yaml`,
  `railway.json`); source types (`.py .html .css .js .json .md .txt`)
  under `routes/` and `components/`; web asset types under `assets/` (with
  the compiled `output.css`); unit and config types under `deploy/`. The
  bundler generates no deploy file: run `uxcompose deploy` first. Every
  other file and directory is left out and listed in the `package` row
  (`excluded: …`): tool caches (`__pycache__`, `.git`, `node_modules`,
  `.pytest_cache`, `.mypy_cache`), a venv (`pyvenv.cfg` and
  `bin/python` or `Scripts/python.exe`), a bundle whose MANIFEST file
  list and hashes match its dir, and `--out` itself. A stray `pyvenv.cfg`
  or MANIFEST does not hide a dir: it stays source.
- Refused (FAIL, nothing written), each listed:
  - any symlink in the walked tree, whatever it points at;
  - a key-shaped file inside an allowed directory: by name (`.env`,
    `.env.*`, `*.env`, `id_rsa*`, `id_dsa*`, `id_ecdsa*`, `id_ed25519*`,
    `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `*.kdbx`,
    `*.gpg`, `.netrc`, `.npmrc`, `.pypirc`, `.htpasswd`) or by content
    (`PRIVATE KEY-----`, a JSON `"private_key":` in the first 64 KiB), and
    a copied file holding a private key. This is best-effort hygiene, not
    a guarantee: it misses DER keys, tokens and keys under innocent names.
    Secrets belong in the environment, not in the app tree; the `package`
    row says so.
- Import check: after doctor, `python -I -B` imports the entry
  (`app:asgi`) from a copy of the assembled bundle, with only the bundle
  dir on `sys.path` (no source root, no `PYTHONPATH`, no user site). A
  failure FAILs the build with the last error line, so a module or data
  file the allowlist missed cannot give BUILD OK.
- Generated: `run.sh` (0755: `cd` to the bundle, `PORT` 8080 / `HOST`
  0.0.0.0 defaults, activates `.venv` if present, runs `python3` to print
  the one-line `Channel secret refused: …` and exit 1 when the secret is
  not usable, then `exec uvicorn app:asgi --app-dir .`; `--app` sets the
  entry, no `PYTHONPATH`), `README.RUN.txt`, and `MANIFEST.json`
  (`generator`, `name`, `entrypoint`, `static_model:
  single_copy_from_site_packages`, each file's `path` / `sha256` / `bytes`,
  and `resolved`: `version` and `vcs_commit` for ux-compose and the four
  specialists). No file names the build machine: no absolute path, no
  timestamp. Library JS is not vendored; the installed packages serve
  `/ux-dom/static/x_element.js`.
- The bundle also FAILs (and is not written) when:
  - `uxcompose doctor --prod` on the assembled bundle has a FAIL row, so
    build with `UX_CHANNEL_SECRET` set and `DEBUG` unset; a missing or
    unresolvable `requirements.txt` is the `requirements` row. A
    `requirements.txt` is never synthesized, and `-r` / `-c` includes are
    refused (the bundle ships `requirements.txt` alone).
  - the `requirements.txt` ux-compose line is not the ux-compose running
    the build (the line create-app would write now), since the bundle
    would install code the build did not check.
  - `SOURCE_DATE_EPOCH` is set and not a non-negative integer.
- `WARNING:` lines: an editable ux-compose checkout with uncommitted
  tracked changes (the bundle pins `HEAD`, so it matches no commit the
  build checked), and create-app's unpushed-`HEAD` note.
- `NAME.tar.gz` has one top-level `NAME/` directory, sorted members,
  uid/gid 0, mtime `SOURCE_DATE_EPOCH` (or 0) in the tar and gzip
  headers: two archives of the same tree are byte-identical.

Architecture: [../internals/hmr.md](../internals/hmr.md).
Decision: [../adr/0005-serve-dev-split.md](../adr/0005-serve-dev-split.md).
CSS how-to: [TAILWIND.md](TAILWIND.md).
