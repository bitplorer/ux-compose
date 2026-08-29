"""Floor shell tokens. No viewport sm: inside kit cards."""

from __future__ import annotations

SHELL = "min-h-dvh bg-[#f3efe6] text-stone-900 antialiased"
WRAP = "mx-auto flex w-full min-w-0 max-w-3xl flex-col gap-8 px-4 py-8"
KICKER = (
    "text-[0.6875rem] font-medium uppercase tracking-[0.22em] text-stone-400"
)
TITLE = (
    "m-0 font-serif text-[2.15rem] font-semibold leading-[1.12] tracking-[-0.03em]"
)
LEDE = "m-0 max-w-[42ch] text-[0.95rem] leading-relaxed text-stone-500"
ROOM = (
    "flex flex-col gap-2 rounded-[1.6rem] border border-stone-900/[0.07] "
    "bg-[#fdfcf8] p-6 shadow-[0_0_0_1px_rgba(22,21,19,0.03),0_28px_56px_-24px_rgba(22,21,19,0.2)] "
    "transition hover:-translate-y-0.5"
)
LOOSE = "flex w-full min-w-0 flex-col gap-8"
