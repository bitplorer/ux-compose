"""Kit Batch B product: chat, questionnaire.

Isolation: this file never imports ux_channel. No Cap kernel / cek-runtime / law.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.kit.catalog import CATALOG, resolve
from ux_compose.kit.copy import copy_component


PRODUCT_B = ("chat", "questionnaire")


def _boot(*classes, **kwargs):
    app = App.boot("KitProductB", **kwargs)
    app.add(*classes)
    return app


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def _cls(stem: str):
    meta = CATALOG[stem]
    mod = __import__(meta["module"], fromlist=[meta["name"]])
    return getattr(mod, meta["name"])


def test_product_b_stems_resolve():
    for stem in PRODUCT_B:
        meta = resolve(stem)
        assert meta["stem"] == stem
        assert meta["css"] is False
        assert meta["page"] is True
    assert resolve("question-naire")["stem"] == "questionnaire" or resolve("questionnaire")["stem"] == "questionnaire"


def test_product_b_render_document_trees():
    from ux_compose.helpers import _serialize_tree

    for stem in PRODUCT_B:
        cls = _cls(stem)
        tree = cls().render()
        assert not isinstance(tree, str), stem
        html = _serialize_tree(tree)
        assert f'id="{cls.id}"' in html, stem
        assert "ux_channel" not in html
        assert "<html" not in html.lower()


def test_chat_log_and_send():
    Chat = _cls("chat")
    app = _boot(Chat, strict_caps=False)
    html = _html(app, "chat")
    assert 'role="log"' in html
    assert "aria-live" in html
    assert 'for="chat-draft"' in html or 'id="chat-draft"' in html
    assert "the table is set" in html

    app.dispatch("chat.send", text="held until dusk")
    inst = app.behavior.get("chat")
    lines = tuple(inst.lines or ())
    assert any("held until dusk" in str(x) for x in lines)
    html = _html(app, "chat")
    assert "held until dusk" in html
    assert not bool(inst.typing)

    app.dispatch("chat.peer_type")
    assert bool(inst.typing)
    html = _html(app, "chat")
    assert "typing" in html.lower()
    app.dispatch("chat.peer_done")
    assert not bool(inst.typing)
    assert any("Atelier" in str(x) for x in tuple(inst.lines or ()))


def test_questionnaire_radios_and_submit_cap():
    Questionnaire = _cls("questionnaire")
    app = _boot(Questionnaire, strict_caps=False)
    html = _html(app, "questionnaire")
    assert "<fieldset" in html or "fieldset" in html
    assert "<legend" in html or "legend" in html
    assert 'role="radiogroup"' in html
    assert 'role="radio"' in html
    assert "aria-checked" in html

    app.dispatch("questionnaire.choose", question="fit", key="close")
    inst = app.behavior.get("questionnaire")
    answers = dict(inst.answers or ())
    assert answers.get("fit") == "close"
    html = _html(app, "questionnaire")
    assert 'data-fit="close"' in html or "close" in html.lower()

    app.dispatch("questionnaire.submit")
    assert bool(inst.done)

    strict = _boot(Questionnaire, strict_caps=True)
    with pytest.raises(Exception):
        strict.dispatch("questionnaire.submit")


def test_a11y_smoke_product_b():
    app = _boot(_cls("chat"), _cls("questionnaire"), strict_caps=False)
    chat = _html(app, "chat")
    assert 'role="log"' in chat
    assert 'id="chat-draft"' in chat
    quiz = _html(app, "questionnaire")
    assert 'role="radiogroup"' in quiz
    assert "aria-labelledby" in quiz or "<legend" in quiz


def test_product_b_caps():
    kit = ROOT / "src" / "ux_compose" / "kit"
    chat_src = (kit / "chat.py").read_text(encoding="utf-8")
    assert '@action(caps=())' in chat_src
    assert "caps=(" not in chat_src.replace('@action(caps=())', "")
    quiz_src = (kit / "questionnaire.py").read_text(encoding="utf-8")
    assert "form.submit" in quiz_src


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_copy_product_b(tmp_path: Path):
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    for stem in PRODUCT_B:
        written = copy_component(stem, root=tmp_path)
        ast.parse(written["py"].read_text(encoding="utf-8"))
        assert "ux_channel" not in written["py"].read_text(encoding="utf-8")
