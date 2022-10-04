# Multi Repository Management Tool

Software (and even more hardware) projects can become quite large. Organizing such a large project and ensuring a smooth and efficient development flow while - ideally - making the individual parts of such a project easily reusable can be a real challenge.

When working with `git`, there already are some tools and workflows available that deal with how to organize large projects, among them are:

- [`git submodules`](https://git-scm.com/book/en/v2/Git-Tools-Submodules).
- Google's [repo](https://gerrit.googlesource.com/git-repo/) tool.
- The [`west`](https://docs.zephyrproject.org/latest/develop/west/index.html) tool developed in the scope of [Zephyr](https://www.zephyrproject.org/).
- Leaving the pure `git` domain, one can also use a package manager like [`conan`](https://conan.io/).
- And lastly, there are also approaches to still pack everything into a large so called *monorepo*.

When we started working on a new project, we looked for a suitable solution for dealing with the problems we saw ahead of us, hoping that there would be some existing tools that exactly modelled the workflow we envisioned. Unfortunately, none of the tools we tested really satisfied us.

But hey, as we are developers - *why not starting our own tool for the purpose?*

And that's what we did - AnyRepo is a our tool for managing a large workspace consisting of several smaller `git` projects. Here is how it compares to the other tools we evaluated:


|                           | `git submodules` | `repo` | `west` | *Monorepos* | *AnyRepo* |
| ------------------------- | ---------------- | ------ | ------ | ----------- | --------- |
| Reusable Components       | ✅               | ✅     | ✅     |             | ✅        |
| Ease of Use               |                  | ✅     | ✅     | ✅          | ✅        |
| Editable Components       |                  | ✅     |        | ✅          | ✅        |
| Freezing Configurations   | ✅               | ✅     | ✅     | ✅          | ✅        |
| Transitive Dependencies   |                  |        | ✅     |             | ✅        |
| Relative Dependency Paths | ✅               | ✅     |        |             | ✅        |

👉 Please note that our view on the various features might be biased. As we did, always look at all the options available to you before deciding for one tool or the other. While the other tools in comparison did not model what we needed for our workflow, they might just be what you are looking for.

- [ ] We should add a link here to the documentation, where the same table can be found (plus some more details).


# Installation

AnyRepo is written in Python and - as usual - installing it is pretty easy:

```python
pip install anyrepo
```

And that's it! Ideally, if your project also uses Python, we recommend adding AnyRepo as a dependency to it as well, so that you can track the exact version of it together with your other dependencies.


# Usage

AnyRepo comes with a command line client called `anyrepo` - this is what you will be using most of the time.

Let's assume we have a project called `MyProject`, which requires a library `MyLib` that is maintained in another `git` repository. In order to use this project with AnyRepo, `MyProject` needs to provide a so called *manifest*. An AnyRepo manifest is a simple [TOML](https://toml.io/) file - by default called `anyrepo.toml` in the project's root folder - which defines the dependencies a project has as well as some other meta information. A minimal manifest for our project could look like this:

```toml
[[dependencies]]
name = "MyLib"
url = "git@github.com:example/mylib.git"
revision = "v2.3.4"
path = "my_lib"
```

If `MyProject` and `MyLib` are stored on the same server, than the manifest can even be simpler by using relative paths:

```toml
[[dependencies]]
name = "MyLib"
url = "../mylib.git"
revision = "v2.3.4"
path = "my_lib"
```

Relative paths are useful as they allow to use the same protocol for the main repository as well as any of its dependencies.

To build a workspace from a project prepared like that, simply clone it via `anyrepo`:

```bash
cd $HOME/Projects
mkdir my_app_workspace
cd my_app_workspace
anyrepo clone git@github.com:example/myapp.git
```

This will clone the app repository and also the library side-by-side:

```bash
ls
# Should print something like
# myapp mylib
```

If we include also hidden files and folders in the listing, you'll notice a special `.anyrepo` folder:

```bash
ls -a
# Should print something like
# . .. .anyrepo myapp mylib
```
