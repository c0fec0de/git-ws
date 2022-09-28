"""General Constants."""
from pathlib import Path
from appdirs import user_config_dir, site_config_dir

ANYREPO_PATH = Path(".anyrepo")
INFO_PATH = ANYREPO_PATH / "info.toml"
MANIFEST_PATH_DEFAULT: Path = Path("anyrepo.toml")

APP_NAME = "AnyRepo"
APP_AUTHOR = "c0fec0de"

SYSTEM_CONFIG_DIR = site_config_dir(APP_NAME, appauthor=APP_AUTHOR)
USER_CONFIG_DIR = user_config_dir(APP_NAME, appauthor=APP_AUTHOR)
