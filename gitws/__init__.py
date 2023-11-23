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

"""
Git Workspace - Multi Repository Management Tool.

`git ws` is a simple and lean multi repository management tool, with the following features:

* Integrated into git command line interface
* Dependency and transient dependency handling
* Relative URL support

The :any:`GitWS` class provides a simple programmatic interface similar to the command line interface.
See :any:`GitWS` for all details.

Getting Started
---------------

There are 4 ways to create a :any:`GitWS` instances in the different szenarios:

* :any:`GitWS.from_path()`: Create :any:`GitWS` for EXISTING workspace at ``path``.
* :any:`GitWS.create()`: Create NEW workspace at ``path`` and return corresponding :any:`GitWS`.
* :any:`GitWS.init()`: Initialize NEW Workspace and return corresponding :any:`GitWS`.
* :any:`GitWS.clone()`: Clone git ``url``, initialize NEW Workspace and return corresponding :any:`GitWS`.

The python module is named `gitws`:

>>> import gitws

Assume an existing git clone with an empty parent directory:

>>> import pathlib
>>> main_path = pathlib.Path('main')
>>> gitws.Git.init(main_path)
Git(...)

Create a manifest:

>>> manifest = gitws.ManifestSpec(defaults=gitws.Defaults(revision='main'))
>>> gitws.save(manifest, main_path / "git-ws.toml")

Initialize Workspace

>>> gws = gitws.GitWS.init(main_path=main_path)
>>> gws
GitWS(...)

In case of an existing Git Workspace in your current working directory just run:

>>> gws = gitws.GitWS.from_path()

:any:`GitWS.update()` updates all dependencies

>>> gws.update()

Run a shell command on all git clones

>>> gws.run_foreach(['ls', '-l'])

For more advanced operations, the :any:`GitWS.clones` iterates over all clones, starting from the main project.

>>> for clone in gws.clones():
...     print(f"=== {clone.info} ===")
...     clone.project
...     clone.git
=== main (MAIN 'main') ===
Project(name='main', path='main', level=0, is_main=True)
Git(...)

Overview
--------

* :py:class:`gitws.GitWS`: the central API to the main functionality.
* :py:class:`gitws.Clone`: is the pair of Of :py:class:`gitws.Project` And :py:class:`gitws.Git` Interface.
* :py:class:`gitws.Git`: provides a reduced API to ``git``.
* :py:class:`gitws.ManifestSpec`: Manifest specification for the current project.
* :py:class:`gitws.Manifest`: Manifest as needed by :py:class:`gitws.GitWS` derived from
  :py:class:`gitws.ManifestSpec`.
* :py:class:`gitws.ProjectSpec`: Dependency Specification in :py:class:`gitws.ManifestSpec`.
* :py:class:`gitws.Project`: A Single Dependency as needed by :py:class:`gitws.GitWS` derived from
  :py:class:`gitws.ProjectSpec`.
* :py:class:`gitws.Remote`: Remote Alias in :py:class:`gitws.ManifestSpec`.
* :py:class:`gitws.Defaults`: Default Values in :py:class:`gitws.ManifestSpec`.
* :py:class:`gitws.AppConfigData`: :py:class:`gitws.GitWS` Configuration.
* :py:class:`gitws.Workspace`: the file system location containing all git clones.
"""

import logging

from pydantic import ValidationError

from ._iters import ManifestIter, ProjectIter
from .appconfig import AppConfig, AppConfigLocation
from .clone import Clone, CloneFilter, filter_clone_on_branch, map_paths
from .datamodel import (
    AppConfigData,
    Defaults,
    FileRef,
    Group,
    GroupFilter,
    GroupFilters,
    Groups,
    GroupSelect,
    GroupSelects,
    MainFileRef,
    Manifest,
    ManifestSpec,
    Project,
    ProjectSpec,
    Remote,
    WorkspaceFileRef,
    WorkspaceFileRefs,
)
from .exceptions import (
    GitCloneMissingError,
    GitCloneMissingOriginError,
    GitCloneNotCleanError,
    GitTagExistsError,
    IncompatibleFormatError,
    InitializedError,
    InvalidConfigurationFileError,
    InvalidConfigurationLocationError,
    ManifestError,
    ManifestExistError,
    ManifestNotFoundError,
    NoAbsUrlError,
    NoGitError,
    NoMainError,
    NotEmptyError,
    OutsideWorkspaceError,
    UninitializedError,
    WorkspaceNotEmptyError,
)
from .git import Git
from .gitws import GitWS
from .gitwsmanifestformat import dump, load, save, upgrade
from .manifestformat import ManifestFormat
from .workspace import Workspace
from .workspacefinder import find_workspace
