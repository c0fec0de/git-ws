"""Test Utilities."""
import contextlib
import os
import re

# pylint: disable=unused-import
from subprocess import run  # noqa


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


def format_logs(caplog, tmp_path):
    """Format Logs."""

    return [replace_tmp_path(record.message, tmp_path) for record in caplog.records]


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
