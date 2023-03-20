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
from .fixtures import repos, repos_dotgit
from .util import chdir, cli, get_sha


@fixture
def gws(tmp_path, repos):
    """Initialized :any:`GitWS` on ``repos``."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos / "main"))
        gws.update()

    with chdir(workspace):
        yield gws


@fixture
def gws_dotgit(tmp_path, repos_dotgit):
    """Initialized :any:`GitWS` on ``repos_dotgit``."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos_dotgit / "main.git"))
        gws.update()

    with chdir(workspace):
        yield gws


def test_validate(tmp_path, gws):
    """Manifest Validate."""
    # pylint: disable=unused-argument

    assert cli(["manifest", "validate"]) == [""]

    manifest_path = tmp_path / "main" / "main" / "git-ws.toml"
    assert manifest_path.write_text(
        "\n".join(
            [
                "[[dependencies]]",
                'nam = "dep1"',
                "",
                "[[dependencies]]",
                'name = "dep2"',
                'url = "../dep2"',
                'revision = "1-feature"',
                "",
            ]
        )
    )
    assert cli(["manifest", "validate"], exit_code=1) == [
        "Error: Manifest 'main/git-ws.toml' is broken: 1 validation error for ManifestSpec",
        "dependencies -> 0 -> name",
        "  field required (type=value_error.missing)",
        "",
    ]


