# Copyright 2022 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""Collection Of All Exceptions Which Might Occur."""

from pathlib import Path


class UninitializedError(RuntimeError):
    """Git Workspace Has Not Been Initialized."""

    def __init__(self):
        super().__init__("git workspace has not been initialized yet.")


class InitializedError(RuntimeError):
    """Git Workspace Has Already Been Initialized."""

    def __init__(self, path, main_path):
        super().__init__(
            f"git workspace has already been initialized at {str(path)!r} with main repo at {str(main_path)!r}."
        )
        self.path = path
        self.main_path = main_path


class NoGitError(RuntimeError):
    """Git Clone Has Not Been Initialized."""

    def __init__(self):
        super().__init__("git clone has not been found or initialized yet.")


class ManifestNotFoundError(RuntimeError):
    """Manifest File Has Not Been Found."""

    def __init__(self, path):
        super().__init__(f"Manifest has not been found at {str(path)!r}.")
        self.path = path


class ManifestExistError(RuntimeError):
    """Manifest Already Exists."""

    def __init__(self, path):
        super().__init__(f"Manifest exists at {str(path)!r}.")


class OutsideWorkspaceError(RuntimeError):
    """Project Is Located Outside Of Workspace."""

    def __init__(self, path, project_path):
        super().__init__(f"Project {str(project_path)!r} is located outside {str(path)!r}.")
        self.path = path
        self.project_path = project_path


class WorkspaceNotEmptyError(RuntimeError):
    """Workspace Is Not Empty."""

    def __init__(self, path):
        super().__init__(f"Workspace {str(path)!r} is not an empty directory.")
        self.path = path


class ManifestError(RuntimeError):
    """The Manifest Is Invalid."""

    def __init__(self, path, details):
        super().__init__(f"Manifest {str(path)!r} is broken: {details}")
        self.path = path
        self.details = details


class InvalidConfigurationFileError(RuntimeError):
    """A Configuration File Is Invalid And Cannot Be Used."""

    def __init__(self, path: Path, details: str):
        super().__init__(f"The configuration file {path} cannot be read: {details}")
        self.path = path
        self.details = details


class InvalidConfigurationLocationError(RuntimeError):
    """An Invalid Location For Configuration Data Has Been Used."""

    def __init__(self, location: str):
        super().__init__(f"The configuration location {location} is not known")
        self.location = location


class InvalidConfigurationValueError(RuntimeError):
    """An invalid configuration value has been passed to the application."""

    def __init__(self, key: str, value):
        super().__init__(f"Invalid value {value} has been passed to option {key}")
        self.key = key
        self.value = value


class InvalidConfigurationOptionError(RuntimeError):
    """An invalid configuration option has been passed to the applicaiton."""

    def __init__(self, key):
        super().__init__(f"Unknown configuration option {key}")
        self.key = key


class GitCloneMissingError(RuntimeError):
    """Git Clone Is Missing."""

    def __init__(self, project_path):
        super().__init__(f"Git Clone {str(project_path)!r} is missing.")
        self.project_path = project_path


class GitCloneNotCleanError(RuntimeError):
    """Git Clone Contains Changes."""

    def __init__(self, project_path):
        super().__init__(f"Git Clone {str(project_path)!r} contains changes.")
        self.project_path = project_path


class GitCloneMissingOriginError(RuntimeError):
    """Git Clone has no remote 'origin'."""

    def __init__(self, project_path, remote="origin"):
        super().__init__(f"Git Clone {str(project_path)!r} has not remote '{remote}'.")
        self.project_path = project_path
        self.remote = remote


class GitTagExistsError(RuntimeError):

    """Git Tag already exists."""

    def __init__(self, tag):
        super().__init__(f"tag {tag} already exists")
        self.tag = tag
