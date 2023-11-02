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
import tempfile
from pathlib import Path

from pytest import fixture

from gitws import Git, ManifestSpec
from gitws.const import CONFIG_PATH, INFO_PATH, MANIFESTS_PATH

from .fixtures import create_repos, set_meta
from .util import chdir, cli, run


@fixture()
def repos():
    """Fixture with main and four depedency repos."""
    with tempfile.TemporaryDirectory(prefix="git-ws-test-repos") as tmpdir:
        repos_path = Path(tmpdir)

        create_repos(repos_path, add_dep5=True, add_dep6=True)

        yield repos_path


def test_tag(tmp_path, repos):
    """Create Tag."""
    # pylint: disable=too-many-locals
    workspace = tmp_path / "main"
    dep6_sha_repo = Git(repos / "dep6").get_sha(revision="HEAD^")

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main"), "--update"], tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "===== main/dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Cloning 'REPOS/dep1'.",
            "===== main/dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Cloning 'REPOS/dep2'.",
            "===== main/dep5 ('dep5', revision='final2') =====",
            "Cloning 'REPOS/dep5'.",
            f"===== main/dep6 ('dep6', revision='{dep6_sha_repo}') =====",
            "Cloning 'REPOS/dep6'.",
            "===== main/dep4 ('dep4', revision='main') =====",
            "Cloning 'REPOS/dep4'.",
            "",
        ]

    assert (workspace / INFO_PATH).read_text() == '# Git Workspace System File. DO NOT EDIT.\n\nmain_path = "main"\n'

    main_git = Git(workspace / "main")
    dep1_sha = Git(workspace / "dep1").get_sha()
    dep2_sha = Git(workspace / "dep2").get_sha()
    dep4_sha = Git(workspace / "dep4").get_sha()
    dep5_sha = Git(workspace / "dep5").get_sha()
    dep6_sha = Git(workspace / "dep6").get_sha()
    dep1_shas = dep1_sha[:7]
    dep2_shas = dep2_sha[:7]
    dep4_shas = dep4_sha[:7]
    dep5_shas = dep5_sha[:7]
    dep6_shas = dep6_sha[:7]

    assert dep6_sha == dep6_sha_repo

    with chdir(workspace):
        main_git.tag("OTHERTAG")

        # create tag
        assert not (workspace / "main" / MANIFESTS_PATH / "MYTAG.toml").exists()
        set_meta(path=main_git.path)
        assert cli(("tag", "MYTAG")) == ["===== main (MAIN 'main', revision='main') =====", ""]
        assert (workspace / "main" / MANIFESTS_PATH / "MYTAG.toml").exists()

        # shorten output
        cli(("git", "config", "advice.detachedHead", "false"))

        assert cli(("manifest", "paths")) == [
            str(workspace / "main" / "git-ws.toml"),
            str(workspace / "dep1" / "git-ws.toml"),
            str(workspace / "dep2" / "git-ws.toml"),
            "",
        ]

        # checkout should do nothing
        assert cli(("checkout",)) == [
            "===== main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Already on '1-feature'",
            "===== dep5 ('dep5', revision='final2') =====",
            f"HEAD is now at {dep5_shas} initial",
            f"===== dep6 ('dep6', revision='{dep6_sha}') =====",
            f"HEAD is now at {dep6_shas} initial",
            "===== dep4 ('dep4', revision='main') =====",
            "Already on 'main'",
            "",
        ]

        # checkout TAG
        main_git.checkout(revision="MYTAG")
        assert cli(("manifest", "paths")) == [
            str(workspace / "main" / MANIFESTS_PATH / "MYTAG.toml"),
            str(workspace / "dep1" / "git-ws.toml"),
            str(workspace / "dep2" / "git-ws.toml"),
            "",
        ]
        assert cli(("checkout",)) == [
            "===== main (MAIN 'main', revision='MYTAG') =====",
            f"===== dep1 ('dep1', revision='{dep1_sha}') " "=====",
            f"HEAD is now at {dep1_shas} other",
            f"===== dep2 ('dep2', revision='{dep2_sha}', submodules=False) " "=====",
            f"HEAD is now at {dep2_shas} feature",
            f"===== dep5 ('dep5', revision='{dep5_sha}') " "=====",
            f"HEAD is now at {dep5_shas} initial",
            f"===== dep6 ('dep6', revision='{dep6_sha}') " "=====",
            f"HEAD is now at {dep6_shas} initial",
            f"===== dep4 ('dep4', revision='{dep4_sha}') " "=====",
            f"HEAD is now at {dep4_shas} initial",
            "",
        ]

        # checkout branch again
        main_git.checkout(revision="main")
        assert cli(("checkout",)) == [
            "===== main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Switched to branch '1-feature'",
            "===== dep5 ('dep5', revision='final2') =====",
            f"HEAD is now at {dep5_shas} initial",
            f"===== dep6 ('dep6', revision='{dep6_sha}') " "=====",
            f"HEAD is now at {dep6_shas} initial",
            "===== dep4 ('dep4', revision='main') =====",
            "Switched to branch 'main'",
            "",
        ]

        # checkout other tag
        main_git.checkout(revision="OTHERTAG")
        assert cli(("checkout",)) == [
            "===== main (MAIN 'main', revision='OTHERTAG') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Already on '1-feature'",
            "===== dep5 ('dep5', revision='final2') =====",
            f"HEAD is now at {dep5_shas} initial",
            f"===== dep6 ('dep6', revision='{dep6_sha}') " "=====",
            f"HEAD is now at {dep6_shas} initial",
            "===== dep4 ('dep4', revision='main') =====",
            "Already on 'main'",
            "",
        ]

        # Feed back
        run(("git", "checkout", "-b", "work"), cwd=(repos / "main"), check=True)
        run(("git", "push", "--tags"), cwd=(workspace / "main"), check=True)

    other_workspace = tmp_path / "other"
    other_main_git = Git(other_workspace / "main")

    with chdir(tmp_path):
        assert cli(
            ["clone", str(repos / "main"), "other/main", "--update", "--revision", "MYTAG"],
            tmp_path=tmp_path,
            repos_path=repos,
        ) == [
            "===== other/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "===== other/dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Cloning 'REPOS/dep1'.",
            "===== other/dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Cloning 'REPOS/dep2'.",
            "===== other/dep5 ('dep5', revision='final2') =====",
            "Cloning 'REPOS/dep5'.",
            f"===== other/dep6 ('dep6', revision='{dep6_sha}') =====",
            "Cloning 'REPOS/dep6'.",
            "===== other/dep4 ('dep4', revision='main') =====",
            "Cloning 'REPOS/dep4'.",
            "",
        ]

    with chdir(other_workspace):
        # shorten output
        cli(("git", "config", "advice.detachedHead", "false"))

        assert cli(("checkout",)) == [
            "===== main (MAIN 'main', revision='MYTAG') =====",
            f"===== dep1 ('dep1', revision='{dep1_sha}') " "=====",
            f"HEAD is now at {dep1_shas} other",
            f"===== dep2 ('dep2', revision='{dep2_sha}', submodules=False) " "=====",
            f"HEAD is now at {dep2_shas} feature",
            f"===== dep5 ('dep5', revision='{dep5_sha}') =====",
            f"HEAD is now at {dep5_shas} initial",
            f"===== dep6 ('dep6', revision='{dep6_sha}') =====",
            f"HEAD is now at {dep6_shas} initial",
            f"===== dep4 ('dep4', revision='{dep4_sha}') " "=====",
            f"HEAD is now at {dep4_shas} initial",
            "",
        ]
        other_main_git.checkout(revision="main")
        assert cli(("checkout",)) == [
            "===== main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Switched to branch '1-feature'",
            "===== dep5 ('dep5', revision='final2') =====",
            f"HEAD is now at {dep5_shas} initial",
            f"===== dep6 ('dep6', revision='{dep6_sha}') " "=====",
            f"HEAD is now at {dep6_shas} initial",
            "===== dep4 ('dep4', revision='main') =====",
            "Switched to branch 'main'",
            "",
        ]

    assert (workspace / INFO_PATH).read_text() == '# Git Workspace System File. DO NOT EDIT.\n\nmain_path = "main"\n'
    assert (
        other_workspace / INFO_PATH
    ).read_text() == '# Git Workspace System File. DO NOT EDIT.\n\nmain_path = "main"\n'
    assert (workspace / CONFIG_PATH).read_text() == 'manifest_path = "git-ws.toml"\n'
    assert (other_workspace / CONFIG_PATH).read_text() == 'manifest_path = "git-ws.toml"\n'


