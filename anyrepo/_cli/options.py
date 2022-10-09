"""Common Command Line Options."""
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
        default = MANIFEST_PATH_DEFAULT
    else:
        help_ = "Manifest file. Initial clone/init settings by default."
        default = None
    return click.option(
        "--manifest", "-M", "manifest_path", type=click.Path(dir_okay=False), default=default, help=help_
    )


def update_option():
    """Update Option."""
    return click.option("--update", "-U", is_flag=True, help="Run 'anyrepo update' too.")


def force_option():
    """Force Option."""
    return click.option("--force", "-f", is_flag=True, help="Enfore operation.")


def groups_option(initial=False):
    """Group Filter Option."""
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
    return click.option("--groups", "-G", "groups", help=help_)


def output_option():
    """Manifest Output Option."""
    return click.option(
        "--output",
        "-O",
        "output",
        type=click.Path(dir_okay=False),
        help="Write Manifest to file instead of STDOUT.",
    )


def paths_argument():
    """Paths."""
    return click.argument("paths", nargs=-1, type=click.UNPROCESSED)
