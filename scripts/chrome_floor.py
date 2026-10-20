"""Fail unless Chrome's major version is at least 155.

CI and the Login, PasswordField and HMR reload browser tests call this
script.
A missing binary, a broken binary, a version with no digits, and a
major below 155 exit non-zero.
"""
from __future__ import annotations

import re
import subprocess
import sys


def main(argv: list[str]) -> int:
    binary = argv[1] if len(argv) > 1 else "google-chrome"
    try:
        text = subprocess.check_output(
            [binary, "--version"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Chrome version check failed for {binary}: {exc}", file=sys.stderr)
        return 1
    text = text.strip()
    print(text)
    match = re.search(r"(\d+)", text)
    if match is None:
        print(f"Chrome version has no major number: {text}", file=sys.stderr)
        return 1
    major = int(match.group(1))
    print(f"Chrome major: {major}")
    if major < 155:
        print(f"Chrome {major} is below 155", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
