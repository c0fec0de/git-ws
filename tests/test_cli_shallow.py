# Copyright 2022-2025 c0fec0de
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

"""Shallow Handling."""

import os
from shutil import rmtree
from unittest import mock

from contextlib_chdir import chdir

from gitws import Git
from gitws._util import run

from .util import check, cli, path2url


def test_cli_clone_update(tmp_path, repos):
    """Shallow Cloning and Update."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", path2url(repos / "main"), "--depth=1"], tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'file://REPOS/main'.",
            "Workspace initialized at 'main'. Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        check(workspace, "main", depth=1, branches=3)
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)

        gitmain = Git(workspace / "main")
        gitmain.set_config("advice.detachedHead", "false")
        shamain = gitmain.get_sha()

        assert (workspace / ".git-ws" / "config.toml").read_text() == 'manifest_path = "git-ws.toml"\ndepth = 1\n'

    with chdir(workspace):
        assert cli(["update"], tmp_path=tmp_path, repos_path=repos) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "From file://REPOS/main",
            " * branch            main       -> FETCH_HEAD",
            f"HEAD is now at {shamain[0:7]} other",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Cloning 'file://REPOS/dep1'.",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Cloning 'file://REPOS/dep2'.",
            "===== dep4 ('dep4', revision='main') =====",
            "Cloning 'file://REPOS/dep4'.",
            "",
        ]

        check(workspace, "main", depth=1, branches=4)
        check(workspace, "dep1", depth=1, branches=3)
        check(workspace, "dep2", content="dep2-feature", depth=1, branches=2)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", depth=1, branches=2)
        check(workspace, "dep5", exists=False)

        gitmain = Git(workspace / "main")
        gitmain.set_config("advice.detachedHead", "false")
        shamain = gitmain.get_sha()

        git1 = Git(workspace / "dep1")
        git1.set_config("advice.detachedHead", "false")
        sha1 = git1.get_sha()

        git2 = Git(workspace / "dep2")
        git2.set_config("advice.detachedHead", "false")
        sha2 = git2.get_sha()

        git4 = Git(workspace / "dep4")
        git4.set_config("advice.detachedHead", "false")
        sha4 = git4.get_sha()

        assert cli(["update"], repos_path=repos) == [
            f"===== main (MAIN 'main', revision='{shamain}') =====",
            "Nothing to do.",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Fetching.",
            "From file://REPOS/dep1",
            " * branch            main       -> FETCH_HEAD",
            f"HEAD is now at {sha1[0:7]} other",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Fetching.",
            "From file://REPOS/dep2",
            " * branch            1-feature  -> FETCH_HEAD",
            f"HEAD is now at {sha2[0:7]} feature",
            "===== dep4 ('dep4', revision='main') =====",
            "Fetching.",
            "From file://REPOS/dep4",
            " * branch            main       -> FETCH_HEAD",
            f"HEAD is now at {sha4[0:7]} initial",
            "",
        ]

        check(workspace, "main", depth=1, branches=4)
        check(workspace, "dep1", depth=1, branches=4)
        check(workspace, "dep2", content="dep2-feature", depth=1, branches=3)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", depth=1, branches=3)
        check(workspace, "dep5", exists=False)


def test_cli_shallow_depth2(tmp_path, repos):
    """Shallow Clone with depth of 2."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        cmd = ["clone", path2url(repos / "main"), "--depth=2", "--update"]
        assert cli(cmd, tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'file://REPOS/main'.",
            "===== main/dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Cloning 'file://REPOS/dep1'.",
            "===== main/dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Cloning 'file://REPOS/dep2'.",
            "===== main/dep4 ('dep4', revision='main') =====",
            "Cloning 'file://REPOS/dep4'.",
            "",
        ]

        assert (workspace / ".git-ws" / "config.toml").read_text() == 'manifest_path = "git-ws.toml"\ndepth = 2\n'

        check(workspace, "main", depth=2, branches=3)
        check(workspace, "dep1", depth=2, branches=3)
        check(workspace, "dep2", content="dep2-feature", depth=2, branches=2)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", depth=1, branches=2)
        check(workspace, "dep5", exists=False)


