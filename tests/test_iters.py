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

"""Iterator Testing."""
from pathlib import Path

from gitws import GroupFilters, ManifestIter, ProjectIter, Workspace


def test_empty_project_iter(tmp_path):
    """Empty Project Iterator."""
    workspace = Workspace.init(tmp_path)
    manifest_path = Path("none.toml")
    group_filters: GroupFilters = []
    project_iter = ProjectIter(workspace, manifest_path, group_filters)
    assert tuple(project_iter) == tuple()


def test_empty_manifest_iter(tmp_path):
    """Empty Manifest Iterator."""
    workspace = Workspace.init(tmp_path)
    manifest_path = Path("none.toml")
    group_filters: GroupFilters = []
    manifest_iter = ManifestIter(workspace, manifest_path, group_filters)
    assert tuple(manifest_iter) == tuple()
