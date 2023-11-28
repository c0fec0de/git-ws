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

"""Command Line Interface."""
from pytest import fixture

from gitws import GitWS

from .util import chdir, cli, path2url


@fixture
def gws(tmp_path, repos):
    """Initialize :any:`GitWS` on ``repos``."""
    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos / "main"))
        gws.update()
    with chdir(tmp_path / "main"):
        yield gws


def test_main_path(tmp_path, gws):
    """Main Path."""
    assert cli(["info", "main-path"], tmp_path=tmp_path) == ["TMP/main/main", ""]


def test_base_path(tmp_path, gws):
    """Base Path."""
    assert cli(["info", "base-path"], tmp_path=tmp_path) == ["TMP/main/main", ""]


def test_workspace_path(tmp_path, gws):
    """Workspace Path."""
    assert cli(["info", "workspace-path"], tmp_path=tmp_path) == ["TMP/main", ""]


def test_project_paths(tmp_path, gws):
    """Project Paths."""
    assert cli(["info", "project-paths"], tmp_path=tmp_path) == [
        "TMP/main/main",
        "TMP/main/dep1",
        "TMP/main/dep2",
        "TMP/main/dep4",
        "",
    ]


def test_dep_tree(tmp_path, gws):
    """Dependency Trees."""
    assert cli(["info", "dep-tree"], tmp_path=tmp_path) == [
        "main",
        "├── dep1",
        "│   └── dep4 (revision='main')",
        "├── dep2 (revision='1-feature', submodules=False)",
        "│   ├── dep3 (revision='main', groups='test')",
        "│   └── dep4 (revision='main')*",
        "└── dep3 (groups='test')*",
        "",
    ]


def test_dep_tree_primary(tmp_path, gws):
    """Dependency Trees - Primary Only."""
    assert cli(["info", "dep-tree", "--primary"], tmp_path=tmp_path) == [
        "main",
        "├── dep1",
        "│   └── dep4 (revision='main')",
        "└── dep2 (revision='1-feature', submodules=False)",
        "    └── dep3 (revision='main', groups='test')",
        "",
    ]


def test_dep_tree_dot(tmp_path, gws):
    """Dependency Trees - dot."""
    assert cli(["info", "dep-tree", "--dot"], tmp_path=tmp_path) == [
        "digraph tree {",
        '    "main";',
        '    "dep1";',
        '    "dep4";',
        '    "dep2";',
        '    "dep3";',
        '    "dep4";',
        '    "dep3";',
        '    "main" -> "dep1";',
        '    "main" -> "dep2" [label="1-feature"];',
        '    "main" -> "dep3" [style="dashed";label="(test)"];',
        '    "dep1" -> "dep4" [label="main"];',
        '    "dep2" -> "dep3" [label="main (test)"];',
        '    "dep2" -> "dep4" [style="dashed";label="main"];',
        "}",
        "",
    ]
