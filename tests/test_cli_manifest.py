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
from .util import chdir, cli, get_sha


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`GitWS` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = GitWS.clone(str(repos / "main"))
        arepo.update()

        yield arepo


def test_validate(tmp_path, arepo):
    """Manifest Validate."""
    # pylint: disable=unused-argument

    assert cli(["manifest", "validate"]) == [""]

    manifest_path = tmp_path / "workspace" / "main" / "git-ws.toml"
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


def test_freeze(tmp_path, arepo):
    """Manifest Freeze."""
    sha1 = get_sha(arepo.path / "dep1")
    sha2 = get_sha(arepo.path / "dep2")
    sha4 = get_sha(arepo.path / "dep4")
    lines = [
        'version = "1.0"',
        "##",
        "## Welcome to Git Workspace's Manifest. It actually contains 4 parts:",
        "##",
        "## * Remotes",
        "## * Groups",
        "## * Defaults",
        "## * Dependencies",
        "##",
        "## =========",
        "##  Remotes",
        "## =========",
        "##",
        "## Remotes just refer to a directory with repositories.",
        "##",
        "## We support relative paths for dependencies. So, if your dependencies are next",
        "## to your repository, you might NOT need any remote.",
        "## In other terms: You only need remotes if your dependencies are located on",
        "## OTHER servers than your server with this manifest.",
        "##",
        "## Remotes have two attributes:",
        "## * name: Required. String.",
        "##         Name of the remote. Any valid string. Must be unique within your",
        "##         manifest.",
        "## * url-base: Required. String.",
        "##             URL Prefix. The project 'name' or 'sub-url' will be appended",
        "##             later-on.",
        "##",
        "# [[remotes]]",
        '# name = "myremote"',
        '# url-base = "https://github.com/myuser"',
        "",
        "",
        "## =========",
        "##  Groups",
        "## =========",
        "##",
        "## Groups structure dependencies.",
        "##",
        "## Groups are optional by default.",
        "## If a dependency belongs to a group, it becomes optional likewise.",
        "## Groups can be later on selected/deselected by '+group' or '-group'.",
        "## An optional group can be selected by '+group',",
        "## a non-optional group can be deselected by '-group'.",
        "## Deselection has higher priority than selection.",
        "##",
        "## Dependencies can refer to non-existing groups. You do NOT need to specify",
        "## all used groups.",
        "##",
        "## Groups have two attributes:",
        "## * name: Required. String.",
        "##         Name of the group. Any valid string. Must be unique within your",
        "##         manifest.",
        "## * optional: Optional. Bool. Default is True.",
        "##             Specifies if the group is optional. Meaning it must be selected",
        "##             explicitly. Otherwise the dependency is not added by default.",
        "##",
        "## The following lines set a group as non-optional.",
        "# [[groups]]",
        '# name = "test"',
        "# optional = false",
        "",
        "",
        "## ==========",
        "##  Defaults",
        "## ==========",
        "##",
        "## The 'defaults' section specifies default values for dependencies.",
        "##",
        "## * remote: Optional. String.",
        "##           Remote used as default.",
        "##           The 'remote' MUST be defined in the 'remotes' section above!",
        "## * revision: Optional. String.",
        "##             Revision used as default. Tag or Branch.",
        "##",
        "## NOTE: It is recommended to specify a default revision (i.e. 'main').",
        "##       If a dependency misses 'revision', GitWS will not take care about",
        "##       revision handling. This may lead to strange side-effects. You",
        "##       have been warned.",
        "",
        "[defaults]",
        '# remote = "myserver"',
        '# revision = "main"',
        "",
        "",
        "## ==============",
        "##  Dependencies",
        "## ==============",
        "##",
        "## The 'dependencies' section specifies all your git clones you need for your",
        "## project to operate.",
        "##",
        "## A dependency has the following attributes:",
        "## * name: Required. String.",
        "##         Just name your dependency. It is recommended to choose a",
        "##         unique name, but not a must.",
        "## * remote: Optional. String. Restricted (see RESTRICTIONS below).",
        "##           Remote Alias.",
        "##           The 'remote' MUST be defined in the 'remotes' section above!",
        "##           The 'remote' can also be specified in the 'defaults' section.",
        "## * sub-url: Optional. String. Default: '../{name}[.git]' (see NOTE1 below).",
        "##            Relative URL to 'url-base' of your specified 'remote'",
        "##            OR",
        "##            Relative URL to the URL of the repository containing this",
        "##            manifest.",
        "## * url: Optional. String. Restricted (see RESTRICTIONS below).",
        "##        Absolute URL to the dependent repository.",
        "## * revision: Optional. String.",
        "##             Revision to be checked out.",
        "##             If this attribute is left blank, GitWS does NOT manage the",
        "##             dependency revision (see NOTE2 below)!",
        "##             The 'revision' can also be specified in the 'defaults' section.",
        "## * path: Optional. String. Default is '{name}'.",
        "##         Project Filesystem Path. Relative to Workspace Root Directory.",
        "##         The dependency 'name' is used as default for 'path'.",
        "##         The 'path' MUST be unique within your manifest.",
        "## * manifest_path: Optional. String. Default: 'git-ws.toml'.",
        "##                   Path to manifest.",
        "##                   Relative to 'path'.",
        "##                   Avoid changing it! It is just additional effort.",
        "## * groups: Optional. List of Strings.",
        "##           Dependency Groups.",
        "##           Dependencies can be categorized into groups.",
        "##           Groups are optional by default. See 'groups' section above.",
        "##",
        "## NOTE1: 'sub-url' is '../{name}[.git]' by default. Meaning if the dependency",
        "##        is next to your repository containing this manifest, the dependency",
        "##        is automatically found.",
        "##        The '.git' suffix is appended if the repository containing this",
        "##        manifest uses a '.git' suffix.",
        "##",
        "## NOTE2: It is recommended to specify a revision (i.e. 'main') either",
        "##        explicitly or via the 'default' section.",
        "##        Without a 'revision' GitWS will not take care about revision",
        "##        handling. This may lead to strange side-effects.",
        "##        You have been warned.",
        "##",
        "## RESTRICTIONS:",
        "##",
        "## * `remote` and `url` are mutually exclusive.",
        "## * `url` and `sub-url` are likewise mutually exclusive",
        "## * `sub-url` requires a `remote`.",
        "##",
        "##",
        "## A full flavored dependency using a 'remote':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# remote = "remote"',
        '# sub-url = "my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "",
        "## A full flavored dependency using a 'url':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# url = "https://github.com/myuser/my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "",
        "## A minimal dependency:",
        "# [[dependencies]]",
        '# name = "my"',
        "[[dependencies]]",
        'name = "dep1"',
        'url = "../dep1"',
        f'revision = "{sha1}"',
        'path = "dep1"',
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "../dep2"',
        f'revision = "{sha2}"',
        'path = "dep2"',
        "",
        "[[dependencies]]",
        'name = "dep4"',
        'url = "../dep4"',
        f'revision = "{sha4}"',
        'path = "dep4"',
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

    assert cli(["update", "-G", "+test"], tmp_path=tmp_path) == [
        "Groups: '+test'",
        "===== main =====",
        "Pulling branch 'main'.",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep3 (revision='main', groups='test') =====",
        "Cloning 'TMP/repos/dep3'.",
        "",
    ]
    assert cli(["manifest", "freeze", "-G", "+test"]) == lines + [
        "[[dependencies]]",
        'name = "dep3"',
        'url = "../dep3"',
        'revision = "v1.0"',
        'path = "dep3"',
        'groups = ["test"]',
        "",
        "",
    ]

    # FILE
    output_path = tmp_path / "manifest.toml"
    assert cli(["manifest", "freeze", "--output", str(output_path)]) == [
        "",
    ]

    assert output_path.read_text().split("\n") == lines

    assert cli(["update", "--manifest", str(output_path)]) == [
        "===== main =====",
        "Pulling branch 'main'.",
        f"===== dep1 (revision={sha1!r}) =====",
        "Fetching.",
        f"Checking out {sha1!r} (previously 'main').",
        f"===== dep2 (revision={sha2!r}) =====",
        "Fetching.",
        f"Checking out {sha2!r} (previously '1-feature').",
        f"===== dep4 (revision={sha4!r}) =====",
        "Fetching.",
        f"Checking out {sha4!r} (previously 'main').",
        "",
    ]

    # STDOUT again
    assert cli(["manifest", "freeze"]) == lines + [""]

    assert cli(["update", "--manifest", str(output_path)]) == [
        "===== main =====",
        "Pulling branch 'main'.",
        f"===== dep1 (revision={sha1!r}) =====",
        "Nothing to do.",
        f"===== dep2 (revision={sha2!r}) =====",
        "Nothing to do.",
        f"===== dep4 (revision={sha4!r}) =====",
        "Nothing to do.",
        "",
    ]


def test_resolve(tmp_path, arepo):
    """Manifest Resolve."""
    # pylint: disable=unused-argument

    lines = [
        'version = "1.0"',
        "##",
        "## Welcome to Git Workspace's Manifest. It actually contains 4 parts:",
        "##",
        "## * Remotes",
        "## * Groups",
        "## * Defaults",
        "## * Dependencies",
        "##",
        "## =========",
        "##  Remotes",
        "## =========",
        "##",
        "## Remotes just refer to a directory with repositories.",
        "##",
        "## We support relative paths for dependencies. So, if your dependencies are next",
        "## to your repository, you might NOT need any remote.",
        "## In other terms: You only need remotes if your dependencies are located on",
        "## OTHER servers than your server with this manifest.",
        "##",
        "## Remotes have two attributes:",
        "## * name: Required. String.",
        "##         Name of the remote. Any valid string. Must be unique within your",
        "##         manifest.",
        "## * url-base: Required. String.",
        "##             URL Prefix. The project 'name' or 'sub-url' will be appended",
        "##             later-on.",
        "##",
        "# [[remotes]]",
        '# name = "myremote"',
        '# url-base = "https://github.com/myuser"',
        "",
        "",
        "## =========",
        "##  Groups",
        "## =========",
        "##",
        "## Groups structure dependencies.",
        "##",
        "## Groups are optional by default.",
        "## If a dependency belongs to a group, it becomes optional likewise.",
        "## Groups can be later on selected/deselected by '+group' or '-group'.",
        "## An optional group can be selected by '+group',",
        "## a non-optional group can be deselected by '-group'.",
        "## Deselection has higher priority than selection.",
        "##",
        "## Dependencies can refer to non-existing groups. You do NOT need to specify",
        "## all used groups.",
        "##",
        "## Groups have two attributes:",
        "## * name: Required. String.",
        "##         Name of the group. Any valid string. Must be unique within your",
        "##         manifest.",
        "## * optional: Optional. Bool. Default is True.",
        "##             Specifies if the group is optional. Meaning it must be selected",
        "##             explicitly. Otherwise the dependency is not added by default.",
        "##",
        "## The following lines set a group as non-optional.",
        "# [[groups]]",
        '# name = "test"',
        "# optional = false",
        "",
        "",
        "## ==========",
        "##  Defaults",
        "## ==========",
        "##",
        "## The 'defaults' section specifies default values for dependencies.",
        "##",
        "## * remote: Optional. String.",
        "##           Remote used as default.",
        "##           The 'remote' MUST be defined in the 'remotes' section above!",
        "## * revision: Optional. String.",
        "##             Revision used as default. Tag or Branch.",
        "##",
        "## NOTE: It is recommended to specify a default revision (i.e. 'main').",
        "##       If a dependency misses 'revision', GitWS will not take care about",
        "##       revision handling. This may lead to strange side-effects. You",
        "##       have been warned.",
        "",
        "[defaults]",
        '# remote = "myserver"',
        '# revision = "main"',
        "",
        "",
        "## ==============",
        "##  Dependencies",
        "## ==============",
        "##",
        "## The 'dependencies' section specifies all your git clones you need for your",
        "## project to operate.",
        "##",
        "## A dependency has the following attributes:",
        "## * name: Required. String.",
        "##         Just name your dependency. It is recommended to choose a",
        "##         unique name, but not a must.",
        "## * remote: Optional. String. Restricted (see RESTRICTIONS below).",
        "##           Remote Alias.",
        "##           The 'remote' MUST be defined in the 'remotes' section above!",
        "##           The 'remote' can also be specified in the 'defaults' section.",
        "## * sub-url: Optional. String. Default: '../{name}[.git]' (see NOTE1 below).",
        "##            Relative URL to 'url-base' of your specified 'remote'",
        "##            OR",
        "##            Relative URL to the URL of the repository containing this",
        "##            manifest.",
        "## * url: Optional. String. Restricted (see RESTRICTIONS below).",
        "##        Absolute URL to the dependent repository.",
        "## * revision: Optional. String.",
        "##             Revision to be checked out.",
        "##             If this attribute is left blank, GitWS does NOT manage the",
        "##             dependency revision (see NOTE2 below)!",
        "##             The 'revision' can also be specified in the 'defaults' section.",
        "## * path: Optional. String. Default is '{name}'.",
        "##         Project Filesystem Path. Relative to Workspace Root Directory.",
        "##         The dependency 'name' is used as default for 'path'.",
        "##         The 'path' MUST be unique within your manifest.",
        "## * manifest_path: Optional. String. Default: 'git-ws.toml'.",
        "##                   Path to manifest.",
        "##                   Relative to 'path'.",
        "##                   Avoid changing it! It is just additional effort.",
        "## * groups: Optional. List of Strings.",
        "##           Dependency Groups.",
        "##           Dependencies can be categorized into groups.",
        "##           Groups are optional by default. See 'groups' section above.",
        "##",
        "## NOTE1: 'sub-url' is '../{name}[.git]' by default. Meaning if the dependency",
        "##        is next to your repository containing this manifest, the dependency",
        "##        is automatically found.",
        "##        The '.git' suffix is appended if the repository containing this",
        "##        manifest uses a '.git' suffix.",
        "##",
        "## NOTE2: It is recommended to specify a revision (i.e. 'main') either",
        "##        explicitly or via the 'default' section.",
        "##        Without a 'revision' GitWS will not take care about revision",
        "##        handling. This may lead to strange side-effects.",
        "##        You have been warned.",
        "##",
        "## RESTRICTIONS:",
        "##",
        "## * `remote` and `url` are mutually exclusive.",
        "## * `url` and `sub-url` are likewise mutually exclusive",
        "## * `sub-url` requires a `remote`.",
        "##",
        "##",
        "## A full flavored dependency using a 'remote':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# remote = "remote"',
        '# sub-url = "my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "",
        "## A full flavored dependency using a 'url':",
        "# [[dependencies]]",
        '# name = "myname"',
        '# url = "https://github.com/myuser/my.git"',
        '# revision = "main"',
        '# path = "mydir"',
        '# groups = ["group"]',
        "",
        "## A minimal dependency:",
        "# [[dependencies]]",
        '# name = "my"',
        "[[dependencies]]",
        'name = "dep1"',
        'url = "../dep1"',
        'path = "dep1"',
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "../dep2"',
        'revision = "1-feature"',
        'path = "dep2"',
        "",
        "[[dependencies]]",
        'name = "dep4"',
        'url = "../dep4"',
        'revision = "main"',
        'path = "dep4"',
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


def test_path(tmp_path, arepo):
    """Manifest Path."""
    # pylint: disable=unused-argument
    assert cli(["manifest", "path"], tmp_path=tmp_path) == ["TMP/workspace/main/git-ws.toml", ""]


def test_paths(tmp_path, arepo):
    """Manifest Paths."""
    # pylint: disable=unused-argument
    assert cli(["manifest", "paths"], tmp_path=tmp_path) == [
        "TMP/workspace/main/git-ws.toml",
        "TMP/workspace/dep1/git-ws.toml",
        "TMP/workspace/dep2/git-ws.toml",
        "",
    ]


def test_upgrade(tmp_path):
    """Test Manifest Upgrade."""
    manifest_path = tmp_path / "my.toml"
    manifest_path.write_text(
        """
something = "different"

[[entry]]
name = "my entry"

[[dependencies]]
name = 'foo'

# My Comment

[[remotes]]
name = 'myremote'
url-base = "my-url"

[[dependencies]]
name = 'bar'

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
## Welcome to Git Workspace's Manifest. It actually contains 4 parts:
##
## * Remotes
## * Groups
## * Defaults
## * Dependencies
##
## =========
##  Remotes
## =========
##
## Remotes just refer to a directory with repositories.
##
## We support relative paths for dependencies. So, if your dependencies are next
## to your repository, you might NOT need any remote.
## In other terms: You only need remotes if your dependencies are located on
## OTHER servers than your server with this manifest.
##
## Remotes have two attributes:
## * name: Required. String.
##         Name of the remote. Any valid string. Must be unique within your
##         manifest.
## * url-base: Required. String.
##             URL Prefix. The project 'name' or 'sub-url' will be appended
##             later-on.
##
# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"
something = "different"
[[remotes]]
name = 'myremote'
url-base = "my-url"


## =========
##  Groups
## =========
##
## Groups structure dependencies.
##
## Groups are optional by default.
## If a dependency belongs to a group, it becomes optional likewise.
## Groups can be later on selected/deselected by '+group' or '-group'.
## An optional group can be selected by '+group',
## a non-optional group can be deselected by '-group'.
## Deselection has higher priority than selection.
##
## Dependencies can refer to non-existing groups. You do NOT need to specify
## all used groups.
##
## Groups have two attributes:
## * name: Required. String.
##         Name of the group. Any valid string. Must be unique within your
##         manifest.
## * optional: Optional. Bool. Default is True.
##             Specifies if the group is optional. Meaning it must be selected
##             explicitly. Otherwise the dependency is not added by default.
##
## The following lines set a group as non-optional.
# [[groups]]
# name = "test"
# optional = false


## ==========
##  Defaults
## ==========
##
## The 'defaults' section specifies default values for dependencies.
##
## * remote: Optional. String.
##           Remote used as default.
##           The 'remote' MUST be defined in the 'remotes' section above!
## * revision: Optional. String.
##             Revision used as default. Tag or Branch.
##
## NOTE: It is recommended to specify a default revision (i.e. 'main').
##       If a dependency misses 'revision', GitWS will not take care about
##       revision handling. This may lead to strange side-effects. You
##       have been warned.

[defaults]
# remote = "myserver"
# revision = "main"


## ==============
##  Dependencies
## ==============
##
## The 'dependencies' section specifies all your git clones you need for your
## project to operate.
##
## A dependency has the following attributes:
## * name: Required. String.
##         Just name your dependency. It is recommended to choose a
##         unique name, but not a must.
## * remote: Optional. String. Restricted (see RESTRICTIONS below).
##           Remote Alias.
##           The 'remote' MUST be defined in the 'remotes' section above!
##           The 'remote' can also be specified in the 'defaults' section.
## * sub-url: Optional. String. Default: '../{name}[.git]' (see NOTE1 below).
##            Relative URL to 'url-base' of your specified 'remote'
##            OR
##            Relative URL to the URL of the repository containing this
##            manifest.
## * url: Optional. String. Restricted (see RESTRICTIONS below).
##        Absolute URL to the dependent repository.
## * revision: Optional. String.
##             Revision to be checked out.
##             If this attribute is left blank, GitWS does NOT manage the
##             dependency revision (see NOTE2 below)!
##             The 'revision' can also be specified in the 'defaults' section.
## * path: Optional. String. Default is '{name}'.
##         Project Filesystem Path. Relative to Workspace Root Directory.
##         The dependency 'name' is used as default for 'path'.
##         The 'path' MUST be unique within your manifest.
## * manifest_path: Optional. String. Default: 'git-ws.toml'.
##                   Path to manifest.
##                   Relative to 'path'.
##                   Avoid changing it! It is just additional effort.
## * groups: Optional. List of Strings.
##           Dependency Groups.
##           Dependencies can be categorized into groups.
##           Groups are optional by default. See 'groups' section above.
##
## NOTE1: 'sub-url' is '../{name}[.git]' by default. Meaning if the dependency
##        is next to your repository containing this manifest, the dependency
##        is automatically found.
##        The '.git' suffix is appended if the repository containing this
##        manifest uses a '.git' suffix.
##
## NOTE2: It is recommended to specify a revision (i.e. 'main') either
##        explicitly or via the 'default' section.
##        Without a 'revision' GitWS will not take care about revision
##        handling. This may lead to strange side-effects.
##        You have been warned.
##
## RESTRICTIONS:
##
## * `remote` and `url` are mutually exclusive.
## * `url` and `sub-url` are likewise mutually exclusive
## * `sub-url` requires a `remote`.
##
##
## A full flavored dependency using a 'remote':
# [[dependencies]]
# name = "myname"
# remote = "remote"
# sub-url = "my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]

## A full flavored dependency using a 'url':
# [[dependencies]]
# name = "myname"
# url = "https://github.com/myuser/my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]

## A minimal dependency:
# [[dependencies]]
# name = "my"
[[dependencies]]
name = 'foo'

[[dependencies]]
name = 'bar'

[[entry]]
name = "my entry"

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