def test_tag_dep(tmp_path, repos):
    """Create Tag."""
    main_workspace = tmp_path / "main"
    dep1_workspace = tmp_path / "dep1"
    dep6_sha = Git(repos / "dep6").get_sha(revision="HEAD^")

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "dep1"), "--update"], tmp_path=tmp_path, repos_path=repos) == [
            "===== dep1/dep1 (MAIN 'dep1') =====",
            "Cloning 'REPOS/dep1'.",
            "===== dep1/dep4 ('dep4', revision='main') =====",
            "Cloning 'REPOS/dep4'.",
            "",
        ]
    with chdir(dep1_workspace):
        # create tag
        set_meta(path=dep1_workspace / "dep1")
        assert cli(("tag", "DEP1TAG")) == ["===== dep1 (MAIN 'dep1', revision='main') =====", ""]

        # push
        run(("git", "checkout", "-b", "work"), cwd=(repos / "dep1"), check=True)
        run(("git", "push", "--tags"), cwd=(dep1_workspace / "dep1"), check=True)
        run(("git", "checkout", "main"), cwd=(repos / "dep1"), check=True)

        # introduce changes
        (repos / "dep1" / "change.txt").touch()
        dep1_git = Git(repos / "dep1")
        set_meta(path=dep1_git.path)
        dep1_git.add((Path("change.txt"),))
        dep1_git.commit(msg="change dep1")

        (repos / "dep4" / "change.txt").touch()
        dep4_git = Git(repos / "dep4")
        set_meta(path=dep4_git.path)
        sha4 = dep4_git.get_sha()
        dep4_git.add((Path("change.txt"),))
        dep4_git.commit(msg="change dep4")

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main")], tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "Workspace initialized at 'main'. Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]
        manifest_path = main_workspace / "main" / "git-ws.toml"
        manifest_spec = ManifestSpec.load(manifest_path)
        deps = [
            (dep.model_copy(update={"revision": "DEP1TAG"}) if dep.name == "dep1" else dep)
            for dep in manifest_spec.dependencies
        ]
        manifest_spec = manifest_spec.model_copy(update={"dependencies": tuple(deps)})
        manifest_spec.save(manifest_path)

    with chdir(main_workspace):
        assert cli(["update"], tmp_path=tmp_path, repos_path=repos) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='DEP1TAG') =====",
            "Cloning 'REPOS/dep1'.",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Cloning 'REPOS/dep2'.",
            "===== dep5 ('dep5', revision='final2') =====",
            "Cloning 'REPOS/dep5'.",
            f"===== dep6 ('dep6', revision='{dep6_sha}') =====",
            "Cloning 'REPOS/dep6'.",
            f"===== dep4 ('dep4', revision='{sha4}') =====",
            "Cloning 'REPOS/dep4'.",
            "",
        ]

        assert cli(("manifest", "paths")) == [
            str(main_workspace / "main" / "git-ws.toml"),
            str(main_workspace / "dep1" / MANIFESTS_PATH / "DEP1TAG.toml"),
            str(main_workspace / "dep2" / "git-ws.toml"),
            "",
        ]


