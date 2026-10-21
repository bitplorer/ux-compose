"""``scaffold.scan_requirements`` reads requirements.txt as pip does (UC1 rule, UC8 row)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.scaffold import SPECIALISTS, scan_requirements

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


@pytest.mark.parametrize(
    "line",
    [
        "git+https://github.com/encode/httpx.git@abc",
        "-e git+https://gitlab.com/acme/tool.git@abc",
        "https://example.com/pkgs/ux-dom-main.tar.gz",
        "git+https://github.com/bitplorer/ux-dom-fork.git@abc",
        "git+https://github.com/someone/ux-dom.git@abc",
    ],
)
def test_nameless_requirement_is_reported_unidentifiable(tmp_path, line):
    """pip learns these names only by building them (#129); not a bitplorer specialist repo."""
    scan = _scan(tmp_path, f"ux-compose\n{line}\n")
    assert scan.problem is None
    assert scan.unchecked == [
        f"requirements.txt:2 names no distribution ({line.removeprefix('-e ')}); "
        "write 'name @ url' or add #egg=name"
    ]


def test_wheel_url_is_named_by_its_filename(tmp_path):
    scan = _scan(tmp_path, "ux-compose\nhttps://example.com/w/ux_dom-0.2.0-py3-none-any.whl\n")
    assert scan.problem == (
        "ux-dom (requirements.txt:2) pinned beside ux-compose; specialists come with the ux-compose line"
    )


@pytest.mark.parametrize("option", ["-c nope.txt", "--constraint=nope.txt", "-cnope.txt"])
def test_missing_constraints_file_fails_like_pip(tmp_path, option):
    assert _scan(tmp_path, f"ux-compose\n{option}\n").problem == (
        "requirements.txt:2: constrains with nope.txt, which does not exist"
    )


def test_constraints_are_not_requirements(tmp_path):
    scan = _scan(tmp_path, "ux-compose\n-c c.txt\n", **{"c.txt": "ux-dom==1\n"})
    assert scan == (None, [], {"ux-compose": "requirements.txt:1"})


@pytest.mark.parametrize(
    "lines",
    [
        "foo; python_version<'3.13'\nfoo; python_version>='3.13'\n",
        "foo==1; sys_platform=='win32'\nFoo @ https://x/foo.zip ; sys_platform!='win32'\n",
        "uvicorn\nuvicorn[standard]\n",
        "uvicorn[standard]>=0.30\nuvicorn[http]>=0.30\n",
    ],
    ids=["markers", "markers-differ-in-pin", "extras", "extras-same-pin"],
)
def test_pip_accepted_splits_are_not_duplicates(tmp_path, lines):
    """pip installs one distribution from these, so they are not a second line (#129)."""
    assert _scan(tmp_path, "ux-compose\n" + lines).problem is None


@pytest.mark.parametrize(
    "lines",
    [
        "foo\nfoo; python_version>='3.13'\n",
        "uvicorn\nuvicorn[standard]>=0.30\n",
        "foo; os_name=='nt'\nfoo; os_name=='nt'\n",
    ],
    ids=["one-unmarked", "extras-with-another-pin", "same-marker"],
)
def test_overlapping_lines_still_count_twice(tmp_path, lines):
    assert _scan(tmp_path, "ux-compose\n" + lines).problem.endswith("one line per distribution")


SPECIALIST_PIN = "{name} (requirements.txt:2) pinned beside ux-compose; specialists come with the ux-compose line"


@pytest.mark.parametrize(
    "line, name",
    [
        ("git+https://github.com/bitplorer/ux-dom.git@0440ccb", "ux-dom"),
        ("git+https://github.com/bitplorer/ux-dom@0440ccb", "ux-dom"),
        ("-e git+https://github.com/bitplorer/ux-dom.git@0440ccb", "ux-dom"),
        ("git+ssh://git@github.com/bitplorer/ux-behavior.git@abc", "ux-behavior"),
        ("git+git@github.com:bitplorer/ux-motion.git@abc", "ux-motion"),
        ("git+https://github.com/bitplorer/ux-channel.git@0ffe8e9#subdirectory=python", "ux-channel"),
        ("git+https://GitHub.com/Bitplorer/UX-Dom.git@abc", "ux-dom"),
        ("https://github.com/bitplorer/ux-dom/archive/0440ccb.tar.gz", "ux-dom"),
        ("https://github.com/bitplorer/ux-dom/archive/refs/heads/main.zip", "ux-dom"),
        ("https://github.com/bitplorer/ux-motion/tarball/abc", "ux-motion"),
        ("https://github.com/bitplorer/ux-motion/zipball/abc", "ux-motion"),
        ("https://codeload.github.com/bitplorer/ux-behavior/tar.gz/abc", "ux-behavior"),
        ("https://api.github.com/repos/bitplorer/ux-channel/tarball/abc", "ux-channel"),
        ("git+https://github.com/bitplorer/ux-dom.git@0440ccb ; python_version >= '3.14'", "ux-dom"),
    ],
)
def test_specialist_repo_url_without_egg_fails_like_a_named_pin(tmp_path, line, name):
    """UC1/D2: pip installs a second specialist from these, #egg or not (#137 review)."""
    scan = _scan(tmp_path, f"ux-compose\n{line}\n")
    assert scan.problem == SPECIALIST_PIN.format(name=name)
    assert scan.unchecked == []


@pytest.mark.parametrize("space", ["", " "])
def test_name_at_url_marker_without_space_is_named(tmp_path, space):
    """pip splits ``name @ url;marker`` at ``;``, so the unspaced form names ux-dom too (#137 review)."""
    line = f'ux-dom @ git+https://github.com/bitplorer/ux-dom.git@0440ccb{space};python_version >= "3.14"'
    scan = _scan(tmp_path, f"ux-compose\n{line}\n")
    assert scan.problem == SPECIALIST_PIN.format(name="ux-dom")


def test_name_at_url_marker_without_space_splits_like_the_spaced_form(tmp_path):
    scan = _scan(
        tmp_path,
        "ux-compose\nfoo @ https://x/foo.zip;sys_platform=='win32'\nfoo @ https://x/foo.zip ; sys_platform!='win32'\n",
    )
    assert scan.problem is None and scan.unchecked == []


def test_bare_compose_url_names_ux_compose(tmp_path):
    scan = _scan(tmp_path, "git+https://github.com/bitplorer/ux-compose.git@abc\n")
    assert scan.problem is None and scan.names == {"ux-compose": "requirements.txt:1"}


# #140: every requirement form resolves to a distribution identity — the declared
# name, else the wheel/sdist filename, else the bitplorer repo — and a ux-*
# specialist identity FAILs, whatever the form, marker or extras.
def _spellings(name):
    """PEP 503: case and runs of ``-_.`` do not change the name."""
    return [name, name.upper().replace("-", "_"), name.replace("-", ".").title()]


def _dist(name):
    """A wheel/sdist filename's distribution field (``-`` is the field separator)."""
    return name.replace("-", "_").replace(".", "_")


MARKERS = ["", ' ; python_version >= "3.14"', ";sys_platform=='linux'"]
EXTRAS = ["", "[standard]", "[a,b]"]
# {n}: a spelling of the specialist, {d}: it as a filename field, {r}: its repo, {e}: extras, {m}: marker.
NAMED_FORMS = [
    "{n}{e}{m}",
    "{n}{e}==0.2.0{m}",
    "{n}{e} @ git+https://github.com/someone/fork.git@abc{m}",
    "{n}{e} @ https://example.com/whatever.zip{m}",
    "git+https://github.com/someone/fork.git@abc#egg={n}{e}{m}",
]
URL_FORMS = [
    "git+https://github.com/bitplorer/{r}.git@abc{m}",
    "git+ssh://git@github.com/bitplorer/{r}.git@abc{m}",
    "git+git@github.com:bitplorer/{r}.git@abc{m}",
    "git+https://github.com/bitplorer/{r}@abc#subdirectory=python{m}",
    "https://github.com/bitplorer/{r}/archive/abc.tar.gz{m}",
    "https://codeload.github.com/bitplorer/{r}/zip/refs/heads/main{m}",
    "https://api.github.com/repos/bitplorer/{r}/tarball/abc{m}",
    "https://files.example.com/p/{d}-0.2.0-py3-none-any.whl{m}",
    "https://files.example.com/p/{d}-0.2.0-py3-none-any.whl#sha256=00{m}",
    "https://files.example.com/p/{d}-0.2.0-py3-none-any.whl?raw=true{m}",
    "https://github.com/someone/fork/releases/download/v1/{d}-0.2.0-py3-none-any.whl{m}",
    "https://files.example.com/p/{d}-0.2.0.tar.gz{m}",
    "https://files.example.com/p/{d}-0.2.0.zip{m}",
    "file:///srv/wheels/{d}-0.2.0-cp314-cp314-manylinux_2_17_x86_64.whl{m}",
    "./wheels/{d}-0.2.0-py3-none-any.whl{m}",
]
EDITABLE_FORMS = [
    "-e git+https://github.com/bitplorer/{r}.git@abc",
    "--editable=git+https://github.com/someone/fork.git@abc#egg={n}{e}",
    "-e git+ssh://git@github.com/bitplorer/{r}.git@abc#subdirectory=py",
    "-e ./vendor/{r}",
    "-e ./src/checkout",  # its pyproject.toml names the specialist
    "./src/checkout",
]


def _cases():
    out = []
    for name in SPECIALISTS:
        for spell in _spellings(name):
            for form in NAMED_FORMS:
                for e in EXTRAS:
                    for m in MARKERS:
                        out.append((name, form.format(n=spell, e=e, m=m)))
            for form in URL_FORMS:
                for m in MARKERS:
                    out.append((name, form.format(r=spell, d=_dist(spell), m=m)))
            for form in EDITABLE_FORMS:
                for e in EXTRAS if "{e}" in form else [""]:
                    out.append((name, form.format(n=spell, r=spell, e=e)))
    return out


SPECIALIST_CASES = _cases()


@pytest.mark.parametrize("name, line", SPECIALIST_CASES, ids=[line for _, line in SPECIALIST_CASES])
def test_every_form_naming_a_specialist_fails(tmp_path, name, line):
    """UC1/D2: a second specialist must never install, by any requirement form (#140)."""
    (tmp_path / "src" / "checkout").mkdir(parents=True)
    (tmp_path / "src" / "checkout" / "pyproject.toml").write_text(
        f'[project]\nname = "{name.upper()}"\nversion = "0"\n', encoding="utf-8"
    )
    scan = _scan(tmp_path, f"ux-compose\n{line}\n")
    assert scan.problem == SPECIALIST_PIN.format(name=name)


def test_the_cross_product_is_full():
    per_spelling = len(NAMED_FORMS) * len(EXTRAS) * len(MARKERS) + len(URL_FORMS) * len(MARKERS) + 5 + len(EXTRAS)
    assert len(SPECIALIST_CASES) == len(SPECIALISTS) * 3 * per_spelling


@pytest.mark.parametrize(
    "line",
    [
        "git+https://github.com/someone/ux-dom.git@abc",
        "git+https://github.com/someone/ux-dom.git@abc ; python_version >= '3.14'",
        "-e git+https://github.com/someone/ux-behavior.git@abc",
        "git+ssh://git@github.com/someone/ux-motion.git@abc",
        "https://github.com/someone/ux-channel/archive/abc.tar.gz",
        "https://codeload.github.com/someone/ux-dom/tar.gz/abc",
        "git+https://github.com/bitplorer/ux-dom-fork.git@abc",
        "git+https://github.com/bitplorer/uxdom.git@abc",
        "git+https://gitlab.com/bitplorer/ux-dom.git@abc",
        "git+git@gitlab.com:someone/ux-dom@abc",
        "https://example.com/pkgs/ux-dom-main.tar.gz",
        "https://example.com/pkgs/tool.tar.gz;sys_platform=='linux'",
    ],
)
def test_forks_and_unknown_urls_warn_with_their_text(tmp_path, line):
    """A fork or an unrelated URL is not a specialist; pip names it only by building it."""
    scan = _scan(tmp_path, f"ux-compose\n{line}\n")
    assert scan.problem is None
    url = line.removeprefix("-e ").split(";")[0].strip()
    assert len(scan.unchecked) == 1 and url in scan.unchecked[0]


@pytest.mark.parametrize(
    "line, name",
    [
        ("ux-dom-fork", "ux-dom-fork"),
        ("uxdom[standard] ; python_version >= '3.14'", "uxdom"),
        ("ux-dom-fork @ git+https://github.com/bitplorer/ux-dom.git@abc", "ux-dom-fork"),
        ("https://x/p/ux_dom_fork-0.2.0-py3-none-any.whl ; python_version >= '3.14'", "ux-dom-fork"),
        ("https://x/p/ux_behavior_extra-1.0.tar.gz", "ux-behavior-extra"),
        ("https://github.com/someone/fork/releases/download/v1/httpx-0.27.0-py3-none-any.whl", "httpx"),
        ("-e ./vendor/lib", None),
        ("-e git+https://github.com/someone/ux-dom.git@abc#egg=my-dom", "my-dom"),
    ],
)
def test_forks_and_other_distributions_do_not_fail(tmp_path, line, name):
    scan = _scan(tmp_path, f"ux-compose\n{line}\n")
    assert scan.problem is None and scan.unchecked == []
    assert set(scan.names) == {"ux-compose"} | ({name} if name else set())


def test_declared_egg_name_wins_over_the_repo(tmp_path):
    """``#egg`` is the declared name; pip refuses a build whose metadata disagrees."""
    scan = _scan(tmp_path, "ux-compose\n-e git+https://github.com/bitplorer/ux-dom.git@abc#egg=other-name\n")
    assert scan.problem is None and "other-name" in scan.names


# (3) A diamond include reads D twice through two parents; that is not a cycle.
def test_diamond_include_is_not_a_failure(tmp_path):
    scan = _scan(
        tmp_path,
        "ux-compose\n-r b.txt\n-r c.txt\n",
        **{"b.txt": "-r d.txt\n", "c.txt": "-r d.txt\n", "d.txt": "fastapi\n"},
    )
    assert scan.problem is None
    assert scan.names == {"ux-compose": "requirements.txt:1", "fastapi": "d.txt:1"}


def test_deep_cycle_still_fails(tmp_path):
    scan = _scan(
        tmp_path,
        "ux-compose\n-r b.txt\n-r c.txt\n",
        **{"b.txt": "-r d.txt\n", "c.txt": "-r d.txt\n", "d.txt": "-r c.txt\n"},
    )
    assert scan.problem == "c.txt:1: includes d.txt, which includes this file again"


# (4) Duplicate lines whose markers can both hold on one interpreter are two lines.
@pytest.mark.parametrize(
    "lines",
    [
        "foo; python_version>='3.13'\nfoo; sys_platform=='linux'\n",
        "foo; python_version>='3.12'\nfoo; python_version>='3.14'\n",
        "foo; os_name=='posix'\nfoo; sys_platform=='darwin'\n",
        "foo; platform_machine=='x86_64'\nfoo; implementation_name=='cpython'\n",
        "foo; python_version >= '3.14'\nfoo; python_version>='3.14'\n",
    ],
    ids=["version-and-platform", "nested-versions", "posix-and-darwin", "machine-and-impl", "spacing-only"],
)
def test_overlapping_markers_count_twice(tmp_path, lines):
    assert _scan(tmp_path, "ux-compose\n" + lines).problem == (
        "foo is listed twice (requirements.txt:2, requirements.txt:3); one line per distribution"
    )


@pytest.mark.parametrize(
    "lines",
    [
        "foo; sys_platform=='win32'\nfoo; sys_platform=='linux'\n",
        "foo; os_name=='nt'\nfoo; sys_platform=='darwin'\n",
        "foo; python_version<'3.15'\nfoo; python_version>='3.15'\n",
        "foo; platform_system=='Windows'\nfoo; platform_system!='Windows'\n",
        "foo; implementation_name=='pypy'\nfoo; implementation_name=='cpython' and os_name=='posix'\n",
    ],
)
def test_disjoint_markers_stay_one_install(tmp_path, lines):
    assert _scan(tmp_path, "ux-compose\n" + lines).problem is None
