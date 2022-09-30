"""General Constants."""

from pathlib import Path

from appdirs import site_config_dir, user_config_dir

ANYREPO_PATH = Path(".anyrepo")
"""The sub-folder in which the tool stores workspace related data."""

INFO_PATH = ANYREPO_PATH / "info.toml"

MANIFEST_PATH_DEFAULT: Path = Path("anyrepo.toml")
"""
The default path to the manifest file.
"""

APP_NAME = "AnyRepo"
APP_AUTHOR = "c0fec0de"

SYSTEM_CONFIG_DIR = site_config_dir(APP_NAME, appauthor=APP_AUTHOR)
"""The default location where to look for system wide configuration files."""

USER_CONFIG_DIR = user_config_dir(APP_NAME, appauthor=APP_AUTHOR)
"""The default location where to look for user configuration files."""