def test_tag_overwrite(tmp_path, repos):
    """Create Tag."""
    # pylint: disable=too-many-locals
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        cli(["clone", str(repos / "main"), "--update"], tmp_path=tmp_path, repos_path=repos)

    main_git = Git(workspace / "main")
    dep1_git = Git(workspace / "dep1")
    dep1_sha = Git(workspace / "dep1").get_sha()
    dep2_sha = Git(workspace / "dep2").get_sha()
    dep4_sha = Git(workspace / "dep4").get_sha()
    dep5_sha = Git(workspace / "dep5").get_sha()
    dep6_sha = Git(workspace / "dep6").get_sha()
    dep1_shas = dep1_sha[:7]
    dep2_shas = dep2_sha[:7]
    dep4_shas = dep4_sha[:7]
    dep5_shas = dep5_sha[:7]
    dep6_shas = dep6_sha[:7]

    with chdir(workspace):
        # shorten output
        cli(("git", "config", "advice.detachedHead", "false"))

        # create tag
        set_meta(path=main_git.path)
        assert cli(("tag", "MYTAG")) == ["===== main (MAIN 'main', revision='main') =====", ""]

        mytag = (workspace / "main" / MANIFESTS_PATH / "MYTAG.toml").read_text()

        (workspace / "dep1" / "foo.txt").touch()
        set_meta(path=dep1_git.path)
        dep1_git.add((Path("foo.txt"),))
        dep1_git.commit("change")

        dep1_sha = Git(workspace / "dep1").get_sha()
        dep1_shas = dep1_sha[:7]

        assert cli(("tag", "MYTAG"), exit_code=1) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Error: tag MYTAG already exists Try:",
            "",
            "Choose another name or use '--force'",
            "",
            "",
        ]
        assert (workspace / "main" / MANIFESTS_PATH / "MYTAG.toml").read_text() == mytag

        assert cli(("tag", "MYTAG", "--force")) == [
            "===== main (MAIN 'main', revision='main') =====",
            "",
        ]

        assert (workspace / "main" / MANIFESTS_PATH / "MYTAG.toml").read_text() != mytag

        # checkout TAG
        main_git.checkout(revision="MYTAG")
        assert cli(("checkout",)) == [
            "===== main (MAIN 'main', revision='MYTAG') =====",
            f"===== dep1 ('dep1', revision='{dep1_sha}') " "=====",
            f"HEAD is now at {dep1_shas} change",
            f"===== dep2 ('dep2', revision='{dep2_sha}', submodules=False) " "=====",
            f"HEAD is now at {dep2_shas} feature",
            f"===== dep5 ('dep5', revision='{dep5_sha}') " "=====",
            f"HEAD is now at {dep5_shas} initial",
            f"===== dep6 ('dep6', revision='{dep6_sha}') " "=====",
            f"HEAD is now at {dep6_shas} initial",
            f"===== dep4 ('dep4', revision='{dep4_sha}') " "=====",
            f"HEAD is now at {dep4_shas} initial",
            "",
        ]