def test_freeze(tmp_path, gws, repos):
    """Manifest Freeze."""
    sha1 = get_sha(gws.path / "dep1")
    sha1s = sha1[:7]
    sha2 = get_sha(gws.path / "dep2")
    sha2s = sha2[:7]
    sha4 = get_sha(gws.path / "dep4")
    sha4s = sha4[:7]
    default = [
        'version = "1.0"',
        "##",
        "## Git Workspace's Manifest. Please see the documentation at:",
        "##",
        "## https://git-ws.readthedocs.io/en/latest/manual/manifest.html",
        "##",
        "",
        "",
        '# group-filters = ["+test", "-doc", "+feature@path"]',
        'group-filters = ["-test"]',
        "",
        "",
        "# [[linkfiles]]",
        '# src = "file-in-main-clone.txt"',
        '# dest = "link-in-workspace.txt"',
        "",
        "",
        "# [[copyfiles]]",
        '# src = "file-in-main-clone.txt"',
        '# dest = "file-in-workspace.txt"',
        "",
        "",
        "# [[remotes]]",
        '# name = "myremote"',
        '# url-base = "https://github.com/myuser"',
        "",
        "",
        "[defaults]",
        "",
        '# remote = "myserver"',
        '# revision = "main"',
        '# groups = ["+test"]',
        '# with_groups = ["doc"]',
        "",
        "",
        "## A full flavored dependency using a 'remote':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# remote = "remote"',
        '# sub-url = "my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "link0-in-workspace.txt"',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "link1-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "file0-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "file1-in-workspace.txt"',
        "",
        "## A full flavored dependency using a 'url':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# url = "https://github.com/myuser/my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "link0-in-workspace.txt"',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "link1-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "file0-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "file1-in-workspace.txt"',
        "",
        "## A minimal dependency:",
        "# [[dependencies]]",
        '# name = "my"',
        "[[dependencies]]",
        'name = "dep1"',
        'url = "../dep1"',
        f'revision = "{sha1}"',
        'path = "dep1"',
        "submodules = true",
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "../dep2"',
        f'revision = "{sha2}"',
        'path = "dep2"',
        "submodules = false",
        "",
        "[[dependencies]]",
        'name = "dep4"',
        'url = "../dep4"',
        f'revision = "{sha4}"',
        'path = "dep4"',
        "submodules = true",
        "",
    ]
    assert cli(["foreach", "git", "config", "advice.detachedHead", "false"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]

    # STDOUT
    assert cli(["manifest", "freeze", "-G", "+test"], exit_code=1) == [
        "Error: Git Clone 'dep3' is missing. Try:",
        "",
        "    git ws update",
        "",
        "",
    ]

    assert cli(["update", "-G", "+test"], tmp_path=tmp_path, repos_path=repos) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "Pulling branch 'main'.",
        "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
        "Pulling branch '1-feature'.",
        "===== dep3 ('dep3', groups='test') =====",
        "git-ws WARNING Clone dep3 (groups='test') has no revision!",
        "Cloning 'REPOS/dep3'.",
        "===== dep4 ('dep4', revision='main') =====",
        "Pulling branch 'main'.",
        "",
    ]
    sha3 = get_sha(gws.path / "dep3")
    withtest = [
        'version = "1.0"',
        "##",
        "## Git Workspace's Manifest. Please see the documentation at:",
        "##",
        "## https://git-ws.readthedocs.io/en/latest/manual/manifest.html",
        "##",
        "",
        "",
        '# group-filters = ["+test", "-doc", "+feature@path"]',
        'group-filters = ["-test"]',
        "",
        "",
        "# [[linkfiles]]",
        '# src = "file-in-main-clone.txt"',
        '# dest = "link-in-workspace.txt"',
        "",
        "",
        "# [[copyfiles]]",
        '# src = "file-in-main-clone.txt"',
        '# dest = "file-in-workspace.txt"',
        "",
        "",
        "# [[remotes]]",
        '# name = "myremote"',
        '# url-base = "https://github.com/myuser"',
        "",
        "",
        "[defaults]",
        "",
        '# remote = "myserver"',
        '# revision = "main"',
        '# groups = ["+test"]',
        '# with_groups = ["doc"]',
        "",
        "",
        "## A full flavored dependency using a 'remote':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# remote = "remote"',
        '# sub-url = "my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "link0-in-workspace.txt"',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "link1-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "file0-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "file1-in-workspace.txt"',
        "",
        "## A full flavored dependency using a 'url':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# url = "https://github.com/myuser/my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "link0-in-workspace.txt"',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "link1-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "file0-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "file1-in-workspace.txt"',
        "",
        "## A minimal dependency:",
        "# [[dependencies]]",
        '# name = "my"',
        "[[dependencies]]",
        'name = "dep1"',
        'url = "../dep1"',
        f'revision = "{sha1}"',
        'path = "dep1"',
        "submodules = true",
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "../dep2"',
        f'revision = "{sha2}"',
        'path = "dep2"',
        "submodules = false",
        "",
        "[[dependencies]]",
        'name = "dep3"',
        'url = "../dep3"',
        f'revision = "{sha3}"',
        'path = "dep3"',
        'groups = ["test"]',
        "submodules = true",
        "",
        "[[dependencies]]",
        'name = "dep4"',
        'url = "../dep4"',
        f'revision = "{sha4}"',
        'path = "dep4"',
        "submodules = true",
        "",
        "",
    ]
    assert cli(["manifest", "freeze", "-G", "+test"]) == withtest

    # FILE
    output_path = tmp_path / "manifest.toml"
    assert cli(["manifest", "freeze", "--output", str(output_path)]) == [
        "",
    ]

    assert output_path.read_text().split("\n") == default

    assert cli(["update", "--manifest", str(output_path)]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Pulling branch 'main'.",
        f"===== dep1 ('dep1', revision={sha1!r}) =====",
        "Fetching.",
        f"HEAD is now at {sha1s} initial",
        f"===== dep2 ('dep2', revision={sha2!r}, submodules=False) =====",
        "Fetching.",
        f"HEAD is now at {sha2s} feature",
        f"===== dep4 ('dep4', revision={sha4!r}) =====",
        "Fetching.",
        f"HEAD is now at {sha4s} initial",
        "",
    ]

    # STDOUT again
    assert cli(["manifest", "freeze"]) == default + [""]

    assert cli(["update", "--manifest", str(output_path)]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Pulling branch 'main'.",
        f"===== dep1 ('dep1', revision={sha1!r}) =====",
        "Nothing to do.",
        f"===== dep2 ('dep2', revision={sha2!r}, submodules=False) =====",
        "Nothing to do.",
        f"===== dep4 ('dep4', revision={sha4!r}) =====",
        "Nothing to do.",
        "",
    ]


