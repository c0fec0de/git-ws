"""AppConfig testing."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from pytest import raises

import anyrepo.const
from anyrepo.appconfig import AppConfig, AppConfigLocation
from anyrepo.exceptions import InvalidConfigurationFileError, InvalidConfigurationLocationError

TEST_DATA_ROOT = Path(__file__).parent / "testdata" / "appconfig"


def _app_config_from(scenario: str, include_workspace=True, **kwargs):
    args = {
        "system_config_dir": str(TEST_DATA_ROOT / scenario / "system"),
        "user_config_dir": str(TEST_DATA_ROOT / scenario / "user"),
    }
    if include_workspace:
        args["workspace_config_dir"] = str(TEST_DATA_ROOT / scenario / "workspace")
    args.update(kwargs)

    return AppConfig(**args)


def test_default_construction():
    """Test if constructing a config object with default paths works."""
    AppConfig()


def test_defaults():
    """Test is sensible defaults are set."""
    config = _app_config_from("empty", use_config_from_env=False)
    assert config.options.color_ui
    assert config.options.manifest_path == str(anyrepo.const.MANIFEST_PATH_DEFAULT)


def test_single_file_config():
    """Test if loading a single config file works."""
    for location in "system", "user", "workspace":
        config = _app_config_from(location + "-only", use_config_from_env=False)
        assert config.options.manifest_path == (location + "-foo-bar-baz-123.xyz")


def test_two_configs():
    """
    Test if loading two configs works.

    This tests if we have two configs that can overrule each other (user beats system, workspace beats user and
    workspace beats system) the overriding works as expected.
    """
    locations_and_winners = (
        ("system-and-user", "user"),
        ("user-and-workspace", "workspace"),
        ("system-and-workspace", "workspace"),
    )
    for location, winner in locations_and_winners:
        config = _app_config_from(location, use_config_from_env=False)
        assert config.options.manifest_path == (winner + "-foo-bar-baz-123.xyz")


def test_three_configs():
    """
    Test if loading three configs works.

    If all three config files (system, user and workspace) are present, we expect the workspace one
    to win and override the options of the other two.
    """
    config = _app_config_from("all", use_config_from_env=False)
    assert config.options.manifest_path == "workspace-foo-bar-baz-123.xyz"


def test_no_workspace_config():
    """Test if loading works if there is no workspace config."""
    config = _app_config_from("all", include_workspace=False, use_config_from_env=False)
    assert config.options.manifest_path == "user-foo-bar-baz-123.xyz"


@mock.patch.dict(os.environ, {"ANYREPO_MANIFEST_PATH": "env-foo-bar-baz-123.xyz"})
def test_config_from_env():
    """
    Test loading configuration values from the environment.

    The user can - at any point - override configuration values by setting
    environment variables. Test that this works and overrides the ones we loaded
    from configuration files.
    """
    config = _app_config_from("all")
    assert config.options.manifest_path == "env-foo-bar-baz-123.xyz"


def test_invalid_config_file():
    """
    Test behavior when loading an invalid configuration file.

    If we try to load a configuration which is "broken", we expect an appropriate exception to be
    thrown.
    """
    config = _app_config_from("invalid_config", use_config_from_env=False)
    with raises(InvalidConfigurationFileError):
        print(config.options.manifest_path)


def test_invalid_config_file_2():
    """
    Test behavior when loading an invalid configuration file.

    If we try to load a configuration file which cannot be validated against our own schema, we expect
    an appropriate exception to be thrown.
    """
    config = _app_config_from("invalid_config_2", use_config_from_env=False)
    with raises(InvalidConfigurationFileError):
        print(config.options.manifest_path)


def test_invalid_config_location():
    """If - for whatever reason - an invalid config location is used, we expect a specific exception."""
    with raises(InvalidConfigurationLocationError):
        AppConfig()._load_configuration("Hello World")  # pylint: disable=protected-access


def test_write_config():
    """Test if writing configuration values works."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "system").mkdir()
        config = AppConfig(
            system_config_dir=tmp_path / "system",
            user_config_dir=tmp_path / "user",
            workspace_config_dir=tmp_path / "workspace",
            use_config_from_env=False,
        )
        options = config.options
        assert options.color_ui
        assert options.manifest_path == "anyrepo.toml"

        with config.edit_configuration(AppConfigLocation.SYSTEM) as sys_conf:
            sys_conf.color_ui = False
            sys_conf.manifest_path = "foo.toml"

        options = config.options
        assert not options.color_ui
        assert options.manifest_path == "foo.toml"

        sys_conf = config.load_configuration(AppConfigLocation.SYSTEM)
        sys_conf.color_ui = None
        sys_conf.manifest_path = None

        config.save_configuration(sys_conf, AppConfigLocation.SYSTEM)

        options = config.options
        assert options.color_ui
        assert options.manifest_path == "anyrepo.toml"
