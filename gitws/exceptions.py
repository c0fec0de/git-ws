# Copyright 2022-2023 c0fec0de
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
from typing import Optional


class UninitializedError(RuntimeError):
    """Git Workspace Has Not Been Initialized."""

    def __init__(self):
        super().__init__("git workspace has not been initialized yet.")


class InitializedError(RuntimeError):
    """Git Workspace Has Already Been Initialized."""

    def __init__(self, path: Path, main_path: Optional[Path]):
        msg = f"git workspace has already been initialized at {str(path)!r}"
        if main_path:
            msg = f"{msg} with main repo at {str(main_path)!r}."
        else:
            msg = f"{msg}."
        super().__init__(msg)
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
    """Reference To Outside Of Workspace."""

    def __init__(self, workspace_path, path, what):
        super().__init__(f"{what} {str(path)!r} refers outside of workspace ({str(workspace_path)!r}).")
        self.workspace_path = workspace_path
        self.path = path


class NotEmptyError(RuntimeError):
    """Directory Is Not Empty."""

    def __init__(self, path):
        super().__init__(f"{str(path)!r} is not an empty directory.")
        self.path = path


class WorkspaceNotEmptyError(RuntimeError):
    """Workspace Is Not Empty."""

    def __init__(self, path, items):
        items = ", ".join(str(item) for item in items)
        super().__init__(f"Workspace {str(path)!r} is not an empty directory. It contains: {items}.")
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
    """An Invalid Configuration Value Has Been Passed To The Application."""

    def __init__(self, key: str, value):
        super().__init__(f"Invalid value {value} has been passed to option {key}")
        self.key = key
        self.value = value


class InvalidConfigurationOptionError(RuntimeError):
    """An Invalid Configuration Option Has Been Passed To The Applicaiton."""

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
    """Git Clone Has No Remote ``Origin``."""

    def __init__(self, project_path, remote="origin"):
        super().__init__(f"Git Clone {str(project_path)!r} has not remote '{remote}'.")
        self.project_path = project_path
        self.remote = remote


class GitTagExistsError(RuntimeError):
    """Git Tag Already Exists."""

    def __init__(self, tag):
        super().__init__(f"tag {tag} already exists")
        self.tag = tag


class NoMainError(RuntimeError):
    """Workspace Has No Main Project."""

    def __init__(self):
        super().__init__("Workspace has been initialized from manifest only, without a main project.")


class NoAbsUrlError(RuntimeError):
    """No Relative Url Possible."""

    def __init__(self, project_name: str):
        msg = (
            "Absolute URL required. Please specify an absolute "
            f"'url' or a 'sub_url' with a 'remote' for {project_name!r}."
        )
        super().__init__(msg)


class FileRefConflict(RuntimeError):
    """File Reference Conflict."""

    def __init__(self, dest: Path, existing: Path, conflict: Path):
        msg = f"File {str(dest)!r} reference from {str(conflict)!r} already referenced from {str(existing)!r}"
        super().__init__(msg)
        self.dest = dest
        self.existing = existing
        self.conflict = conflict


class FileRefModifiedError(RuntimeError):
    """File Reference Got Modified."""

    def __init__(self, dest: Path, src: Path):
        msg = f"File {str(dest)!r} got manipulated. (Originally {str(src)!r})"
        super().__init__(msg)
        self.dest = dest
        self.src = src


class IncompatibleFormatError(RuntimeError):
    """Incompatibility Error."""
