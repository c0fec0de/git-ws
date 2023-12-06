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
from typing import List

from pytest import fixture

from gitws import GroupFilters, ManifestSpec, Project, ProjectSpec, Workspace, const, save
from gitws._iters import ManifestIter, ProjectIter, ProjectLevelIter
from gitws._manifestformatmanager import ManifestFormatManager
from gitws.gitwsmanifestformat import GitWSManifestFormat

from .fixtures import git_repo
from .util import path2url


@fixture
def mngr():
    """Provide Initialized ManifestFormatManager."""
    mngr = ManifestFormatManager()
    mngr.add(GitWSManifestFormat())
    yield mngr


def test_empty_project_iter(tmp_path, mngr):
    """Empty Project Iterator."""
    workspace = Workspace.init(tmp_path)
    manifest_path = Path("none.toml")
    group_filters: GroupFilters = []
    assert tuple(ProjectIter(workspace, mngr, manifest_path, group_filters)) == ()


def test_empty_project_level_iter(tmp_path, mngr):
    """Empty Project Level Iterator."""
    workspace = Workspace.init(tmp_path)
    manifest_path = Path("none.toml")
    group_filters: GroupFilters = []
    assert tuple(ProjectLevelIter(workspace, mngr, manifest_path, group_filters)) == ()


def test_empty_manifest_iter(tmp_path, mngr):
    """Empty Manifest Iterator."""
    workspace = Workspace.init(tmp_path)
    manifest_path = Path("none.toml")
    group_filters: GroupFilters = []
    assert tuple(ManifestIter(workspace, mngr, manifest_path, group_filters)) == ()


def _create_hier(tmp_path, name, levels) -> List[ProjectSpec]:
    project_specs: List[ProjectSpec] = []
    sublevels = levels[1:]
    for idx in range(levels[0]):
        subname = f"{name}-{idx}"
        project_specs.append(ProjectSpec(name=subname))
        if sublevels:
            sub_project_specs = _create_hier(tmp_path, subname, sublevels)
            spec = ManifestSpec(dependencies=sub_project_specs)
        else:
            spec = ManifestSpec()
        with git_repo(tmp_path / f"{subname}", commit="initial", origin=path2url(tmp_path)):
            save(spec, const.MANIFEST_PATH_DEFAULT)
    return project_specs


def create_hier(tmp_path, name, levels):
    """Create Hierarchical Project Structure."""
    spec = ManifestSpec(dependencies=_create_hier(tmp_path, name, levels))
    with git_repo(tmp_path / f"{name}", commit="initial", origin=path2url(tmp_path)):
        save(spec, const.MANIFEST_PATH_DEFAULT)


def test_project_iter(tmp_path, mngr):
    """Test On Project Iterator."""
    workspace = Workspace.init(tmp_path)
    create_hier(tmp_path, "main", [2, 4, 3])
    group_filters: GroupFilters = ()
    manifest_path = tmp_path / "main" / const.MANIFEST_PATH_DEFAULT
    assert tuple(ProjectIter(workspace, mngr, manifest_path, group_filters)) == (
        Project(name="main-0", path="main-0", level=1, url="../main-0"),
        Project(name="main-1", path="main-1", level=1, url="../main-1"),
        Project(name="main-0-0", path="main-0-0", level=2, url="../main-0-0"),
        Project(name="main-0-1", path="main-0-1", level=2, url="../main-0-1"),
        Project(name="main-0-2", path="main-0-2", level=2, url="../main-0-2"),
        Project(name="main-0-3", path="main-0-3", level=2, url="../main-0-3"),
        Project(name="main-1-0", path="main-1-0", level=2, url="../main-1-0"),
        Project(name="main-1-1", path="main-1-1", level=2, url="../main-1-1"),
        Project(name="main-1-2", path="main-1-2", level=2, url="../main-1-2"),
        Project(name="main-1-3", path="main-1-3", level=2, url="../main-1-3"),
        Project(name="main-0-0-0", path="main-0-0-0", level=3, url="../main-0-0-0"),
        Project(name="main-0-0-1", path="main-0-0-1", level=3, url="../main-0-0-1"),
        Project(name="main-0-0-2", path="main-0-0-2", level=3, url="../main-0-0-2"),
        Project(name="main-0-1-0", path="main-0-1-0", level=3, url="../main-0-1-0"),
        Project(name="main-0-1-1", path="main-0-1-1", level=3, url="../main-0-1-1"),
        Project(name="main-0-1-2", path="main-0-1-2", level=3, url="../main-0-1-2"),
        Project(name="main-0-2-0", path="main-0-2-0", level=3, url="../main-0-2-0"),
        Project(name="main-0-2-1", path="main-0-2-1", level=3, url="../main-0-2-1"),
        Project(name="main-0-2-2", path="main-0-2-2", level=3, url="../main-0-2-2"),
        Project(name="main-0-3-0", path="main-0-3-0", level=3, url="../main-0-3-0"),
        Project(name="main-0-3-1", path="main-0-3-1", level=3, url="../main-0-3-1"),
        Project(name="main-0-3-2", path="main-0-3-2", level=3, url="../main-0-3-2"),
        Project(name="main-1-0-0", path="main-1-0-0", level=3, url="../main-1-0-0"),
        Project(name="main-1-0-1", path="main-1-0-1", level=3, url="../main-1-0-1"),
        Project(name="main-1-0-2", path="main-1-0-2", level=3, url="../main-1-0-2"),
        Project(name="main-1-1-0", path="main-1-1-0", level=3, url="../main-1-1-0"),
        Project(name="main-1-1-1", path="main-1-1-1", level=3, url="../main-1-1-1"),
        Project(name="main-1-1-2", path="main-1-1-2", level=3, url="../main-1-1-2"),
        Project(name="main-1-2-0", path="main-1-2-0", level=3, url="../main-1-2-0"),
        Project(name="main-1-2-1", path="main-1-2-1", level=3, url="../main-1-2-1"),
        Project(name="main-1-2-2", path="main-1-2-2", level=3, url="../main-1-2-2"),
        Project(name="main-1-3-0", path="main-1-3-0", level=3, url="../main-1-3-0"),
        Project(name="main-1-3-1", path="main-1-3-1", level=3, url="../main-1-3-1"),
        Project(name="main-1-3-2", path="main-1-3-2", level=3, url="../main-1-3-2"),
    )


