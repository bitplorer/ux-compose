"""Lumen shell tokens. Kit cards keep their own ``class_*``. No ``sm:`` inside kit."""

from __future__ import annotations

SHELL = "min-h-dvh bg-[#12110f] text-[#f3efe6] antialiased"
WRAP = "mx-auto flex w-full min-w-0 max-w-3xl flex-col gap-10 px-4 py-10"
KICKER = (
    "text-[0.6875rem] font-medium uppercase tracking-[0.22em] text-[#c4a574]"
)
TITLE = (
    "m-0 font-serif text-[2.35rem] font-semibold leading-[1.08] tracking-[-0.03em] "
    "text-[#f4f0e8]"
)
LEDE = "m-0 max-w-[44ch] text-[0.95rem] leading-relaxed text-[#9a9388]"
ROOM = (
    "flex flex-col gap-2 rounded-[1.5rem] border border-white/[0.08] "
    "bg-[#1b1a17] p-6 shadow-[0_24px_48px_-28px_rgba(0,0,0,0.8)] "
    "transition hover:-translate-y-0.5 hover:border-[#c4a574]/35"
)
LOOSE = "flex w-full min-w-0 flex-col gap-8"
