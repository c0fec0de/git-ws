"""General Constants."""

from pathlib import Path

ANYREPO_PATH = Path(".anyrepo")
"""The sub-folder in which the tool stores workspace related data, relative to the workspace folder."""

CONFIG_FILE_NAME = "config.toml"
"""Name of the config file in the :any:`ANYREPO_PATH`."""

INFO_PATH = ANYREPO_PATH / "info.toml"
"""Path to the info file relative to the workspace folder."""

CONFIG_PATH = ANYREPO_PATH / CONFIG_FILE_NAME
"""Path to the config file relative to the workspace folder."""

MANIFEST_PATH_DEFAULT: Path = Path("anyrepo.toml")
"""The default path to the manifest file, relative to the project folder."""

APP_NAME = "AnyRepo"
"""Application Name."""

APP_AUTHOR = "c0fec0de"
"""Application Author."""