def test_cli_fetch_unshallow(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        cmd = ["clone", path2url(repos / "main"), "--depth=1", "--update"]
        assert cli(cmd, tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'file://REPOS/main'.",
            "===== main/dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Cloning 'file://REPOS/dep1'.",
            "===== main/dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Cloning 'file://REPOS/dep2'.",
            "===== main/dep4 ('dep4', revision='main') =====",
            "Cloning 'file://REPOS/dep4'.",
            "",
        ]

        assert (workspace / ".git-ws" / "config.toml").read_text() == 'manifest_path = "git-ws.toml"\ndepth = 1\n'

        check(workspace, "main", depth=1, branches=3)
        check(workspace, "dep1", depth=1, branches=3)
        check(workspace, "dep2", content="dep2-feature", depth=1, branches=2)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", depth=1, branches=2)
        check(workspace, "dep5", exists=False)

    with chdir(workspace):
        assert cli(["fetch", "--unshallow", "-P", "dep1"]) == [
            "===== SKIPPING main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== SKIPPING dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "===== SKIPPING dep4 ('dep4', revision='main') =====",
            "",
        ]

        check(workspace, "main", depth=1)
        check(workspace, "dep1", depth=2)
        check(workspace, "dep2", content="dep2-feature", depth=1)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", depth=1)
        check(workspace, "dep5", exists=False)

        assert cli(["fetch", "--unshallow", "-P", "main", "-P", "dep2"]) == [
            "===== main (MAIN 'main', revision='main') =====",
            "===== SKIPPING dep1 ('dep1') =====",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "===== SKIPPING dep4 ('dep4', revision='main') =====",
            "",
        ]

        check(workspace, "main", depth=3)
        check(workspace, "dep1", depth=2)
        check(workspace, "dep2", content="dep2-feature", depth=2)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", depth=1)
        check(workspace, "dep5", exists=False)

        git4 = Git(workspace / "dep4")
        git4.set_config("advice.detachedHead", "false")
        sha4 = git4.get_sha()

        assert cli(["update"], repos_path=repos) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Fetching.",
            "Merging branch '1-feature'.",
            "===== dep4 ('dep4', revision='main') =====",
            "Fetching.",
            "From file://REPOS/dep4",
            " * branch            main       -> FETCH_HEAD",
            f"HEAD is now at {sha4[0:7]} initial",
            "",
        ]


def test_init(tmp_path):
    """Initialize."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        cli(["manifest", "create"])

        assert cli(["init", "--depth", "2", "--update"]) == [
            "===== . (MAIN 'main') =====",
            "Workspace initialized at '..'.",
            "",
        ]

        assert (tmp_path / ".git-ws" / "config.toml").read_text() == 'manifest_path = "git-ws.toml"\ndepth = 2\n'

        assert cli(["update"]) == [
            "===== . (MAIN 'main') =====",
            "Nothing to do.",
            "",
        ]


def test_cli_unshallow(tmp_path, repos):
    """Unshallow."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", path2url(repos / "main"), "--depth=1", "--update"])

        assert (workspace / ".git-ws" / "config.toml").read_text() == 'manifest_path = "git-ws.toml"\ndepth = 1\n'

    with chdir(workspace):
        assert cli(["unshallow", "-P", "dep1"])

        check(workspace, "main", depth=1)
        check(workspace, "dep1", depth=2)
        check(workspace, "dep2", content="dep2-feature", depth=1)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", depth=1)
        check(workspace, "dep5", exists=False)

        assert (workspace / ".git-ws" / "config.toml").read_text() == 'manifest_path = "git-ws.toml"\ndepth = 1\n'

    with chdir(workspace):
        assert cli(["unshallow"])

        check(workspace, "main", depth=3)
        check(workspace, "dep1", depth=2)
        check(workspace, "dep2", content="dep2-feature", depth=2)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", depth=1)
        check(workspace, "dep5", exists=False)

        assert (workspace / ".git-ws" / "config.toml").read_text() == 'manifest_path = "git-ws.toml"\ndepth = 0\n'

        # future clones
        rmtree(workspace / "dep1")
        assert cli(["update"])
        check(workspace, "dep1", depth=2)