def test_project_level_iter(tmp_path, mngr):
    """Test On Project Level Iterator."""
    workspace = Workspace.init(tmp_path)
    create_hier(tmp_path, "main", [2, 4, 3])
    group_filters: GroupFilters = ()
    manifest_path = tmp_path / "main" / const.MANIFEST_PATH_DEFAULT
    assert tuple(ProjectLevelIter(workspace, mngr, manifest_path, group_filters)) == (
        (
            Project(name="main-0", path="main-0", level=1, url="../main-0"),
            Project(name="main-1", path="main-1", level=1, url="../main-1"),
        ),
        (
            Project(name="main-0-0", path="main-0-0", level=2, url="../main-0-0"),
            Project(name="main-0-1", path="main-0-1", level=2, url="../main-0-1"),
            Project(name="main-0-2", path="main-0-2", level=2, url="../main-0-2"),
            Project(name="main-0-3", path="main-0-3", level=2, url="../main-0-3"),
            Project(name="main-1-0", path="main-1-0", level=2, url="../main-1-0"),
            Project(name="main-1-1", path="main-1-1", level=2, url="../main-1-1"),
            Project(name="main-1-2", path="main-1-2", level=2, url="../main-1-2"),
            Project(name="main-1-3", path="main-1-3", level=2, url="../main-1-3"),
        ),
        (
            Project(name="main-0-0-0", path="main-0-0-0", level=3, url="../main-0-0-0"),
            Project(name="main-0-0-1", path="main-0-0-1", level=3, url="../main-0-0-1"),
            Project(name="main-0-0-2", path="main-0-0-2", level=3, url="../main-0-0-2"),
            Project(name="main-0-1-0", path="main-0-1-0", level=3, url="../main-0-1-0"),
            Project(name="main-0-1-1", path="main-0-1-1", level=3, url="../main-0-1-1"),
            Project(name="main-0-1-2", path="main-0-1-2", level=3, url="../main-0-1-2"),
            Project(name="main-0-2-0", path="main-0-2-0", level=3, url="../main-0-2-0"),
            Project(name="main-0-2-1", path="main-0-2-1", level=3, url="../main-0-2-1"),
            Project(name="main-0-2-2", path="main-0-2-2", level=3, url="../main-0-2-2"),
            Project(name="main-0-3-0", path="main-0-3-0", level=3, url="../main-0-3-0"),
            Project(name="main-0-3-1", path="main-0-3-1", level=3, url="../main-0-3-1"),
            Project(name="main-0-3-2", path="main-0-3-2", level=3, url="../main-0-3-2"),
            Project(name="main-1-0-0", path="main-1-0-0", level=3, url="../main-1-0-0"),
            Project(name="main-1-0-1", path="main-1-0-1", level=3, url="../main-1-0-1"),
            Project(name="main-1-0-2", path="main-1-0-2", level=3, url="../main-1-0-2"),
            Project(name="main-1-1-0", path="main-1-1-0", level=3, url="../main-1-1-0"),
            Project(name="main-1-1-1", path="main-1-1-1", level=3, url="../main-1-1-1"),
            Project(name="main-1-1-2", path="main-1-1-2", level=3, url="../main-1-1-2"),
            Project(name="main-1-2-0", path="main-1-2-0", level=3, url="../main-1-2-0"),
            Project(name="main-1-2-1", path="main-1-2-1", level=3, url="../main-1-2-1"),
            Project(name="main-1-2-2", path="main-1-2-2", level=3, url="../main-1-2-2"),
            Project(name="main-1-3-0", path="main-1-3-0", level=3, url="../main-1-3-0"),
            Project(name="main-1-3-1", path="main-1-3-1", level=3, url="../main-1-3-1"),
            Project(name="main-1-3-2", path="main-1-3-2", level=3, url="../main-1-3-2"),
        ),
    )
