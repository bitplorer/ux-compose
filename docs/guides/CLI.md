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
| editable or local git checkout (`pip install -e .`) | `ux-compose @ git+https://github.com/bitplorer/ux-compose.git@<HEAD>`, plus one stderr note: push that commit; uncommitted changes are not in it |
| package index | `ux-compose==<version>` |
| remote archive URL | `ux-compose @ <url>` |
| local wheel or sdist file, or not installed | create-app exits 1 and writes nothing |

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
- `uxcompose build` and `uxcompose serve prod` without a secret print one
  line, no traceback: `Channel secret missing: set UX_CHANNEL_SECRET (≥16
  chars) for prod, or DEBUG=1 for a local build`. build exits 1, serve prod
  exits 2. `ux_compose.doctor.secret_readiness(env)` is that check. When a
  secret is set but refused (the published dev secret), or `REDIS_URL` is
  set without one, build shows ux-behavior's own `[ATTACH_SECRET_REQUIRED]`
  line instead, still without a traceback.
- `uxcompose deploy` declares `UX_CHANNEL_SECRET` for every target and
  never writes a value: render `generateValue: true`; fly `fly secrets set`;
  docker `docker run -e UX_CHANNEL_SECRET`; railway `railway variables
  --set`; vps `EnvironmentFile=/etc/<name>.env`; checklist step 3.

Architecture: [../internals/hmr.md](../internals/hmr.md).
Decision: [../adr/0005-serve-dev-split.md](../adr/0005-serve-dev-split.md).
CSS how-to: [TAILWIND.md](TAILWIND.md).