def test_cli_shallow_cache(tmp_path, repos):
    """Shallow Clone with cache."""
    workspace = tmp_path / "main"

    cache = tmp_path / "cache"

    with mock.patch.dict(os.environ, {"GIT_WS_CLONE_CACHE": str(cache)}):
        with chdir(tmp_path):
            assert not cache.exists()

            cmd = ["clone", path2url(repos / "main"), "--depth=1", "--update"]
            assert cli(cmd, tmp_path=tmp_path, repos_path=repos) == [
                "===== main/main (MAIN 'main') =====",
                "Cloning 'file://REPOS/main'.",
                "Initializing clone-cache",
                "From file://REPOS/main",
                " * branch            HEAD       -> FETCH_HEAD",
                "===== main/dep1 ('dep1') =====",
                "WARNING: Clone dep1 has no revision!",
                "Cloning 'file://REPOS/dep1'.",
                "Initializing clone-cache",
                "From file://REPOS/dep1",
                " * branch            HEAD       -> FETCH_HEAD",
                "===== main/dep2 ('dep2', revision='1-feature', submodules=False) =====",
                "Cloning 'file://REPOS/dep2'.",
                "Initializing clone-cache",
                "From file://REPOS/dep2",
                " * branch            1-feature  -> FETCH_HEAD",
                "===== main/dep4 ('dep4', revision='main') =====",
                "Cloning 'file://REPOS/dep4'.",
                "Initializing clone-cache",
                "From file://REPOS/dep4",
                " * branch            main       -> FETCH_HEAD",
                "",
            ]

            check(workspace, "main", depth=1)  # branches=3)
            check(workspace, "dep1", depth=1)  # branches=2)
            check(workspace, "dep2", content="dep2-feature", depth=1)  # branches=5)
            check(workspace, "dep3", exists=False)
            check(workspace, "dep4", depth=1)  # branches=2)
            check(workspace, "dep5", exists=False)

            # clone again
            rmtree(workspace)
            assert cli(cmd, tmp_path=tmp_path, repos_path=repos) == [
                "===== main/main (MAIN 'main') =====",
                "Cloning 'file://REPOS/main'.",
                "Using clone-cache",
                "From file://REPOS/main",
                " * branch            HEAD       -> FETCH_HEAD",
                "===== main/dep1 ('dep1') =====",
                "WARNING: Clone dep1 has no revision!",
                "Cloning 'file://REPOS/dep1'.",
                "Using clone-cache",
                "From file://REPOS/dep1",
                " * branch            HEAD       -> FETCH_HEAD",
                "===== main/dep2 ('dep2', revision='1-feature', submodules=False) =====",
                "Cloning 'file://REPOS/dep2'.",
                "Using clone-cache",
                "From file://REPOS/dep2",
                " * branch            1-feature  -> FETCH_HEAD",
                "===== main/dep4 ('dep4', revision='main') =====",
                "Cloning 'file://REPOS/dep4'.",
                "Using clone-cache",
                "From file://REPOS/dep4",
                " * branch            main       -> FETCH_HEAD",
                "",
            ]


def test_cli_shallow_update(tmp_path, repos):
    """Update Shallow Clone."""
    workspace = tmp_path / "main"

    def modify(path):
        dep = Git(path)
        (dep.path / "some.txt").write_text(path.name)
        dep.add(("some.txt",))
        dep.commit(msg="some")
        sha = dep.get_sha()

        dep.tag("mytag", msg="mytag")

        (dep.path / "foo.txt").touch()
        dep.add(("foo.txt",))
        dep.commit(msg="foo")
        head = dep.get_sha()
        return sha, head

    with chdir(tmp_path):
        cli(("clone", path2url(repos / "main"), "--depth=1", "--update"))

        sha1, _ = modify(repos / "dep1")
        sha2, _ = modify(repos / "dep2")
        modify(repos / "dep3")
        _, head4 = modify(repos / "dep4")

    with chdir(workspace / "main"):
        cli(["dep", "set", "dep1", "revision", sha1])
        cli(["dep", "set", "dep2", "revision", "mytag"])

        Git(workspace / "dep4").set_config("advice.detachedHead", "false")

        cli(("update",), tmp_path=tmp_path, repos_path=repos)
        assert Git(workspace / "dep1").get_sha() == sha1
        assert Git(workspace / "dep2").get_sha() == sha2
        assert Git(workspace / "dep4").get_sha() == head4
        assert Git(workspace / "dep1").get_revision() == sha1
        assert Git(workspace / "dep2").get_revision() == sha2
        assert Git(workspace / "dep4").get_revision() == head4
