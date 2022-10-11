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
MANIFEST_DEFAULT = """version = "1.0"
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
"""
