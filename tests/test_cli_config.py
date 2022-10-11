"""Tests of the config command line interface."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional
from unittest import mock

from click.testing import CliRunner
from pytest import mark

from gitws._cli import main
from gitws.const import (
    BLOCK_APP_CONFIG_FROM_ENV_ENV_NAME,
    MANIFEST_PATH_DEFAULT,
    SYSTEM_CONFIG_PATH_ENV_NAME,
    USER_CONFIG_PATH_ENV_NAME,
    WORKSPACE_CONFIG_PATH_ENV_NAME,
)

from .util import format_output


@mark.parametrize(
    "env_patches,cli_args,initial_manifest_path",
    [
        # Test editing system config
        ([SYSTEM_CONFIG_PATH_ENV_NAME], ["--system"], None),
        # Test editing user config
        ([USER_CONFIG_PATH_ENV_NAME], ["--user"], None),
        # Test editing workspace config
        ([WORKSPACE_CONFIG_PATH_ENV_NAME], ["--workspace"], None),
        # Test editing user config when outside workspace
        ([USER_CONFIG_PATH_ENV_NAME], [], str(MANIFEST_PATH_DEFAULT)),
        # Test editing workspace config when inside workspace
        ([USER_CONFIG_PATH_ENV_NAME, WORKSPACE_CONFIG_PATH_ENV_NAME], [], str(MANIFEST_PATH_DEFAULT)),
    ],
)
def test_config_cli(env_patches: List[str], cli_args: List[str], initial_manifest_path: Optional[str]):
    """Check that we can edit the system config file with the CLI."""
    with TemporaryDirectory() as tmpdir:
        patch = {
            # This prevents env variables that the user might have set from interfering with out testing:
            BLOCK_APP_CONFIG_FROM_ENV_ENV_NAME: "1"
        }
        for i, path_var in enumerate(env_patches):
            patch[path_var] = str(Path(tmpdir) / str(i))
        with mock.patch.dict(os.environ, patch):
            # Manifest path shall be at default
            result = CliRunner().invoke(main, ["config", "get", "manifest_path"] + cli_args)
            if initial_manifest_path is None:
                assert format_output(result) == ["", ""]
            else:
                assert format_output(result) == [initial_manifest_path, ""]

            # Same but with JSON output:
            result = CliRunner().invoke(main, ["config", "get", "manifest_path", "--format", "json"] + cli_args)
            assert json.loads(result.stdout) == {"manifest_path": initial_manifest_path}

            # Listing the config options shall show the manifest path as empty:
            result = CliRunner().invoke(main, ["config", "list"] + cli_args)
            if initial_manifest_path is None:
                assert "manifest_path" in format_output(result)
            else:
                assert "manifest_path = " + initial_manifest_path in format_output(result)

            # An the same with JSON output:
            result = CliRunner().invoke(main, ["config", "list", "--format", "json"] + cli_args)
            assert json.loads(result.output).get("manifest_path") == initial_manifest_path

            # Set the workspace path:
            result = CliRunner().invoke(main, ["config", "set", "manifest_path", "hello_world.toml"] + cli_args)
            assert result.exit_code == 0

            # Now, getting the variable shall yield the new value:
            result = CliRunner().invoke(main, ["config", "get", "manifest_path"] + cli_args)
            assert format_output(result) == ["hello_world.toml", ""]

            # Same for the listing:
            result = CliRunner().invoke(main, ["config", "list"] + cli_args)
            assert "manifest_path = hello_world.toml" in format_output(result)

            # Let's delete the value:
            result = CliRunner().invoke(main, ["config", "delete", "manifest_path"] + cli_args)
            assert result.exit_code == 0

            # We should now be back to the defaults:
            result = CliRunner().invoke(main, ["config", "get", "manifest_path"] + cli_args)
            if initial_manifest_path is None:
                assert format_output(result) == ["", ""]
            else:
                assert format_output(result) == [initial_manifest_path, ""]

            # Same with the listing:
            result = CliRunner().invoke(main, ["config", "list"] + cli_args)
            if initial_manifest_path is None:
                assert "manifest_path" in format_output(result)
            else:
                assert "manifest_path = " + initial_manifest_path in format_output(result)

            # Deleting a value which is currently unset should have no effect:
            result = CliRunner().invoke(main, ["config", "delete", "manifest_path"] + cli_args)
            assert result.exit_code == 0

            # By default, trying to set a value unknown to the tool shall yield an error:
            custom_config_val = "hello world"
            result = CliRunner().invoke(main, ["config", "set", "foo_bar_baz", custom_config_val] + cli_args)
            assert result.exit_code != 0

            # We can politely :
            result = CliRunner().invoke(
                main, ["config", "set", "foo_bar_baz", custom_config_val, "--ignore-unknown"] + cli_args
            )
            assert result.exit_code == 0

            # Reading the custom value should work, too:
            result = CliRunner().invoke(main, ["config", "get", "foo_bar_baz"] + cli_args)
            assert format_output(result) == [custom_config_val, ""]

            # When setting config values, we do some type checking. Let's see if the tool prevents
            # an invalid value to be set to a boolean like color_ui:
            result = CliRunner().invoke(main, ["config", "set", "color_ui", "foo"] + cli_args)
            assert result.exit_code != 0
            assert format_output(result) == ["Error: Invalid value foo has been passed to option color_ui", ""]
