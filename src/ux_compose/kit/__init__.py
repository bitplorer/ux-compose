"""Deprecated: use ux_compose.components (one release of warnings, then removed).

from ux_compose.kit import Tabs and ux_compose.kit.<stem> keep working
and point at the same objects in ux_compose.components.
"""

from __future__ import annotations

import importlib as _importlib
import sys as _sys
import warnings as _warnings

_warnings.warn(
    "ux_compose.kit is deprecated; import from ux_compose.components "
    "(removed after one release).",
    DeprecationWarning,
    stacklevel=2,
)

from ux_compose.components import *  # noqa: F401,F403,E402
from ux_compose.components import __all__  # noqa: E402,F401

_STEMS = "accordion actionsheet alert alertdialog attachment avatar badge banner bottomnav breadcrumb calendar card carousel chart chat colorpicker combobox command contextmenu countdown cta datepicker descriptionlist dialog diff drawer dropdown emptystate fab featuregrid feed fieldset fileupload filterbar footer formlayout hero hovercard login logocloud menubar mockup multiselect navbar navmenu newsletter otp overlay pagination plans popover pricingsection progress pullrefresh questionnaire rating resizable scrollarea searchbar select separator sheet sidebar skeleton slider spinbutton stats stepper switch table tabs tagsinput testimonials themeswitch timeline toast togglegroup toolbar tooltip tree typeahead usermenu ".split()

for _stem in _STEMS:
    _sys.modules[f"{__name__}.{_stem}"] = _importlib.import_module(
        f"ux_compose.components.{_stem}"
    )
