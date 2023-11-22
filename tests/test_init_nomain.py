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

"""Initialization Tests without Main Repo."""
from pytest import raises

from gitws import Defaults, GitWS, InitializedError, ManifestSpec, NoAbsUrlError, NoMainError, ProjectSpec, Remote, save
from gitws.const import CONFIG_PATH, INFO_PATH, MANIFEST_PATH_DEFAULT

from .common import MANIFEST_DEFAULT
from .fixtures import create_repos
from .util import chdir, cli


def test_nomain(tmp_path):
    """Init without main."""
    path = tmp_path / "workspace"
    path.mkdir(parents=True)
    with chdir(path):
        GitWS.create_manifest()
        manifest_path = path / "git-ws.toml"
        assert manifest_path.read_text() == MANIFEST_DEFAULT

        gws = GitWS.init(path=path)

        assert gws.path == path
        assert gws.main_path is None
        assert gws.base_path == path
        info_file = gws.path / INFO_PATH
        assert info_file.read_text().split("\n") == [
            "# Git Workspace System File. DO NOT EDIT.",
            "",
            "",
        ]
        config_file = gws.path / CONFIG_PATH
        assert config_file.read_text().split("\n") == [
            'manifest_path = "git-ws.toml"',
            "",
        ]

        assert cli(["info", "base-path"], tmp_path=tmp_path) == ["TMP/workspace", ""]

        with raises(InitializedError):
            GitWS.init(path=path)

        rrepo = GitWS.from_path()
        assert rrepo.path == path
        assert gws.workspace == rrepo.workspace
        assert gws.manifest_path == rrepo.manifest_path
        assert gws.group_filters == rrepo.group_filters
        assert gws == rrepo

        # re-init
        arepo = GitWS.init(path=path, force=True, group_filters=("+test", "-doc"))
        assert arepo.path == path
        assert gws.workspace == arepo.workspace
        assert gws.manifest_path == arepo.manifest_path
        assert arepo.group_filters == ("+test", "-doc")


def test_noabs(tmp_path):
    """Test Without absolute paths"""
    path = tmp_path / "workspace"
    path.mkdir(parents=True)
    with chdir(path):
        dependencies = [
            ProjectSpec(name="dep1"),
        ]
        manifest_spec = ManifestSpec(dependencies=dependencies)
        save(manifest_spec, MANIFEST_PATH_DEFAULT)

        gws = GitWS.init(path=path)
        with raises(NoAbsUrlError):
            gws.update()


def test_deps(tmp_path):
    """Pulling of dependencies."""
    path = tmp_path / "workspace"
    path.mkdir(parents=True)
    repos = tmp_path / "repos"
    create_repos(repos)
    with chdir(path):
        manifest_spec = ManifestSpec(
            defaults=Defaults(revision="main"),
            remotes=[
                Remote(name="main", url_base=f"file://{repos!s}"),
            ],
            dependencies=[
                ProjectSpec(name="dep1", sub_url="dep1", remote="main"),
            ],
        )
        save(manifest_spec, MANIFEST_PATH_DEFAULT)
        gws = GitWS.init(path=path)
        gws.update()
        assert (path / "dep1").exists()
        assert not (path / "dep2").exists()
        assert not (path / "dep3").exists()
        assert (path / "dep4").exists()

        with raises(NoMainError):
            gws.tag("mytag")
