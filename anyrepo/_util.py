"""Utilities."""
import logging
import subprocess

_LOGGER = logging.getLogger("anyrepo")
# Dependencies to any anyrepo module are forbidden here!

_LOGLEVELMAP = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


def get_loglevel(verbose: int):
    """Return `logging.level` according to verbosity."""
    return _LOGLEVELMAP.get(verbose, logging.DEBUG)


def run(cmd, cwd=None, capture_output=False, check=True):
    """Simplified wrapper around subprocess.run."""
    try:
        result = subprocess.run(cmd, capture_output=capture_output, check=check, cwd=cwd)
        _LOGGER.info("run(%r) OK stdout=%r stderr=%r", cmd, result.stdout, result.stderr)
        return result
    except subprocess.CalledProcessError as error:
        _LOGGER.info("run(%r) FAILED stdout=%r stderr=%r", cmd, error.stdout, error.stderr)
        raise error


def no_banner(text):
    """Just suppress `text`."""
