[![PyPI Version](https://badge.fury.io/py/git-ws.svg)](https://badge.fury.io/py/git-ws)
[![PyPI Downloads](https://img.shields.io/pypi/dm/git-ws.svg?label=pypi%20downloads)](https://pypi.python.org/pypi/git-ws)
[![Python Build](https://github.com/c0fec0de/git-ws/actions/workflows/main.yml/badge.svg)](https://github.com/c0fec0de/git-ws/actions/workflows/main.yml)
[![Documentation](https://readthedocs.org/projects/git-ws/badge/?version=latest)](https://git-ws.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/c0fec0de/git-ws/badge.svg?branch=main)](https://coveralls.io/github/c0fec0de/git-ws?branch=main)
[![python-versions](https://img.shields.io/pypi/pyversions/git-ws.svg)](https://pypi.python.org/pypi/git-ws)
[![pylint](https://img.shields.io/badge/linter-pylint-%231674b1?style=flat)](https://www.pylint.org/)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Git Workspace - Multi Repository Management Tool

* [Installation](https://github.com/c0fec0de/git-ws#-installation)
* [Usage](https://github.com/c0fec0de/git-ws#-usage)
* [Getting Started](https://github.com/c0fec0de/git-ws#-getting-started)
* [Cheat-Sheet](https://github.com/c0fec0de/git-ws#%EF%B8%8F-cheat-sheet)
* [Python API](https://github.com/c0fec0de/git-ws#-python-api)
* [Alternatives](https://github.com/c0fec0de/git-ws#-alternatives)

Git Workspace is a lightweight tool for creating and managing *workspaces* consisting of several interdependent `git` repositories. Starting from a *main repository*, Git Workspace discovers dependencies specified in a *manifest file*, fetching any specified required repositories and assembling them into a single workspace.

![Workspace](https://github.com/c0fec0de/git-ws/raw/main/docs/images/workspace.png)

👉 You can read more about the used [nomenclature](https://git-ws.readthedocs.io/en/latest/manual/nomenclature.html) in the [documentation](https://git-ws.readthedocs.io/en/latest/index.html).



## 📦 Installation

Git Workspace is written in Python and - as usual - installing it is pretty easy:

```bash
pip install git-ws
```

And that's it! Ideally, if your project also uses Python, we recommend adding Git Workspace as a dependency to it as well so that you can track the exact version of it together with your other dependencies. For example, if you use `poetry`, add it by running

```bash
# Add Git Workspace as a development dependency:
poetry add --group dev git-ws
```

For testing you can try:

```bash
git ws --version
```


## 📔 Usage

Git Workspace is integrated into git `git ws` - this is what you will be using most of the time.

#### The Manifest

Let's assume we have a project called `myapp`, which requires a library `mylib` that is maintained in another `git` repository. In order to use this project with Git Workspace, `myapp` needs to provide a so called *manifest*. A Git Workspace manifest is a simple [TOML](https://toml.io/) file - by default called `git-ws.toml` in the project's root folder - which defines the dependencies a project has as well as some other meta information. A minimal manifest for our project could look like this:

```toml
[[dependencies]]
name = "mylib"
url = "git@github.com:example/mylib.git"
revision = "v2.3.4"
```

If `myapp` and `mylib` are stored on the same server (side-by-side), then the manifest can even be simpler:

```toml
[[dependencies]]
name = "mylib"
revision = "v2.3.4"
```

The project will be searched via a relative path (which is either `../mylib` or `../mylib.git` depending on the main repository's URL). Relative paths are in general useful as they allow using the same protocol for the main repository as well as any of its dependencies.

See the [Manifest Documentation](https://git-ws.readthedocs.io/en/latest/manual/manifest.html) for any further details on available options.

#### The Initial Clone

To build a workspace from a project prepared like that, simply clone it via `git ws`:

```bash
cd $HOME/Projects
git ws clone --update git@github.com:example/myapp.git
```

👉 Without the `--update` option, only the main repository will be fetched.

The above will clone the app repository and also the library side-by-side:

```bash
ls -a myapp/
# Should print something like
.
..
.git-ws
myapp
mylib
```

As you can see, besides the two repositories we wanted, there is also a hidden `.git-ws` folder where the tool stores the needed configuration data.

The [`git ws clone` documentation](https://git-ws.readthedocs.io/en/latest/manual/command-line-interface/workspace-management.html#git-ws-clone) describes all options.

#### Initialization

Sometimes there are use cases where using `git ws clone` cannot be used. For example, when you set up your manifest for the first time or when a CI/CD system creates the initial clone of the main repository, you may need a way to fetch the remaining projects. This can be done by simply running the following **within** the main project:

```bash
git ws init --update
```

👉 As with `git ws clone`, without the `--update`, no dependencies will be fetched.

This command initializes the workspace and just needs to run once.
Changes to the manifest require an update operation (see next section) but no re-initialization.

#### Updating

Another important use case is keeping a workspace up-to-date. Let's say you pull in an update in the main repository, which in turn might cause changes in the manifest to be pulled in as well. Updating the existing workspace is as simple as

```bash
# Update the workspace (main and all dependent repositories):
git ws update

# Alternatively, run `git rebase` instead of `git pull` in dependencies:
git ws update --rebase
```

#### Non-Git Main Projects

`git ws` can leave the manifest version control to any other version control system (Subversion, VCS, DesignSync, etc.).
Just manage the manifest file `git-ws.toml` within the version control system of your choice.
Run `git ws init --update` or `git ws init --update -M path/to/git-ws.toml` in the intended workspace directory.

👉 As before, without the `--update`, no dependencies will be fetched.

**Inside** a git clone, `git ws init` uses the actual git project as the *main project* of the workspace.
**Outside** a git clone, `git ws init` initializes a workspace *without* a *main project*.

👉 There are just two drawbacks of a workspace without a main project:

1. `git ws tag` has no main project to tag and will fail. Please use [`git ws manifest freeze`](https://git-ws.readthedocs.io/en/latest/manual/command-line-interface/manifest.html#git-ws-manifest-freeze).
2. Relative URLs are not supported, as there is no URL to be relative to. Please use `remotes`:

```toml
[[remotes]]
name = "main"
url-base = "git@github.example.com:your-group"

[[dependencies]]
name = "dep1"
remote = "main"
```

## 👍 Getting Started

Please ensure a proper [installation](https://github.com/c0fec0de/git-ws#-installation).

Lets take a clone of an example project, which does not use ``git ws`` yet.

```bash
mkdir -p $HOME/Projects/Example-Workspace
cd $HOME/Projects/Example-Workspace
git clone https://github.com/c0fec0de/git-ws-example-one.git
# Cloning into 'git-ws-example-one'...
# remote: Enumerating objects: 3, done.
# remote: Counting objects: 100% (3/3), done.
# remote: Compressing objects: 100% (2/2), done.
# remote: Total 3 (delta 0), reused 0 (delta 0), pack-reused 0
# Receiving objects: 100% (3/3), done.
```

Now you should have one git clone in your workspace directory. Let's use it as *main project*.
At first, we need a manifest file ``git-ws.toml``.

```bash
cd git-ws-example-one
git ws manifest create
# Manifest 'git-ws.toml' created.
git add git-ws.toml
```

Now, we need to initialize the workspace

```bash
git ws init
# ===== . (MAIN 'git-ws-example-one') =====
# Workspace initialized at '..'.
# Please continue with:
#
#     git ws update
#
```

The parent directory became the ``git ws`` *workspace directory* .
The actual git clone is the *main project* now.
``git ws`` suggests to run ``git ws update``.
You can try, but nothing will happen yet, as the manifest is quite empty.

Let's add our first dependency ``git-ws-example-lib``, which is located on the same git server.
You can manually edit the manifest file ``git-ws.toml``, or you just run

```bash
git ws dep add git-ws-example-lib
```

Feel free to inspect the ``git-ws.toml`` file.
``git ws update`` will now apply the manifest changes and pull the new dependency:


```bash
git ws update
# ===== . (MAIN 'git-ws-example-one', revision='main') =====
# Pulling branch 'main'.
# Already up to date.
# ===== ../git-ws-example-lib ('git-ws-example-lib') =====
# git-ws WARNING Clone git-ws-example-lib has no revision!
# Cloning 'https://github.com/c0fec0de/git-ws-example-lib.git'.
# Cloning into '../git-ws-example-lib'...
# remote: Enumerating objects: 3, done.
# remote: Counting objects: 100% (3/3), done.
# remote: Compressing objects: 100% (2/2), done.
# remote: Total 3 (delta 0), reused 0 (delta 0), pack-reused 0
# Receiving objects: 100% (3/3), done.
```

Please note the warning:

```bash
# git-ws WARNING Clone git-ws-example-lib has no revision!
```

It is strongly recommended to specify a default revision for all dependencies. The command

```bash
git ws default revision main
```

solves that for you. Any successive ``git ws update`` is now free of this warning:

```
===== . (MAIN 'git-ws-example-one', revision='main') =====
Pulling branch 'main'.
Already up to date.
===== ../git-ws-example-lib ('git-ws-example-lib', revision='main') =====
Pulling branch 'main'.
Already up to date.
```

Now you can add, commit and push your changes to the ``git-ws.toml`` file.
Other colleagues should use now:

```bash
cd $HOME/Projects
git ws clone --update YOUR-REPO-URL

# OR

cd $HOME/Projects/Workspace
git clone YOUR-REPO-URL
cd <directory>
git ws init --update
```

``git ws status`` shows all changes within all git clones in the workspace.
``git ws add`` runs likewise the ``git add`` operation in the associated git clones.
Please see the next section for an overview of all commands.


## 🕹️ Cheat-Sheet

#### Initialization

| Command | Description |
| --- | --- |
| `git ws clone URL` | Clone git repository from `URL` as main repository and initialize Git Workspace |
| `git ws init` (**inside** a git clone) | Initialize Git Workspace at parent directory. Use current git clone as main repository |
| `git ws init` (**outside** a git clone) | Initialize Git Workspace at current directory. No main repository. |
| `git ws manifest create` | Create well documented, empty manifest |

#### Basic

| Command | Description |
| --- | --- |
| `git ws update` | Pull latest changes on main repository and all dependent repositories (clone them if needed) |
| `git ws update --rebase` | Same as above, but fetch and rebase instead of pull |
| `git ws status` | Run `git status` on all repositories (displayed paths include the actual clone path) |
| `git ws add FILES` | Run `git add FILE` on `FILES` in the corresponding repositories |
| `git ws reset FILES` | Run `git reset FILE` on `FILES` in the corresponding repositories. Undo `git add` |
| `git ws commit FILES -m MESSAGE` | Run `git commit FILE` on `FILES` in the corresponding repositories |
| `git ws commit -m MESSAGE` | Run `git commit` repositories with changes |
| `git ws checkout FILES` | Run `git checkout FILE` on `FILES` in the corresponding repositories |
| `git ws checkout` | Checkout git revision specified as in the manifest(s) (clone them if needed) |

#### Run Commands on all repositories

| Command | Description |
| --- | --- |
| `git ws push` | Run `git push` on all repositories (in reverse order) |
| `git ws fetch` | Run `git fetch` on all repositories |
| `git ws rebase` | Run `git rebase` on all repositories |
| `git ws pull` | Run `git pull` on all repositories |
| `git ws diff` | Run `git diff` on all repositories |
| `git ws git CMD` | Run `git CMD` on all repositories |
| `git ws foreach CMD` | Run `CMD` on all repositories |

#### Other

| Command | Description |
| --- | --- |
| `git ws manifest freeze`   | Print The Resolved Manifest With SHAs For All Project Revisions. |
| `git ws manifest path`     | Print Path to Main Manifest File. |
| `git ws manifest paths`    | Print Paths to ALL Manifest Files. |
| `git ws manifest resolve`  | Print The Manifest With All Projects And All Their Dependencies. |
| `git ws manifest upgrade`  | Update Manifest To Latest Version. |
| `git ws manifest validate` | Validate The Current Manifest, Exiting With An Error On Issues. |
| `git ws info main-path`      | Print Path to Main Git Clone. |
| `git ws info project-paths`  | Print Paths to all git clones. |
| `git ws info workspace-path` | Print Path to Workspace. |
| `git ws info dep-tree` | Print Dependency Tree. |
| `git ws info dep-tree --dot \| dot -Tpng > dep-tree.png` | Draw Dependency Diagramm (needs [graphviz](https://graphviz.org)) |


See the [command-line interface documentation](https://git-ws.readthedocs.io/en/latest/manual/command-line-interface/index.html) for any further details.


## 🐍 Python API

Git Workspace is written in Python. Besides the `git ws` command line tool, there is also an API which you can use to further automate workspace creation and maintenance. If you are interested, have a look into the [API documentation](https://git-ws.readthedocs.io/en/latest/api/gitws.html).


## 🤝 Alternatives

Before writing Git Workspace, we investigated several other existing tools in the hope they would fulfil our needs. In particular, we looked into the following tools and methodologies which are widely used to organize large projects:

- [`git submodules`](https://git-scm.com/book/en/v2/Git-Tools-Submodules).
- Google's [repo](https://gerrit.googlesource.com/git-repo/) tool.
- The [`west`](https://docs.zephyrproject.org/latest/develop/west/index.html) tool developed in the scope of [Zephyr](https://www.zephyrproject.org/).
- Leaving the pure `git` domain, one can also use a package manager like [`conan`](https://conan.io/).
- And lastly, there are also approaches to still pack everything into a large, so called *monorepo*.

Unfortunately, none of the tools we tested really satisfied us. But hey, as we are developers - *why not start our own tool for the purpose?*

And that's what we did - Git Workspace is our tool for managing a large workspace consisting of several smaller `git` projects. Here is how it compares to the other tools we evaluated:


|                           | `git submodules` | `repo` | `west` | *Monorepos* | `git ws` |
| ------------------------- | ---------------- | ------ | ------ | ----------- | --------- |
| Reusable Components       | ✅               | ✅     | ✅     | ➖          | ✅        |
| Ease of Use               | ➖               | ✅     | ✅     | ✅          | ✅        |
| Editable Components       | ➖               | ✅     | ➖     | ✅          | ✅        |
| Freezing Configurations   | ✅               | ✅     | ✅     | ✅          | ✅        |
| Transitive Dependencies   | ➖               | ➖     | ✅     | ➖          | ✅        |
| Relative Dependency Paths | ✅               | ✅     | ➖     | ➖          | ✅        |
| Branches as dependencies  | ➖               | ✅     | ✅     | ➖          | ✅        |

👉 Please note that our view on the various features might be biased. As we did, always look at all the options available to you before deciding on one tool or the other. While the other tools in comparison did not model what we needed for our workflow, they might just be what you are looking for.

If you want to learn more, have a look into [Why We Started Git Workspace](https://git-ws.readthedocs.io/en/latest/manual/why.html).

