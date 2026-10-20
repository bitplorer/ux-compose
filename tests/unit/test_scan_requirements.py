"""``scaffold.scan_requirements`` reads requirements.txt as pip does (UC1 rule, UC8 row)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.scaffold import scan_requirements

CORPUS = Path(__file__).resolve().parent / "requirements_corpus"


def _scan(tmp_path, text, **others):
    for name, body in others.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(body, encoding="utf-8")
    req = tmp_path / "requirements.txt"
    req.write_text(text, encoding="utf-8")
    return scan_requirements(req)


@pytest.mark.parametrize(
    "text, problem",
    [
        ("ux-compose @ git+https://x/ux-compose.git@abc#subdirectory=py  # pinned\n", None),
        ("# header\n\nUX_Compose==0.2.0\nuvicorn[standard]>=0.30 ; python_version>='3.14'\n", None),
        ("ux-compose\n-e .\n-e ./vendor/lib\n", None),
        ("ux-compose\nhttps://example.com/pkgs/tool-1.0-py3-none-any.whl\n", None),
        (
            "ux-compose\nfastapi\nFastAPI>=0.115\n",
            "fastapi is listed twice (requirements.txt:2, requirements.txt:3); one line per distribution",
        ),
        (
            "ux-compose\nux_compose @ https://x/a.zip\n",
            "ux-compose is listed twice (requirements.txt:1, requirements.txt:2); one line per distribution",
        ),
        (
            "ux-compose\nux-motion\nux-channel\n",
            "ux-channel (requirements.txt:3), ux-motion (requirements.txt:2) pinned beside "
            "ux-compose; specialists come with the ux-compose line",
        ),
        (
            "ux-compose\n-e git+https://github.com/bitplorer/ux-dom.git@abc#egg=ux-dom\n",
            "ux-dom (requirements.txt:2) pinned beside ux-compose; specialists come with the ux-compose line",
        ),
        (
            "ux-compose\n--editable=git+https://x/f.git#egg=FastAPI\nfastapi\n",
            "fastapi is listed twice (requirements.txt:2, requirements.txt:3); one line per distribution",
        ),
        ("ux-compose\nnot a requirement!\n", "requirements.txt:2: not a requirement: 'not a requirement!'"),
        ("ux-compose\n--index-url 'https://x\n", "requirements.txt:2: cannot read options (No closing quotation)"),
        ("fastapi\n", "requirements.txt does not name ux-compose"),
    ],
)
def test_one_line_per_distribution(tmp_path, text, problem):
    assert _scan(tmp_path, text).problem == problem


def test_continuations_and_hashes_join_into_one_requirement(tmp_path):
    scan = _scan(
        tmp_path,
        "ux-compose \\\n    --hash=sha256:00 \\\n    --hash=sha256:11\n    # via -r requirements.in\n"
        "idna==3.10 --hash=sha256:22\n",
    )
    assert scan.problem is None
    assert scan.names == {"ux-compose": "requirements.txt:1", "idna": "requirements.txt:5"}


def test_options_are_not_requirements(tmp_path):
    scan = _scan(
        tmp_path,
        "--index-url https://pypi.org/simple\n--extra-index-url=https://x/simple\n"
        "-f ./wheels\n--find-links https://x/links\n--trusted-host x\n--pre\n"
        "-c constraints.txt\n--constraint=constraints.txt\nux-compose\n",
        **{"constraints.txt": "ux-dom==1\n"},
    )
    assert scan == (None, [], {"ux-compose": "requirements.txt:9"})


def test_includes_are_followed_relative_to_the_including_file(tmp_path):
    scan = _scan(
        tmp_path,
        "-r reqs/base.txt\nux-compose\n",
        **{"reqs/base.txt": "-rshared.txt\n", "reqs/shared.txt": "ux-dom\n"},
    )
    assert scan.problem == (
        "ux-dom (reqs/shared.txt:1) pinned beside ux-compose; specialists come with the ux-compose line"
    )


def test_include_duplicates_count(tmp_path):
    scan = _scan(tmp_path, "--requirement base.txt\nfastapi\nux-compose\n", **{"base.txt": "fastapi\n"})
    assert scan.problem == (
        "fastapi is listed twice (base.txt:1, requirements.txt:2); one line per distribution"
    )


def test_include_cycle_fails_like_pip(tmp_path):
    scan = _scan(tmp_path, "ux-compose\n-r a.txt\n", **{"a.txt": "-r requirements.txt\n"})
    assert scan.problem == "a.txt:1: includes requirements.txt, which includes this file again"


def test_missing_include_fails(tmp_path):
    assert _scan(tmp_path, "ux-compose\n-r nope.txt\n").problem == (
        "requirements.txt:2: includes nope.txt, which does not exist"
    )


def test_remote_include_is_unchecked_not_failed(tmp_path):
    scan = _scan(tmp_path, "ux-compose\n-r https://example.com/r.txt\n")
    assert scan.problem is None
    assert scan.unchecked == ["requirements.txt:2 includes https://example.com/r.txt"]


# Real-world shapes; tests/integration/test_requirements_corpus_pip.py proves pip accepts them.
@pytest.mark.parametrize(
    "name, names",
    [
        ("hashed.txt", {"certifi": "hashed.txt:2", "idna": "hashed.txt:6"}),
        ("index_options.txt", {"idna": "index_options.txt:7", "certifi": "index_options.txt:8"}),
        ("includes.txt", {"idna": "includes_common.txt:1", "certifi": "includes_extra.txt:1"}),
    ],
)
def test_corpus_parses(name, names):
    scan = scan_requirements(CORPUS / name)
    assert scan.names == names
    # The corpus installs plain PyPI packages, so only the ux-compose rule is unmet.
    assert scan.problem == f"{name} does not name ux-compose"
    assert scan.unchecked == []
