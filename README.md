[![pypi-version](https://badge.fury.io/py/anyrepo.svg)](https://badge.fury.io/py/anyrepo)
[![pypi-downloads](https://img.shields.io/pypi/dm/anyrepo.svg?label=pypi%20downloads)](https://pypi.python.org/pypi/anyrepo)
[![doc](https://readthedocs.org/projects/anyrepo/badge/?version=latest)](https://anyrepo.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/c0fec0de/anyrepo/badge.svg?branch=main)](https://coveralls.io/github/c0fec0de/anyrepo?branch=main)
[![python-versions](https://img.shields.io/pypi/pyversions/anyrepo.svg)](https://pypi.python.org/pypi/anyrepo)
[![pylint](https://img.shields.io/badge/linter-pylint-%231674b1?style=flat)](https://www.pylint.org/)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Multi Repository Management Tool

* [Installation](#installation)
* [Usage](#usage)
* [Cheat-Sheet](#cheatsheet)
* [Python API](#api)
* [Alternatives](#alternatives)

AnyRepo is a lightweight tool for creating and managing *workspaces* consisting of several interdependent `git` repositories. Starting from a *main repository*, AnyRepo discovers dependencies specified in a *manifest file*, fetching any specified required repositories and assembling them into a single workspace.

![Workspace](https://github.com/c0fec0de/anyrepo/raw/main/docs/images/workspace.png)

👉 You can read more about the used [nomenclature](https://anyrepo.readthedocs.io/en/latest/manual/nomenclature.html) in the [documentation](https://anyrepo.readthedocs.io/en/latest/index.html).


<a name="installation"/>

# 📦 Installation

AnyRepo is written in Python and - as usual - installing it is pretty easy:

```bash
pip install anyrepo
```

And that's it! Ideally, if your project also uses Python, we recommend adding AnyRepo as a dependency to it as well, so that you can track the exact version of it together with your other dependencies. For example, if you use `poetry`, add it by running

```bash
# Add AnyRepo as development dependency:
poetry add --group dev anyrepo
```


<a name="usage"/>

# 📔 Usage

AnyRepo comes with a command line client called `anyrepo` - this is what you will be using most of the time.

Let's assume we have a project called `myapp`, which requires a library `mylib` that is maintained in another `git` repository. In order to use this project with AnyRepo, `myapp` needs to provide a so called *manifest*. An AnyRepo manifest is a simple [TOML](https://toml.io/) file - by default called `anyrepo.toml` in the project's root folder - which defines the dependencies a project has as well as some other meta information. A minimal manifest for our project could look like this:

```toml
[[dependencies]]
name = "mylib"
url = "git@github.com:example/mylib.git"
revision = "v2.3.4"
```

If `myapp` and `mylib` are stored on the same server (side-by-side), than the manifest can even be simpler:

```toml
[[dependencies]]
name = "mylib"
revision = "v2.3.4"
```

The project will be searched via a relative path (which is either `../mylib` or `../mylib.git` depending on the main repository's URL). Relative paths are in general useful as they allow to use the same protocol for the main repository as well as any of its dependencies.

To build a workspace from a project prepared like that, simply clone it via `anyrepo`:

```bash
cd $HOME/Projects
mkdir my_app_workspace
cd my_app_workspace
anyrepo clone --update git@github.com:example/myapp.git
```

👉 Without the `--update` option, only the main repository will be fetched.

The above will clone the app repository and also the library side-by-side:

```bash
ls -a
# Should print something like
# . .. .anyrepo myapp mylib
```

As you can see, besides the two repositories we wanted, there is also a hidden `.anyrepo` folder where the tool stores the needed configuration data.

Sometimes there are use cases where using `anyrepo clone` cannot be used. For example, when a CI/CD system creates the initial clone of the main repository, you may need a way to fetch the remaining projects. This can be done by simply running the following within the main project:

```bash
anyrepo init --update
```

👉 As with `anyrepo clone`, without the `--update`, no dependencies will be fetched.

Another important use case is keeping a workspace up-to-date. Lets say you pull in an update in the main repository, which in turn might cause changes in the manifest to be pulled in as well. Updating the existing workspace is as simple as

```bash
# Update the workspace (main and all dependent repositories):
anyrepo update

# Alternatively, run `git rebase` instead of `git pull` in dependencies:
anyrepo update --rebase
```
<a name="cheatsheet"/>

## Cheat-Sheet

| Command | Description |
| --- | --- |
| `anyrepo clone URL` | Clone git repository from `URL` as main repository and initialize AnyRepo workspace |
| `anyrepo init` | Initialize AnyRepo workspace. Use existing git clone as main repository |
| `anyrepo manifest create` | Create well documented, empty manifest |
| `anyrepo update` | Pull latest changes on main repository and all dependent repositories (and clone them if needed) |
| `anyrepo update --rebase` | Same as above, but fetch and rebase instead |
| `anyrepo status` | Run `git status` on all repositories (displayed paths include the actual clone path) |
| `anyrepo add FILES` | Run `git add FILE` on `FILES` in the corresponding repositories |
| `anyrepo reset FILES` | Run `git reset FILE` on `FILES` in the corresponding repositories. Undo `git add` |
| `anyrepo commit FILES -m MESSAGE` | Run `git commit FILE` on `FILES` in the corresponding repositories |
| `anyrepo checkout FILES` | Run `git checkout FILE` on `FILES` in the corresponding repositories |
| `anyrepo checkout` | Checkout git revision specified as specified in the manifests |
| `anyrepo push` | Run `git push` on all repositories |
| `anyrepo fetch` | Run `git fetch` on all repositories |
| `anyrepo rebase` | Run `git rebase` on all repositories |
| `anyrepo pull` | Run `git pull` on all repositories |
| `anyrepo diff` | Run `git diff` on all repositories |
| `anyrepo git CMD` | Run `git CMD` on all repositories |
| `anyrepo foreach CMD` | Run `CMD` on all repositories |
| `anyrepo manifest freeze` | Print The Resolved Manifest With SHAs For All Project Revisions |
| `anyrepo manifest resolve` | Print The Manifest With All Imports Resolved |

<a name="api"/>

## 🐍 Python API

AnyRepo is written in Python. Besides the `anyrepo` command line tool, there is also an API which you can use to further automate workspace creation and maintenance. If you are interested, have a look into the [API documentation](https://anyrepo.readthedocs.io/en/latest/api/anyrepo.html).


<a name="alternatives"/>

## 🤝 Alternatives

Before writing AnyRepo, we investigates several other existing tools in the hope they would fulfil out needs. In particular, we looked into the following tools and methodologies which are widely used to organize large projects:

- [`git submodules`](https://git-scm.com/book/en/v2/Git-Tools-Submodules).
- Google's [repo](https://gerrit.googlesource.com/git-repo/) tool.
- The [`west`](https://docs.zephyrproject.org/latest/develop/west/index.html) tool developed in the scope of [Zephyr](https://www.zephyrproject.org/).
- Leaving the pure `git` domain, one can also use a package manager like [`conan`](https://conan.io/).
- And lastly, there are also approaches to still pack everything into a large so called *monorepo*.

Unfortunately, none of the tools we tested really satisfied us. But hey, as we are developers - *why not starting our own tool for the purpose?*

And that's what we did - AnyRepo is a our tool for managing a large workspace consisting of several smaller `git` projects. Here is how it compares to the other tools we evaluated:


|                           | `git submodules` | `repo` | `west` | *Monorepos* | *AnyRepo* |
| ------------------------- | ---------------- | ------ | ------ | ----------- | --------- |
| Reusable Components       | ✅               | ✅     | ✅     | ➖          | ✅        |
| Ease of Use               | ➖               | ✅     | ✅     | ✅          | ✅        |
| Editable Components       | ➖               | ✅     | ➖     | ✅          | ✅        |
| Freezing Configurations   | ✅               | ✅     | ✅     | ✅          | ✅        |
| Transitive Dependencies   | ➖               | ➖     | ✅     | ➖          | ✅        |
| Relative Dependency Paths | ✅               | ✅     | ➖     | ➖          | ✅        |

👉 Please note that our view on the various features might be biased. As we did, always look at all the options available to you before deciding for one tool or the other. While the other tools in comparison did not model what we needed for our workflow, they might just be what you are looking for.

If you want to learn more, have a look into the [documentation](https://anyrepo.readthedocs.io/en/latest/manual/why.html).

