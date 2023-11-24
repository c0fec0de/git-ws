# Copyright 2022-2023 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""Test Utilities."""
import contextlib
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path, PosixPath
from subprocess import run

from click.testing import CliRunner

from gitws._cli import main

_RE_EMPTY_LINE = re.compile(r"[ \t]*\r")

LEARN = False


@contextlib.contextmanager
def chdir(path):
    """Change Working Directory to ``path``."""
    curdir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(curdir)


def get_sha(path):
    """Get SHA for ``path``."""
    assert (path / ".git").exists()
    result = run(("git", "rev-parse", "HEAD"), capture_output=True, check=True, cwd=path)
    return result.stdout.decode("utf-8").strip()


def format_output(result, tmp_path=None, repos_path=None):
    """Format Command Output."""
    text = result.output
    text = _RE_EMPTY_LINE.sub("", text)
    lines = text.split("\n")
    if repos_path:
        lines = [replace_path(line, repos_path, "REPOS") for line in lines]
    if tmp_path:
        lines = [replace_path(line, tmp_path, "TMP") for line in lines]
    return lines


def format_logs(caplog, tmp_path=None, repos_path=None, replacements=None):
    """Format Logs."""
    # Feel free to improve performance
    replacements = replacements or {}
    lines = [f"{record.levelname:7s} {record.name} {record.message}" for record in caplog.records]
    caplog.clear()
    for key, value in replacements.items():
        lines = [line.replace(str(key), value) for line in lines]
    if repos_path:
        lines = [replace_path(line, repos_path, "REPOS") for line in lines]
    if tmp_path:  # pragma: no cover
        lines = [replace_path(line, tmp_path, "TMP") for line in lines]
    return lines


def replace_path(text, path, repl):
    """Replace ``path`` by ``repl`` in ``text``."""
    path_esc = re.escape(str(path))
    sep_esc = re.escape(os.path.sep)
    regex = re.compile(rf"{path_esc}([A-Za-z0-9_{sep_esc}]*)")

    def func(mat):
        sub = mat.group(1)
        sub = sub.replace(os.path.sep, "/")
        return f"{repl}{sub}"

    return regex.sub(func, text)


def cli(command, exit_code=0, tmp_path=None, repos_path=None):
    """Invoke CLI."""
    result = CliRunner().invoke(main, command)
    output = format_output(result, tmp_path=tmp_path, repos_path=repos_path)
    assert result.exit_code == exit_code, (result.exit_code, output)
    return output


def check(workspace, name, path=None, content=None, exists=True, depth=None, branches=None):
    """Check."""
    path = path or name
    file_path = workspace / path / "data.txt"
    content = content or name
    if exists:
        assert file_path.exists()
        data = file_path.read_text()
        assert data == content, f"{data} == {content}"
    else:
        assert not file_path.exists()
    if depth is not None:
        result = run(("git", "log", "--pretty=%H"), cwd=(workspace / path), capture_output=True, check=True)
        lines = result.stdout.decode("utf-8").rstrip().split("\n")
        lines = [hash_ for hash_ in lines if hash_]
        assert depth == len(lines), f"{depth} == len({lines})"
    if branches is not None:
        result = run(("git", "branch", "--all"), cwd=(workspace / path), capture_output=True, check=True)
        lines = result.stdout.decode("utf-8").rstrip().split("\n")
        lines = [hash_ for hash_ in lines if hash_]
        assert branches == len(lines), f"{branches} == len({lines})"


def assert_gen(genpath, refpath, capsys=None, caplog=None, tmp_path=None, repos_path=None, replacements=None):
    """Compare Generated Files Versus Reference."""
    genpath.mkdir(parents=True, exist_ok=True)
    refpath.mkdir(parents=True, exist_ok=True)
    if capsys:
        assert tmp_path
        assert repos_path
        captured = capsys.readouterr()
        out = captured.out
        err = captured.err
        out = replace_path(out, repos_path, "REPOS")
        err = replace_path(err, repos_path, "REPOS")
        out = replace_path(out, tmp_path, "TMP")
        err = replace_path(err, tmp_path, "TMP")
        (genpath / "stdout.txt").write_text(out)
        (genpath / "stderr.txt").write_text(err)
    if caplog:
        with open(genpath / "logging.txt", "w", encoding="utf-8") as file:
            for item in format_logs(caplog, tmp_path=tmp_path, repos_path=repos_path, replacements=replacements):
                file.write(f"{item}\n")
    if LEARN:  # pragma: no cover
        logging.getLogger(__name__).warning("LEARNING %s", refpath)
        shutil.rmtree(refpath, ignore_errors=True)
        shutil.copytree(genpath, refpath)
    cmd = ["diff", "-r", "--exclude", "__pycache__", str(refpath), str(genpath)]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as error:  # pragma: no cover
        raise AssertionError(error.stdout.decode("utf-8")) from None


def assert_any(gen, refs):  # pragma: no cover
    """Check if one of the refs fits."""
    for ref in refs:
        if gen == ref:
            assert True
            break
    else:
        # complain enriched
        assert gen == refs[0], gen


def path2url(path: Path) -> str:
    """
    Convert ``path`` to URL.

    >>> path2url(Path("/tmp/foo"))
    'file:///tmp/foo'
    """
    path = PosixPath(path)
    return f"file://{path}"
