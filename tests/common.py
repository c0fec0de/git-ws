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

"""Shared Test Stuff."""
MANIFEST_DEFAULT = """\
version = "1.0"
##
## Git Workspace\'s Manifest. Please see the documentation at:
##
## https://git-ws.readthedocs.io/en/latest/manual/manifest.html
##


# group-filters = ["+test", "-doc", "+feature@path"]
group-filters = []


# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"


[defaults]
# remote = "myserver"
# revision = "main"
# groups = ["+test"]
# with_groups = ["doc"]


## A full flavored dependency using a \'remote\':
# [[dependencies]]
# name = "myname"
# remote = "remote"
# sub-url = "my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]

## A full flavored dependency using a \'url\':
# [[dependencies]]
# name = "myname"
# url = "https://github.com/myuser/my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]

## A minimal dependency:
# [[dependencies]]
# name = "my"
"""
