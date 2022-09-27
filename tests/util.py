"""Test Utilities."""
import contextlib
import os

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


def format_caplog(tmp_path, caplog):
    """Format caplog."""
    return [record.getMessage().replace(str(tmp_path), "WORK") for record in caplog.records]
