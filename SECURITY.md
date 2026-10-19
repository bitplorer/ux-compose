# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes (best-effort while pre-1.0) |
| 0.1.x   | No (unreleased; superseded by 0.2.0) |

## Threat model

Compose’s security is the union of the levels you enabled:

| Level | Specialist | Security you get |
|-------|------------|------------------|
| 0 | ux-dom | Render + CSP stamp. A plain route or fragment `str` is parsed and sanitized (`defHTML`); `Markup` and `raw()` stay verbatim. |
| 1 | ux-behavior | Offline Cap Law / `AuthorityError` |
| 2 | ux-channel | Live Caps, signed Intent, JTI |
| 3 | ux-motion | Plan IR. Plain strings that compose serializes are sanitized first; `Markup` and `raw()` are not. |

A plain `str` or `bytes` from a route or fragment is HTML. Compose parses it with ux-dom `defHTML` and drops runnable constructs (script, event handlers, Alpine and `hx-on` attributes, `javascript:` URLs). Safe tags stay. Pass `markupsafe.Markup` or an ux-dom `raw()` node to keep that markup verbatim. Author tag trees are not re-parsed. CSP remains the ux-dom stamp. A nonce is never stamped onto a plain `str` or `Markup`. Trusted inline scripts are `script()` nodes.

Product code must **not** import `ux_channel` outside compose `wire/`. HMR and tunnel exist only under `uxcompose serve`.

## Reporting

GitHub Security Advisory on [bitplorer/ux-compose](https://github.com/bitplorer/ux-compose/security/advisories/new) or **bitplorer@outlook.com**. If the bug is inside a specialist, we transfer it. Do not file a public issue for unreleased details.
