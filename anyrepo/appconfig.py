"""Application Configuration Handling."""

from typing import Optional
import tomlkit
import tomlkit.exceptions
from pathlib import Path
from enum import Enum, auto

from pydantic import BaseSettings, Extra, ValidationError

from anyrepo.exceptions import InvalidConfigurationFileError, InvalidConfigurationLocationError, UninitializedError

from .workspace import Workspace
from .const import SYSTEM_CONFIG_DIR, USER_CONFIG_DIR, ANYREPO_PATH


class AppConfigData(BaseSettings, extra=Extra.allow):
    """
    Configuration data of the application.

    This class holds the concrete configuration values of the application.
    The following values are defined:

    :param color_ui: Defines if outputs by the tool shall be colored.
    """

    color_ui: Optional[bool]


class _EnvAppConfigData(AppConfigData, env_prefix="anyrepo_", case_sensitive=False):
    """
    Configuration data read from the environment.

    This class is used to read the configuration values from the user's environment variables.
    """


class AppConfigLocation(Enum):
    """
    The location where configuration options are stored.

    This enum encodes the different locations where the application stores information.
    """

    SYSTEM = auto()
    """
    System wide configuration.

    Use this to refer to configuration options for the entire system.
    """

    USER = auto()
    """
    User configuration.

    Use this to refer to configuration specific to the current user.
    """

    WORKSPACE = auto()
    """
    Workspace configuration.

    Use this to refer to configuration specific to the current workspace (if any).
    """


class AppConfig:
    """
    Application wide configuration.

    This class holds the application wide configuration and also provides means to modify it.
    """

    CONFIG_FILE_NAME = "config.toml"
    """The name of the configuration file."""

    def __init__(
        self,
        system_config_dir: Optional[str] = None,
        user_config_dir: Optional[str] = None,
        workspace_config_dir: Optional[str] = None,
    ) -> None:
        super().__init__()
        if system_config_dir is None:
            system_config_dir = SYSTEM_CONFIG_DIR
        if user_config_dir is None:
            user_config_dir = USER_CONFIG_DIR
        if workspace_config_dir is None:
            try:
                workspace_config_dir = str(Workspace.find_path() / ANYREPO_PATH)
            except UninitializedError:
                pass
        self._system_config_dir = system_config_dir
        self._user_config_dir = user_config_dir
        self._workspace_config_dir = workspace_config_dir
        self._merged_config: Optional[AppConfigData] = None

    @staticmethod
    def _load_config_from_path(file_path: Path) -> tomlkit.TOMLDocument:
        """
        Load the configuration file at the given path.

        Args:
            file_path: The path to the config file to load.

        Raises:
            InvalidConfigurationFileError: The configuration file cannot be parsed.
        """
        try:
            config_data = file_path.read_text()
        except FileNotFoundError:
            # If the file does not exist, construct a default settings object
            return tomlkit.TOMLDocument()
        try:
            return tomlkit.loads(config_data)
        except tomlkit.exceptions.ParseError as parse_error:
            # If we cannot parse the config file, raise an error here as we cannot
            # safely continue
            raise InvalidConfigurationFileError(file_path, str(parse_error)) from parse_error

    def _load_configuration(self, location: AppConfigLocation) -> tomlkit.TOMLDocument:
        """
        Load a configuration file from a location.

        This loads a configuration file from a specific location.

        Args:

            location: The location to load the configuration from.

        Raises:
            UninitializedError: When trying to load the workspace configuration while being outside a workspace.
            InvalidConfigurationLocationError: When an invalid location has been specified.
        """
        config_file_path = self._get_config_file_path(location)
        return AppConfig._load_config_from_path(config_file_path)

    def _get_config_file_path(self, location: AppConfigLocation) -> Path:
        """
        Given a storage location, return the path to the config file.

        Raises:
            InvalidConfigurationLocationError: The location given is invalid.
        """
        if location == AppConfigLocation.SYSTEM:
            return Path(self._system_config_dir) / AppConfig.CONFIG_FILE_NAME
        if location == AppConfigLocation.USER:
            return Path(self._user_config_dir) / AppConfig.CONFIG_FILE_NAME
        if location == AppConfigLocation.WORKSPACE:
            workspace_config_dir = self._workspace_config_dir
            if workspace_config_dir is not None:
                return Path(workspace_config_dir) / AppConfig.CONFIG_FILE_NAME
            raise UninitializedError()
        raise InvalidConfigurationLocationError(str(location))

    def load_configuration(self, location: AppConfigLocation) -> AppConfigData:
        """
        Load the configuration from the specified location.

        This loads and evaluates the configuration from the specified location.

        Args:
            location: The location to load the configuration from.

        Raises:
            InvalidConfigurationFileError: The configuration file is invalid and cannot be used.
            InvalidConfigurationLocationError: The location given is invalid.
        """
        try:
            doc = self._load_configuration(location)
        except UninitializedError:
            return AppConfigData()
        try:
            return AppConfigData(**doc)
        except ValidationError as validation_error:
            raise InvalidConfigurationFileError(
                self._get_config_file_path(location), str(validation_error)
            ) from validation_error

    @property
    def options(self) -> AppConfigData:
        """
        Get the effective options used by the application.

        This returns a configuration object which is built by merging the system,
        user and workspace configuration as well as configurations read from environment
        variables.
        """
        if self._merged_config is None:
            sys_config = self.load_configuration(AppConfigLocation.SYSTEM)
            user_config = self.load_configuration(AppConfigLocation.USER)
            workspace_config = self.load_configuration(AppConfigLocation.WORKSPACE)
            env_config = _EnvAppConfigData()
            merged_config_data = {}
            merged_config_data.update(sys_config.dict())
            merged_config_data.update(user_config.dict())
            merged_config_data.update(workspace_config.dict())
            merged_config_data.update(env_config.dict())
            self._merged_config = AppConfigData(**merged_config_data)
        return self._merged_config

    def _create_merged_config(self) -> AppConfigData:
        data = self._system_settings.dict()
        data.update(self._user_settings.dict())
        data.update(self._local_settings.dict())
        data.update(self._env_settings.dict())

        # Provide some sensible defaults (in case some options are not set anywhere):
        if "color_ui" not in data:
            data["color_ui"] = True

        return AppConfigData(**data)
