"""Shared Tailwind class strings. No companion CSS. No viewport sm: inside cards."""

from __future__ import annotations

# Nested kit cards sit in a product column. Containment stays on the card
# (min-w-0 + overflow-x-hidden) so Prev/Next/dots wrap instead of escaping
# rounded chrome. max-w-* is a column concern, not a card concern.
CARD = (
    "relative flex w-full min-w-0 flex-col gap-4 overflow-x-hidden "
    "rounded-3xl border border-stone-200 bg-white p-5 text-stone-900 shadow-sm"
)

CARD_WIDE = (
    "relative flex w-full min-w-0 flex-col gap-4 overflow-x-hidden "
    "rounded-3xl border border-stone-200 bg-white p-5 text-stone-900 shadow-sm"
)

SHELL = (
    "min-h-dvh bg-[#f3efe6] text-stone-900 antialiased"
)

WRAP = "mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 px-3.5 py-5"

KICKER = "text-xs font-medium uppercase tracking-widest text-stone-400"
TITLE = "m-0 font-serif text-3xl font-semibold tracking-tight"
LEDE = "m-0 text-sm leading-relaxed text-stone-500"
