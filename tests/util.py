"""Test Utilities."""
import contextlib
import os
import re

# pylint: disable=unused-import
from subprocess import run  # noqa

from click.testing import CliRunner

from gitws._cli import main


@contextlib.contextmanager
def chdir(path):
    """Change Working Directory to `path`."""
    curdir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(curdir)


def get_sha(path):
    """Get SHA for `path`."""
    assert (path / ".git").exists()
    result = run(("git", "rev-parse", "HEAD"), capture_output=True, check=True, cwd=path)
    return result.stdout.decode("utf-8").strip()


def format_output(result, tmp_path=None):
    """Format Command Output."""
    lines = result.output.split("\n")
    if tmp_path:
        lines = [replace_tmp_path(line, tmp_path) for line in lines]
    return lines


def format_logs(caplog, tmp_path=None):
    """Format Logs."""
    lines = [f"{record.levelname:7s} {record.name} {record.message}" for record in caplog.records]
    if tmp_path:  # pragma: no cover
        lines = [replace_tmp_path(line, tmp_path) for line in lines]
    return lines


def replace_tmp_path(text, tmp_path):
    """Replace `tmp_path` in `text`."""
    tmp_path_esc = re.escape(str(tmp_path))
    sep_esc = re.escape(os.path.sep)
    regex = re.compile(rf"{tmp_path_esc}([A-Za-z0-9_{sep_esc}]*)")

    def repl(mat):
        sub = mat.group(1) or ""
        sub = sub.replace(os.path.sep, "/")
        return f"TMP{sub}"

    return regex.sub(repl, text)


def cli(command, exit_code=0, tmp_path=None):
    """Invoke CLI."""
    result = CliRunner().invoke(main, command)
    assert result.exit_code == exit_code, result.exit_code
    return format_output(result, tmp_path=tmp_path)
