"""Common Options."""
import click

from ..const import MANIFEST_PATH_DEFAULT


def projects_option():
    """Projects Option."""
    return click.option(
        "--project",
        "-P",
        "projects",
        multiple=True,
        type=click.Path(file_okay=False),
        help="Project path to operate on only. All by default. This option can be specified multiple times.",
    )


def manifest_option(initial=False):
    """Manifest Option."""
    if initial:
        help_ = f"Manifest file. '{MANIFEST_PATH_DEFAULT!s}' by default."
    else:
        help_ = "Manifest file. Initial clone/init filter settings by default."
    return click.option("--manifest", "-M", type=click.Path(dir_okay=False), default=MANIFEST_PATH_DEFAULT, help=help_)


def update_option(default=None):
    """Update Option."""
    return click.option("--update", "-U", is_flag=True, help="Run 'anyrepo update' too.")


def filter_option(initial=False):
    """Filter Option."""
    if initial:
        help_ = """\
Group Filtering.
TODO: more details.
The setting becomes default for all successive runs.
"""
    else:
        help_ = """\
Group Filtering.
TODO: more details.
Initial clone/init filter settings by default.
"""
    return click.option("--filter", "-F", "filter_", help=help_)