def test_resolve(tmp_path, gws):
    """Manifest Resolve."""
    # pylint: disable=unused-argument

    lines = [
        'version = "1.0"',
        "##",
        "## Git Workspace's Manifest. Please see the documentation at:",
        "##",
        "## https://git-ws.readthedocs.io/en/latest/manual/manifest.html",
        "##",
        "",
        "",
        '# group-filters = ["+test", "-doc", "+feature@path"]',
        'group-filters = ["-test"]',
        "",
        "",
        "# [[linkfiles]]",
        '# src = "file-in-main-clone.txt"',
        '# dest = "link-in-workspace.txt"',
        "",
        "",
        "# [[copyfiles]]",
        '# src = "file-in-main-clone.txt"',
        '# dest = "file-in-workspace.txt"',
        "",
        "",
        "# [[remotes]]",
        '# name = "myremote"',
        '# url-base = "https://github.com/myuser"',
        "",
        "",
        "[defaults]",
        "",
        '# remote = "myserver"',
        '# revision = "main"',
        '# groups = ["+test"]',
        '# with_groups = ["doc"]',
        "",
        "",
        "## A full flavored dependency using a 'remote':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# remote = "remote"',
        '# sub-url = "my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "link0-in-workspace.txt"',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "link1-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "file0-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "file1-in-workspace.txt"',
        "",
        "## A full flavored dependency using a 'url':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# url = "https://github.com/myuser/my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "link0-in-workspace.txt"',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "link1-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "file0-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "file1-in-workspace.txt"',
        "",
        "## A minimal dependency:",
        "# [[dependencies]]",
        '# name = "my"',
        "[[dependencies]]",
        'name = "dep1"',
        'url = "../dep1"',
        'path = "dep1"',
        "submodules = true",
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "../dep2"',
        'revision = "1-feature"',
        'path = "dep2"',
        "submodules = false",
        "",
        "[[dependencies]]",
        'name = "dep4"',
        'url = "../dep4"',
        'revision = "main"',
        'path = "dep4"',
        "submodules = true",
        "",
    ]

    # STDOUT
    assert cli(["manifest", "resolve"]) == lines + [""]

    # FILE
    output_path = tmp_path / "manifest.toml"
    assert cli(["manifest", "resolve", "--output", str(output_path)]) == [
        "",
    ]
    assert output_path.read_text().split("\n") == lines


def test_path(tmp_path, gws):
    """Manifest Path."""
    # pylint: disable=unused-argument
    assert cli(["manifest", "path"], tmp_path=tmp_path) == ["TMP/main/main/git-ws.toml", ""]


def test_paths(tmp_path, gws):
    """Manifest Paths."""
    # pylint: disable=unused-argument
    assert cli(["manifest", "paths"], tmp_path=tmp_path) == [
        "TMP/main/main/git-ws.toml",
        "TMP/main/dep1/git-ws.toml",
        "TMP/main/dep2/git-ws.toml",
        "",
    ]


def test_upgrade(tmp_path):
    """Test Manifest Upgrade."""
    manifest_path = tmp_path / "my.toml"
    manifest_path.write_text(
        """
version = "0.9"
[defaults]
remote = "myremote"
"""
    )
    assert cli(["manifest", "upgrade", "-M", str(manifest_path)]) == [
        f"Manifest '{manifest_path!s}' upgraded.",
        "",
    ]
    assert (
        manifest_path.read_text()
        == """version = "1.0"
##
## Git Workspace's Manifest. Please see the documentation at:
##
## https://git-ws.readthedocs.io/en/latest/manual/manifest.html
##


# group-filters = ["+test", "-doc", "+feature@path"]
group-filters = []


# [[linkfiles]]
# src = "file-in-main-clone.txt"
# dest = "link-in-workspace.txt"


# [[copyfiles]]
# src = "file-in-main-clone.txt"
# dest = "file-in-workspace.txt"


# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"


[defaults]
remote = "myremote"

# remote = "myserver"
# revision = "main"
# groups = ["+test"]
# with_groups = ["doc"]


## A full flavored dependency using a 'remote':
# [[dependencies]]
# name = "myname"
# remote = "remote"
# sub-url = "my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]
#
# [[dependencies.linkfiles]]
# src = "file0-in-mydir.txt"
# dest = "link0-in-workspace.txt"
#
# [[dependencies.linkfiles]]
# src = "file1-in-mydir.txt"
# dest = "link1-in-workspace.txt"
#
# [[dependencies.copyfiles]]
# src = "file0-in-mydir.txt"
# dest = "file0-in-workspace.txt"
#
# [[dependencies.copyfiles]]
# src = "file1-in-mydir.txt"
# dest = "file1-in-workspace.txt"

## A full flavored dependency using a 'url':
# [[dependencies]]
# name = "myname"
# url = "https://github.com/myuser/my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]
#
# [[dependencies.linkfiles]]
# src = "file0-in-mydir.txt"
# dest = "link0-in-workspace.txt"
#
# [[dependencies.linkfiles]]
# src = "file1-in-mydir.txt"
# dest = "link1-in-workspace.txt"
#
# [[dependencies.copyfiles]]
# src = "file0-in-mydir.txt"
# dest = "file0-in-workspace.txt"
#
# [[dependencies.copyfiles]]
# src = "file1-in-mydir.txt"
# dest = "file1-in-workspace.txt"

## A minimal dependency:
# [[dependencies]]
# name = "my"
"""
    )


