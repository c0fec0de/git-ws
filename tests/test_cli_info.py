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

"""Command Line Interface."""
from pytest import fixture

from gitws import GitWS

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`GitWS` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = GitWS.clone(str(repos / "main"))
        arepo.update()

        yield arepo


def test_main_path(tmp_path, arepo):
    """Main Path."""
    # pylint: disable=unused-argument
    assert cli(["info", "main-path"], tmp_path=tmp_path) == ["TMP/workspace/main", ""]


def test_workspace_path(tmp_path, arepo):
    """Workspace Path."""
    # pylint: disable=unused-argument
    assert cli(["info", "workspace-path"], tmp_path=tmp_path) == ["TMP/workspace", ""]


def test_project_paths(tmp_path, arepo):
    """Project Paths."""
    # pylint: disable=unused-argument
    assert cli(["info", "project-paths"], tmp_path=tmp_path) == [
        "TMP/workspace/main",
        "TMP/workspace/dep1",
        "TMP/workspace/dep2",
        "TMP/workspace/dep4",
        "",
    ]


def test_dep_tree(tmp_path, arepo):
    """Dependency Trees."""
    # pylint: disable=unused-argument
    assert cli(["info", "dep-tree"], tmp_path=tmp_path) == [
        "main",
        "├── dep1 [PRIMARY]",
        "│   └── dep4 (revision='main') [PRIMARY]",
        "└── dep2 (revision='1-feature') [PRIMARY]",
        "    ├── dep3 (revision='main', groups='test') [PRIMARY]",
        "    └── dep4 (revision='main')",
        "",
    ]


def test_dep_tree_dot(tmp_path, arepo):
    """Dependency Trees - dot."""
    # pylint: disable=unused-argument
    assert cli(["info", "dep-tree", "--dot"], tmp_path=tmp_path) == [
        "digraph tree {",
        '    "main";',
        '    "dep1";',
        '    "dep4";',
        '    "dep2";',
        '    "dep3";',
        '    "dep4";',
        '    "main" -> "dep1";',
        '    "main" -> "dep2" [label="1-feature"];',
        '    "dep1" -> "dep4" [label="main"];',
        '    "dep2" -> "dep3" [label="main (test)"];',
        '    "dep2" -> "dep4" [style="dashed";label="main"];',
        "}",
        "",
    ]
