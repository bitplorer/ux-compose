"""Posted control names must arrive on static kit actions.

The payload matches a live control: ``data-channel-args`` (``field=``) plus
the input's ``name``. ux-behavior drops a key the action does not name, so
these tests are red until each ``set_field`` declares its fields.
"""
from __future__ import annotations

from ux_compose import App
from ux_compose.components.chat import Chat
from ux_compose.components.colorpicker import ColorPicker
from ux_compose.components.combobox import Combobox
from ux_compose.components.command import Command
from ux_compose.components.filterbar import FilterBar
from ux_compose.components.login import Login
from ux_compose.components.newsletter import Newsletter
from ux_compose.components.otp import Otp
from ux_compose.components.searchbar import SearchBar
from ux_compose.components.tagsinput import TagsInput


def _boot(component):
    app = App.boot("Posted", level=1, strict_caps=False)
    app.add(component)
    return app


def test_login_posted_fields_arrive():
    app = _boot(Login)
    app.dispatch("login.set_field", field="email", email="ada@atelier.test")
    app.dispatch("login.set_field", field="password", password="secret123")
    app.dispatch("login.set_field", field="name", name="Ada Lovelace")
    inst = app.behavior.get("login")
    assert inst.email == "ada@atelier.test"
    assert inst.password == "secret123"
    assert inst.name == "Ada Lovelace"


def test_newsletter_posted_email_arrives():
    app = _boot(Newsletter)
    app.dispatch("newsletter.set_field", field="email", email="ada@atelier.test")
    assert app.behavior.get("newsletter").email == "ada@atelier.test"


def test_otp_posted_code_arrives():
    app = _boot(Otp)
    app.dispatch("otp.set_field", field="code", code="123456")
    assert app.behavior.get("otp").code == "123456"


def test_combobox_posted_query_arrives():
    app = _boot(Combobox)
    app.dispatch("combobox.set_field", field="q", q="wool")
    assert app.behavior.get("combobox").query == "wool"
    app.dispatch("combobox.set_field", field="query", query="silk")
    assert app.behavior.get("combobox").query == "silk"


def test_command_posted_query_arrives():
    app = _boot(Command)
    app.dispatch("command.set_field", field="q", q="wool")
    assert app.behavior.get("command").query == "wool"
    app.dispatch("command.set_field", field="query", query="silk")
    assert app.behavior.get("command").query == "silk"


def test_chat_posted_text_arrives():
    app = _boot(Chat)
    app.dispatch("chat.set_field", field="text", text="held until dusk")
    assert app.behavior.get("chat").draft == "held until dusk"


def test_tagsinput_posted_tag_arrives():
    app = _boot(TagsInput)
    app.dispatch("tagsinput.set_field", field="tag", tag="wool")
    assert app.behavior.get("tagsinput").draft == "wool"


def test_searchbar_posted_query_arrives():
    app = _boot(SearchBar)
    app.dispatch("searchbar.set_field", field="q", q="wool")
    assert app.behavior.get("searchbar").query == "wool"


def test_filterbar_posted_query_arrives():
    app = _boot(FilterBar)
    app.dispatch("filterbar.set_field", field="q", q="wool")
    assert app.behavior.get("filterbar").query == "wool"


def test_choose_keeps_an_existing_query_when_q_is_empty():
    """An empty posted q must not wipe the query. The chip still applies."""
    app = _boot(FilterBar)
    app.dispatch("filterbar.set_field", field="q", q="wool")
    app.dispatch("filterbar.choose", key="linen", q="")
    inst = app.behavior.get("filterbar")
    assert str(inst.query) == "wool"
    assert str(inst.which) == "linen"


def test_choose_stores_a_nonempty_posted_query():
    app = _boot(FilterBar)
    app.dispatch("filterbar.choose", key="oak", q="board")
    inst = app.behavior.get("filterbar")
    assert str(inst.query) == "board"
    assert str(inst.which) == "oak"


def test_colorpicker_posted_hex_arrives():
    app = _boot(ColorPicker)
    app.dispatch("colorpicker.set_field", field="hex", hex="#112233")
    assert app.behavior.get("colorpicker").hex == "#112233"