def test_upgrade_fail(tmp_path):
    """Test Manifest Upgrade."""
    manifest_path = tmp_path / "my.toml"
    with chdir(tmp_path):
        manifest_path.write_text(
            """
    [[entry]
    name = "my entry"
     """
        )
        assert cli(["manifest", "upgrade", "-M", str(manifest_path)], exit_code=1) == [
            "Error: Manifest 'my.toml' is broken: Unexpected character: 'n' at line 3 col 4",
            "",
        ]


def test_freeze_dotgit(tmp_path, gws_dotgit):
    """Manifest Freeze with .git."""
    sha1 = get_sha(gws_dotgit.path / "dep1")
    sha1s = sha1[:7]
    sha2 = get_sha(gws_dotgit.path / "dep2")
    sha2s = sha2[:7]
    sha3 = get_sha(gws_dotgit.path / "dep3")
    sha3s = sha3[:7]
    sha4 = get_sha(gws_dotgit.path / "dep4")
    sha4s = sha4[:7]
    manifest = [
        'version = "1.0"',
        "##",
        "## Git Workspace's Manifest. Please see the documentation at:",
        "##",
        "## https://git-ws.readthedocs.io/en/latest/manual/manifest.html",
        "##",
        "",
        "",
        '# group-filters = ["+test", "-doc", "+feature@path"]',
        "group-filters = []",
        "",
        "",
        "# [[linkfiles]]",
        '# src = "file-in-main-clone.txt"',
        '# dest = "link-in-workspace.txt"',
        "",
        "",
        "# [[copyfiles]]",
        '# src = "file-in-main-clone.txt"',
        '# dest = "file-in-workspace.txt"',
        "",
        "",
        "# [[remotes]]",
        '# name = "myremote"',
        '# url-base = "https://github.com/myuser"',
        "",
        "",
        "[defaults]",
        "",
        '# remote = "myserver"',
        '# revision = "main"',
        '# groups = ["+test"]',
        '# with_groups = ["doc"]',
        "",
        "",
        "## A full flavored dependency using a 'remote':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# remote = "remote"',
        '# sub-url = "my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "link0-in-workspace.txt"',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "link1-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "file0-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "file1-in-workspace.txt"',
        "",
        "## A full flavored dependency using a 'url':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# url = "https://github.com/myuser/my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "link0-in-workspace.txt"',
        "#",
        "# [[dependencies.linkfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "link1-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file0-in-mydir.txt"',
        '# dest = "file0-in-workspace.txt"',
        "#",
        "# [[dependencies.copyfiles]]",
        '# src = "file1-in-mydir.txt"',
        '# dest = "file1-in-workspace.txt"',
        "",
        "## A minimal dependency:",
        "# [[dependencies]]",
        '# name = "my"',
        "[[dependencies]]",
        'name = "dep1"',
        'url = "../dep1.git"',
        f'revision = "{sha1}"',
        'path = "dep1"',
        "submodules = true",
        "",
        "[[dependencies]]",
        'name = "dep3"',
        'url = "../dep3"',
        f'revision = "{sha3}"',
        'path = "dep3"',
        "submodules = true",
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "../dep2.git"',
        f'revision = "{sha2}"',
        'path = "dep2"',
        "submodules = true",
        "",
        "[[dependencies]]",
        'name = "dep4"',
        'url = "../dep4"',
        f'revision = "{sha4}"',
        'path = "dep4"',
        "submodules = true",
        "",
    ]

    assert cli(["foreach", "git", "config", "advice.detachedHead", "false"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1', revision='main') =====",
        "===== dep3 ('dep3', revision='main') =====",
        "===== dep2 ('dep2', revision='main') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]

    # FILE
    output_path = tmp_path / "manifest.toml"
    assert cli(["manifest", "freeze", "--output", str(output_path)]) == [
        "",
    ]

    assert output_path.read_text().split("\n") == manifest

    assert cli(["update", "--manifest", str(output_path)]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Pulling branch 'main'.",
        f"===== dep1 ('dep1', revision='{sha1}') " "=====",
        "Fetching.",
        f"HEAD is now at {sha1s} initial",
        f"===== dep3 ('dep3', revision='{sha3}') " "=====",
        "Fetching.",
        f"HEAD is now at {sha3s} initial",
        f"===== dep2 ('dep2', revision='{sha2}') " "=====",
        "Fetching.",
        f"HEAD is now at {sha2s} initial",
        f"===== dep4 ('dep4', revision='{sha4}') " "=====",
        "Fetching.",
        f"HEAD is now at {sha4s} initial",
        "",
    ]
