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

"""Git Workspace Manifest Testing."""

from pytest import fixture

from gitws import Defaults, FileRef, MainFileRef, ManifestSpec, ProjectSpec, Remote
from gitws.gitwsmanifestformat import GitWSManifestFormat

from .common import MANIFEST_DEFAULT


@fixture
def mod_manifest_spec():
    """Return Modified Manifest Spec."""
    yield ManifestSpec(
        version="1.1",
        remotes=[Remote(name="remote")],
        group_filters=("+test",),
        defaults=Defaults(remote="remote"),
        linkfiles=[
            MainFileRef(src="l0", dest="s/l0"),
            MainFileRef(src="l1", dest="s/l1"),
            MainFileRef(src="l2", dest="s/l2", groups=["ab", "cd"]),
        ],
        copyfiles=[
            MainFileRef(src="l0", dest="s/l0"),
            MainFileRef(src="l1", dest="s/l1"),
            MainFileRef(src="l2", dest="s/l2", groups=["ab", "cd"]),
        ],
        dependencies=(
            ProjectSpec(
                name="dep",
                linkfiles=(
                    FileRef(src="src0", dest="subdir/dest0"),
                    FileRef(src="src1", dest="subdir/dest1"),
                ),
                copyfiles=(
                    FileRef(src="src2", dest="subdir/dest2"),
                    FileRef(src="src3", dest="subdir/dest3"),
                ),
            ),
        ),
    )


def test_save_default(tmp_path):
    """Default Manifest Saving."""
    manifest_spec = ManifestSpec()
    filepath = tmp_path / "manifest.toml"
    mfmt = GitWSManifestFormat()
    mfmt.save(manifest_spec, filepath)
    assert filepath.read_text() == MANIFEST_DEFAULT


def test_save_mod(tmp_path, mod_manifest_spec):
    """Modified Manifest Saving."""
    filepath = tmp_path / "manifest.toml"
    mfmt = GitWSManifestFormat()
    mfmt.save(mod_manifest_spec, filepath)
    manifest = """\
version = "1.1"
##
## Git Workspace's Manifest. Please see the documentation at:
##
## https://git-ws.readthedocs.io/en/stable/manual/manifest.html
##


# group-filters = ["-doc", "-feature@path"]
group-filters = ["+test"]


# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"
[[remotes]]
name = "remote"


[defaults]
remote = "remote"

# remote = "myserver"
# revision = "main"
# groups = ["test"]
# with-groups = ["doc"]


## A minimal dependency:
# [[dependencies]]
# name = "my"

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

[[dependencies]]
name = "dep"

[[dependencies.linkfiles]]
src = "src0"
dest = "subdir/dest0"

[[dependencies.linkfiles]]
src = "src1"
dest = "subdir/dest1"

[[dependencies.copyfiles]]
src = "src2"
dest = "subdir/dest2"

[[dependencies.copyfiles]]
src = "src3"
dest = "subdir/dest3"


# [[linkfiles]]
# src = "file-in-main-clone.txt"
# dest = "link-in-workspace.txt"
[[linkfiles]]
src = "l0"
dest = "s/l0"

[[linkfiles]]
src = "l1"
dest = "s/l1"

[[linkfiles]]
src = "l2"
dest = "s/l2"
groups = ["ab", "cd"]


# [[copyfiles]]
# src = "file-in-main-clone.txt"
# dest = "file-in-workspace.txt"
[[copyfiles]]
src = "l0"
dest = "s/l0"

[[copyfiles]]
src = "l1"
dest = "s/l1"

[[copyfiles]]
src = "l2"
dest = "s/l2"
groups = ["ab", "cd"]
"""
    assert filepath.read_text() == manifest


def test_save_empty(tmp_path, mod_manifest_spec):
    """Modified Manifest Saving to Empty File."""
    filepath = tmp_path / "manifest.toml"
    filepath.touch()
    mfmt = GitWSManifestFormat()
    mfmt.save(mod_manifest_spec, filepath)
    manifest = """\
version = "1.1"
group-filters = ["+test"]

[[remotes]]
name = "remote"

[defaults]
remote = "remote"

[[dependencies]]
name = "dep"

[[dependencies.linkfiles]]
src = "src0"
dest = "subdir/dest0"

[[dependencies.linkfiles]]
src = "src1"
dest = "subdir/dest1"

[[dependencies.copyfiles]]
src = "src2"
dest = "subdir/dest2"

[[dependencies.copyfiles]]
src = "src3"
dest = "subdir/dest3"

[[linkfiles]]
src = "l0"
dest = "s/l0"

[[linkfiles]]
src = "l1"
dest = "s/l1"

[[linkfiles]]
src = "l2"
dest = "s/l2"
groups = ["ab", "cd"]

[[copyfiles]]
src = "l0"
dest = "s/l0"

[[copyfiles]]
src = "l1"
dest = "s/l1"

[[copyfiles]]
src = "l2"
dest = "s/l2"
groups = ["ab", "cd"]
"""
    assert filepath.read_text() == manifest


def test_save_no_update(tmp_path, mod_manifest_spec):
    """Modified Manifest Saving Without Update."""
    filepath = tmp_path / "manifest.toml"
    filepath.touch()
    mfmt = GitWSManifestFormat()
    mfmt.save(mod_manifest_spec, filepath, update=False)
    manifest = """\
version = "1.1"
##
## Git Workspace's Manifest. Please see the documentation at:
##
## https://git-ws.readthedocs.io/en/stable/manual/manifest.html
##


# group-filters = ["-doc", "-feature@path"]
group-filters = ["+test"]


# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"
[[remotes]]
name = "remote"


[defaults]
remote = "remote"

# remote = "myserver"
# revision = "main"
# groups = ["test"]
# with-groups = ["doc"]


## A minimal dependency:
# [[dependencies]]
# name = "my"

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

[[dependencies]]
name = "dep"

[[dependencies.linkfiles]]
src = "src0"
dest = "subdir/dest0"

[[dependencies.linkfiles]]
src = "src1"
dest = "subdir/dest1"

[[dependencies.copyfiles]]
src = "src2"
dest = "subdir/dest2"

[[dependencies.copyfiles]]
src = "src3"
dest = "subdir/dest3"


# [[linkfiles]]
# src = "file-in-main-clone.txt"
# dest = "link-in-workspace.txt"
[[linkfiles]]
src = "l0"
dest = "s/l0"

[[linkfiles]]
src = "l1"
dest = "s/l1"

[[linkfiles]]
src = "l2"
dest = "s/l2"
groups = ["ab", "cd"]


# [[copyfiles]]
# src = "file-in-main-clone.txt"
# dest = "file-in-workspace.txt"
[[copyfiles]]
src = "l0"
dest = "s/l0"

[[copyfiles]]
src = "l1"
dest = "s/l1"

[[copyfiles]]
src = "l2"
dest = "s/l2"
groups = ["ab", "cd"]
"""
    assert filepath.read_text() == manifest


def test_save_load(tmp_path, mod_manifest_spec):
    """Modified Manifest Saving And Load."""
    filepath = tmp_path / "manifest.toml"
    filepath.touch()
    mfmt = GitWSManifestFormat()
    mfmt.save(mod_manifest_spec, filepath, update=False)
    assert mfmt.load(filepath) == mod_manifest_spec
