"""Shared Tailwind class strings. Dark-first SaaS desk; light via ``.dark`` off."""

from __future__ import annotations

# Product shell — containment lives here, not inside kit cards.
SHELL = (
    "min-h-dvh antialiased [font-feature-settings:'ss01'] "
    "bg-[#f4f6f9] text-slate-900 "
    "dark:bg-[#07090d] dark:text-slate-100"
)

RAIL = (
    "flex w-56 shrink-0 flex-col gap-1 border-r border-slate-200/80 "
    "bg-white/80 px-3 py-5 backdrop-blur "
    "dark:border-white/10 dark:bg-[#0c1017]/90"
)

WRAP = "mx-auto flex w-full min-w-0 max-w-[88rem] flex-col gap-5 px-4 py-5 lg:px-6"

TOP = (
    "sticky top-0 z-30 flex min-w-0 flex-wrap items-center justify-between gap-3 "
    "border-b border-slate-200/80 bg-[#f4f6f9]/85 px-4 py-3.5 backdrop-blur "
    "dark:border-white/10 dark:bg-[#07090d]/80"
)

PANEL = (
    "relative flex w-full min-w-0 flex-col gap-4 overflow-hidden "
    "rounded-2xl border border-slate-200 bg-white p-5 text-slate-900 "
    "shadow-sm dark:border-white/10 dark:bg-[#121822] dark:text-slate-100 "
    "dark:shadow-[0_1px_0_rgba(255,255,255,0.04)]"
)

KICKER = (
    "text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400 "
    "dark:text-slate-500"
)
TITLE = "m-0 font-serif text-2xl font-semibold tracking-tight"
LEDE = "m-0 text-sm leading-relaxed text-slate-500 dark:text-slate-400"
NUM = "m-0 font-serif text-3xl font-semibold tracking-tight tabular-nums"

BTN = (
    "inline-flex min-h-10 cursor-pointer items-center justify-center rounded-full "
    "border-0 bg-teal-700 px-4 text-sm font-medium text-white hover:bg-teal-600 "
    "dark:bg-teal-400 dark:text-slate-950 dark:hover:bg-teal-300"
)
BTN_GHOST = (
    "inline-flex min-h-10 cursor-pointer items-center justify-center rounded-full "
    "border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 "
    "hover:bg-slate-50 dark:border-white/10 dark:bg-transparent dark:text-slate-200 "
    "dark:hover:bg-white/5"
)

# Kit copies inherit these so cards sit in a product column, not a max-w-xl island.
KIT_CARD = (
    "relative flex w-full min-w-0 flex-col gap-4 overflow-x-hidden "
    "rounded-2xl border border-slate-200 bg-white p-5 text-slate-900 shadow-sm "
    "dark:border-white/10 dark:bg-[#121822] dark:text-slate-100"
)
KIT_KICKER = KICKER
KIT_TITLE = "m-0 font-serif text-xl font-semibold tracking-tight"
KIT_LEDE = LEDE
KIT_TILE = (
    "flex flex-col gap-1 rounded-2xl bg-slate-50 px-4 py-4 "
    "dark:bg-[#0c1017]"
)
KIT_BTN = BTN
KIT_BTN_GHOST = BTN_GHOST
