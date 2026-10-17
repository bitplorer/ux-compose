"""Form fields — the remaining 99% of inputs.

Signup / wizard / typeahead live in ``forms.py``. This file is every other
control a product actually ships:

    radio / checkbox set     names in RefState + dirty
    combobox                 query MorphState + value MorphState
    date                     named window MorphState; ISO in RefState
    file drop                filenames RefState + dirty
    slider                   magnitude RefState + dirty
    OTP                      digits RefState; verify is a Cap
    password reveal          bool MorphState; secret RefState
    autosave                 unsaved MorphState; draft RefState
    limited note             length derived from RefState

Never put ints / money / counts on MorphState if the class will go live
(Channel session plane refuses quantity). Named steps, bools, and short
strings are legal.

Validation is public. The verb that *creates / charges / verifies identity*
is Cap-protected.

Run:
  PYTHONPATH=src:. python examples/fields.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.autosave import Autosave
from ux_compose.components.choicegroup import ChoiceGroup
from ux_compose.components.combobox import Combobox
from ux_compose.components.datefield import DateField
from ux_compose.components.filedrop import FileDrop
from ux_compose.components.limitednote import LimitedNote
from ux_compose.components.otpgate import OtpGate
from ux_compose.components.passwordfield import PasswordField
from ux_compose.components.sliderfield import SliderField


def demo() -> None:
    app = App.boot("Fields")
    app.add(
        ChoiceGroup,
        Combobox,
        DateField,
        FileDrop,
        SliderField,
        OtpGate,
        PasswordField,
        Autosave,
        LimitedNote,
    )
    print("finish", app.dispatch("choices.set_finish", key="wax"))
    print("combo", app.dispatch("combobox.pick", key="Wool throw"))
    print("date", app.dispatch("datefield.set_window", key="week"))
    print("file", app.dispatch("filedrop.add", name="linen.jpg"))
    print("slider", app.dispatch("slider.set", n="75"))
    print("otp", app.dispatch("otpgate.type", code="2468"))
    print("pass", app.dispatch("password.set", secret="held"))
    print("auto", app.dispatch("autosave.type", text="draft"))
    print("note", app.dispatch("limited.type", text="hello"))
    strict = App.boot("Fields", strict_caps=True)
    strict.add(OtpGate)
    try:
        strict.dispatch("otpgate.verify")
        print("UNEXPECTED verify")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
