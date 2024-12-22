#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "ignorelib",
#     "python-magic",
# ]
# ///

"""
Packfiles allows merging multiple files into a single Markdown file.
"""

import argparse
import io
import re
import sys
from pathlib import Path
from shutil import copyfileobj
from subprocess import CalledProcessError, check_output
from typing import TextIO

from ignorelib import IgnoreFilterManager
from magic import Magic

__author__ = "EcmaXp"
__version__ = "0.1.0"
__license__ = "MIT"
__url__ = "https://pypi.org/project/packfiles/"
__all__ = []

CODE_MIME_TYPES_PATTERN = re.compile(r"^(text/.*|application/json|.*\+xml)$")

GIT_IGNORE_FILEPATHS: list[Path] = [
    # get_git_global_ignore_file_paths():
    # - `.git/info/exclude` (git repo)
    # - `~/.gitignore` (git user)
]
GIT_IGNORE_PATTERNS = [
    ".git",
    "*.lock",
]
GIT_IGNORE_FILENAME = ".gitignore"

magic = Magic(mime=True)


def packfiles(
    path: Path,
    *,
    ignore_filter: IgnoreFilterManager | None = None,
) -> None:
    if path.is_dir():
        files = sorted(path.rglob("*"))
        folder = path
    else:
        files = [path]
        folder = path.parent

    folder = get_git_root(path) or path
    if ignore_filter is None:
        ignore_filter = get_ignore_filter(folder)

    for file in files:
        if not file.is_file():
            continue
        if ignore_filter.is_ignored(str(file)):
            continue
        if not is_source_code_file(file):
            continue

        packfile(file, folder)


def packfile(file: Path, folder: Path):
    print(f"```{file.relative_to(folder)}")

    with open(file, "r", encoding="utf-8") as f:
        copyfileobj(f, sys.stdout)
        if not is_ends_with_newline(f):
            print()

    print("```")
    print()


def is_ends_with_newline(fp: TextIO) -> bool:
    pos = fp.tell()
    try:
        fp.seek(fp.seek(0, io.SEEK_END) - 1)
        return fp.read(1) == "\n"
    finally:
        fp.seek(pos)


def get_git_root(path: Path) -> Path | None:
    if (path / ".git").is_dir():
        return path
    if path == path.parent:
        return None
    return get_git_root(path.parent)


def get_git_core_excludesfile() -> Path | None:
    try:
        global_ignore_file = check_output(
            ["git", "config", "core.excludesfile"],
            encoding="utf-8",
        )
    except CalledProcessError:
        return None
    return Path(global_ignore_file).expanduser()


def get_ignore_filter(path: Path) -> IgnoreFilterManager:
    return IgnoreFilterManager.build(
        str(path),
        global_ignore_file_paths=list(map(str, get_git_global_ignore_file_paths(path))),
        global_patterns=GIT_IGNORE_PATTERNS,
        ignore_file_name=GIT_IGNORE_FILENAME,
    )


def get_git_global_ignore_file_paths(path: Path) -> list[Path]:
    global_ignore_file_paths = GIT_IGNORE_FILEPATHS.copy()
    if git_root := get_git_root(path):
        global_ignore_file_paths.append(git_root / ".git" / "info" / "exclude")
    if git_core_excludesfile := get_git_core_excludesfile():
        global_ignore_file_paths.append(git_core_excludesfile)
    return global_ignore_file_paths


def is_source_code_file(path: Path) -> bool:
    mime_type = magic.from_file(path)
    return CODE_MIME_TYPES_PATTERN.match(mime_type) is not None


parser = argparse.ArgumentParser(description=(__doc__ or "").strip())
parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
parser.add_argument("path", type=Path, nargs="*", default=[Path(".")])


def main() -> None:
    args = parser.parse_args()
    for path in args.path:
        packfiles(path)


if __name__ == "__main__":
    main()
