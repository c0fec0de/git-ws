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

"""Test API."""


def test_imports():
    """Test imports."""
    # pylint: disable=unused-import,too-many-locals,import-outside-toplevel
    from gitws import (
        AppConfig,
        AppConfigData,
        AppConfigLocation,
        Clone,
        Defaults,
        Git,
        GitCloneMissingError,
        GitCloneMissingOriginError,
        GitWS,
        Group,
        GroupFilter,
        GroupFilters,
        GroupSelect,
        GroupSelects,
        InitializedError,
        InvalidConfigurationFileError,
        InvalidConfigurationLocationError,
        Manifest,
        ManifestError,
        ManifestExistError,
        ManifestIter,
        ManifestNotFoundError,
        ManifestSpec,
        NoGitError,
        OutsideWorkspaceError,
        Project,
        ProjectIter,
        ProjectSpec,
        Remote,
        UninitializedError,
        Workspace,
        WorkspaceNotEmptyError,
        find_workspace,
    )
