# Assets — styling contract

**Do not put CSS or client JS inside Python strings.**

## Correct path (ux-dom / Tailwind)

1. Author classes in Python (`className="…"`).
2. Design tokens + component classes live in `assets/css/input.css`.
3. Tailwind scans **this app** (`app.py`, `routes/**/*.py`) via `@source` or
   `tailwind.config.js`. The globs in this repo's `tailwind.config.js`
   (`apps/**`, `examples/**`, `src/**`) are for library demos.
4. Build (production minify):

```bash
# product output — same path uxdom build writes
python -m pytailwindcss \
  -i assets/css/input.css \
  -o assets/static/file/css/output.css \
  --minify

# ux-dom app layout (app/main.py) also:
#   uxdom build
# fallback if app/tailwindcss.py exists and input.css does not:
#   python -m app.tailwindcss
```

Dev watch is `--watch` instead of `--minify` (XOR). `uxcompose serve --hmr`
reloads the browser when `.css` changes; it does not compile.

5. Document/shell **links** `/css/output.css`. Mount
   `assets/static/file/css` at `/css`. Never `style(raw(CSS))`.
   Never `cdn.tailwindcss.com`.

Production deploy: compile before the image (commit `output.css`) or add a
Docker `RUN` minify. `uxcompose deploy` does not run Tailwind.
How-to: [docs/guides/TAILWIND.md](../docs/guides/TAILWIND.md).

## Demo hosts (atelier_*)

Until the demo hosts are full ux-dom scaffolds, they serve a static snapshot:

- `apps/atelier_studio/static/css/atelier.css`
- `apps/atelier_shop/static/css/atelier.css`

These are the same design system extracted from the old Python strings. Prefer
evolving `assets/css/input.css` and regenerating.

## Client JS

Specialist scripts only (`ux-channel.js`, `ux-motion-player.js`, idiomorph).
Host must not inject form-intercept / applyOps patches (`ENHANCE_JS` is forbidden).
