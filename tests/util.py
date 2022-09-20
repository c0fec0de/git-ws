import contextlib
import os
from subprocess import run  # noqa


@contextlib.contextmanager
def chdir(dir):
    """Change Working Directory to `dir`."""
    curdir = os.getcwd()
    try:
        os.chdir(dir)
        yield
    finally:
        os.chdir(curdir)
