# ADR 0006 — serve-dev shared session store

> **Status:** accepted · **Date:** 2026-09-09 · **Layer:** ux-compose + ux-channel
> Process split: [0005-serve-dev-split.md](0005-serve-dev-split.md)
> Architecture: [../internals/hmr.md](../internals/hmr.md)

## Decision

ADR 0005 isolates Channel from ui reload (origin + ui + channel).
That split is not a durable store. Document GET stays on the ui
worker (HMR for route edits). Caps stay on the channel worker.
Both processes must see the same MorphState / `ch.draft`.

**Channel owns the store implementation.** `FileStateStore` lives
next to `MemoryStateStore` / `RedisStateStore` in
`ux_channel.host.stores`. Values are JSON (`default=str`), same
domain as Redis — not pickle. `change()` uses `BEGIN IMMEDIATE` so
ui + channel cannot lose increments.

**Compose owns delivery lifecycle only.** When `REDIS_URL` is unset,
`uxcompose serve dev` prepares `.uxcompose-serve-dev.state`, exports
`UXCOMPOSE_STATE_STORE`, clears that sqlite bag on
`serve restart-channel`, and unlinks WAL sidecars on shutdown. It
does not export both envs. `src/ux_compose/serve_state.py` never
imports `ux_channel` and does not define a store class. Doctor
`scan_store_clone` / `scan_store_precedence` fail closed if a store
class reappears or both envs are set.

`Channel.boot` opens `FileStateStore` when `UXCOMPOSE_STATE_STORE`
is set and `REDIS_URL` is not. Channel prefers Redis when both are
set. `serve dev` will not export both. Compose does not duck-assign
`channel.state`.

## Why

A compose-owned `FileStateStore` (PR #58) closed the split-brain
hole by cloning Channel's StateStore protocol. Isolation held.
Ownership Law did not. The next agent would clone again.

JSON matches Redis. Pickle in a cwd file was a threat (and a lie:
serve-dev accepted objects production Redis would stringify).

## Consequences

- `src/ux_compose/serve_state.py` — env, path, prepare / clear / drop.
- `src/ux_compose/wire/boot.py` — no `channel.state =` assignment.
- Sister: `ux_channel.host.stores.FileStateStore` + boot env honor.
- Restart-channel still means "empty the sqlite bag and respawn
  Channel". It does not clear Redis.
- Pin ux-channel to a SHA that includes `FileStateStore`, the
  #27 Cap / health honesty, Cuts 1–2 CLI/layout honesty, and Cut C
  empty Content-Type fail-closed
  (`985e58aee76ca683774c4d4d58ab30a1d3b6efee`). Current compose pin
  `ae5a675991db5c168d0b6df018e929d808c7511f` is Soft 1+2 on that floor.

## Rejected

| Alternative | Why not |
|-------------|---------|
| Keep compose FileStateStore | Second store product; pickle |
| Revert PR #58 | Hole returns |
| Route HTML GET to channel | Drops route-edit HMR |
| Redis required for `serve dev` | Author DX cost |
| Duck-assign from `wire/boot.py` forever | Boot already selects Memory/Redis |

## Frozen names

`UXCOMPOSE_STATE_STORE`, `.uxcompose-serve-dev.state`,
`serve restart-channel`. Do not rename.
