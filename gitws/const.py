"""General Constants."""

from pathlib import Path

GIT_WS_PATH = Path(".git-ws")
"""The sub-folder in which the tool stores workspace related data, relative to the workspace folder."""

CONFIG_FILE_NAME = "config.toml"
"""Name of the config file in the :any:`GIT_WS_PATH`."""

INFO_PATH = GIT_WS_PATH / "info.toml"
"""Path to the info file relative to the workspace folder."""

CONFIG_PATH = GIT_WS_PATH / CONFIG_FILE_NAME
"""Path to the config file relative to the workspace folder."""

MANIFEST_PATH_DEFAULT: Path = Path("git-ws.toml")
"""The default path to the manifest file, relative to the project folder."""

APP_NAME = "GitWS"
"""Application Name."""

APP_AUTHOR = "c0fec0de"
"""Application Author."""

SYSTEM_CONFIG_PATH_ENV_NAME = "GIT_WS_CONFIG_SYSTEM_DIR"
"""The name of the environment variable which points to an alternative system config folder path."""

USER_CONFIG_PATH_ENV_NAME = "GIT_WS_CONFIG_USER_DIR"
"""The name of the environment variable which points to an alternative user config folder path."""

WORKSPACE_CONFIG_PATH_ENV_NAME = "GIT_WS_CONFIG_WORKSPACE_DIR"
"""The name of the environment variable which points to an alternative workspace config folder path."""

BLOCK_APP_CONFIG_FROM_ENV_ENV_NAME = "GIT_WS_ENV_NO_LOAD"
"""If this environment variable is set, do not evaluate environment variables when loading the app config."""
