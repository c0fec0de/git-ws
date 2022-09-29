"""AppConfig testing."""

from pathlib import Path

from anyrepo.appconfig import AppConfig

TEST_DATA_ROOT = Path(__file__).parent / "testdata" / "appconfig"


def _app_config_from(scenario: str, **kwargs):
    return AppConfig(
        system_config_dir=str(TEST_DATA_ROOT / scenario / "system"),
        user_config_dir=str(TEST_DATA_ROOT / scenario / "user"),
        workspace_config_dir=str(TEST_DATA_ROOT / scenario / "workspace"),
        **kwargs
    )


def test_defaults():
    """Test is sensible defaults are set."""
    config = _app_config_from("empty", use_config_from_env=False)
    assert config.options.color_ui
