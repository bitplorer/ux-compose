"""Theme — Paper house is light-only. This still shows a locale/theme MorphState.

Ported from the ``systems`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    action,
    update_with,
    div,
    h2,
    p,
    header,
)

from ux_compose.author import act

class Theme(Component):
    """Paper house is light-only. This still shows a locale/theme MorphState."""

    id = "theme"
    locale = MorphState("en")

    def render(self):
        copy = {
            "en": "Quiet pieces for a working house.",
            "hi": "कामकाजी घर के शांत टुकड़े।",
        }[str(self.locale or "en")]
        kids = (
            header(
                p("Locale MorphState", className="kicker"),
                h2("Locale", className="widget-title"),
            ),
            p(copy, className="lede"),
            div(
                act("theme.set_locale", "English", kind="ghost", locale="en"),
                act("theme.set_locale", "हिंदी", kind="ghost", locale="hi"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def set_locale(self, locale: str = "en"):
        self.locale = locale if locale in {"en", "hi"} else "en"
        return update_with(self)


__all__ = ["Theme"]
