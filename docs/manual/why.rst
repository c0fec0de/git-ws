Why We Started Git Workspace
============================

Developing large projects can be a real challenge. There are lots of aspects that make the daily work on huge projects rather difficult. One - among many! - aspects is how to organize the structure of a project, i.e. how to break it down into smaller, better maintainable components and reuse them.


Our Requirements
----------------

Let's start by checking what we *wanted to achieve* for our project:

- Modularity: We wanted to be able to easily reuse parts of the project, so for new projects in the future, we would simply be able to take some of the (basic) components and include them as-is in the new project.
- Ease of use: A system for composing a larger project from smaller components should be easy to use and understand - not everyone is an expert in configuration management, and there shall be no reason for them to become one.
- Support for working in parallel on several components: Especially during the *hot* development phase, not only the *main* project needs to be changed, but also the other components it is made of need to be edited all the time.
- Support for freezing a configuration: The other way round - once a certain version of the project is released, we wanted to be able to record the exact version of all the involved components so it is easy to reconstruct the source base a particular binary release has been built from.
- Dependency management: Once we start breaking down a project into smaller components, these components in turn might also have own dependencies. We wanted to be able to have this kind of transitive dependencies.
- Relative Dependency Paths: On top, we wanted to be able to use relative paths for dependencies. This is important when getting the main project from the server using varying URLs (e.g. `https` vs `ssh` of when some users might use a local mirror of the main `git` server).


Evaluation of Existing Tools
----------------------------

As everyone, we were lazy - in terms of development, this usually is a good thing!

So we checked if there were existing solutions that fit our needs. If there were tools fulfilling what we wanted, that it would be the easiest path just using one of them, right? So here is what we digged out:


`git submodules`
++++++++++++++++

One of the first things that come to mind - and which we already used in other tools - were `git submodules <https://git-scm.com/book/en/v2/Git-Tools-Submodules>`_. `git submodules` have a lot of good things about them, that make them a strong first contender for building larger projects from several smaller components:

- They are integrated into `git` since `v1.5` - so they should be available defacto everywhere `git` is used as well.
- Since `submodules` are by default included with a specific commit, each version of the *parent* repository has a well-defined configuration associated with it. Restoring a past configuration of the project hence is really easy.
- Tools and platforms such as GitHub and GitLab have some support for `submodules` and e.g. automatically link to the referenced sub-repo in their web interface.

Seems good, right? However, we found the `submodule` approach also to bear some downsides as well:

- Steep learning curve: Developers have to be aware how `submodules` work - especially in relation to `git`.
- Especially merging can be tricky if conflicts in `submodule` revisions need to be resolved.

So, the obvious question was: Are there better alternatives available?


Google's `repo` Tool
++++++++++++++++++++

One other well-known tool for building workspaces from multiple `git` repositories is Google's `repo <https://gerrit.googlesource.com/git-repo/>`_ tool. It is a relatively simple tool written in Python which - based on a *manifest* assembles a workspace.

`repo` has some nice benefits:

- It makes tracking *synchronized* branches across repositories easy.
- In addition, it provides built-in commands for creating new branches across the entire project.

However, `repo` also comes with its own downsides as well:

- It needs an extra repository where the *manifest* files are stored.

At least for us, `repo` didn't seem to be the best choice to get the job done, so we had to venture forth...


Zephyr's `west` Tool
++++++++++++++++++++

This is another interesting option, and - on paper - it made a really great first impression!  `west <https://docs.zephyrproject.org/latest/develop/west/index.html>`_ is a tool developed in the scope of the `Zephyr <https://www.zephyrproject.org/>`_ project. `west` promised to solve a lot of our requirements and also regarding their way of structuring a workspace fit quite nicely with what we had in mind:

- `west` uses a *manifest* which is stored in the main project to include further dependencies.
- It explicitly supports including specific revisions of a project - so including a project at a specific tag is possible without issues.
- It also has some integration for `git submodules`, so the two of them can also be mixed (which is a nice, future option).
- A manifest can *import* another one from the sub-projects. That way, `west` implements some kind of poor-man's dependency management.
- There is an option to create a *frozen* manifest where all the included projects are fixed at a particular revision - this is important when creating a release to have a well-defined configuration of the project.

The list of advantages is quite long and `west` really looked like a great choice at first. However, after giving it a try, we noticed downsides as well:

- Whenever a `west update` is run, the tool will check out the sub-projects at a *detached head* state instead of a branch. That makes it difficult to really work in parallel on a main project and one or more of its dependencies - something we really need.
- In addition, `west` has no option to include other projects using relative paths. This however is important if the main project can be accessed using various different URLs (e.g. when cloning via both `ssh` and `https` is possible or when a `git` mirror server is used).
- Another thing we didn't like (but this is really something one could ignore): `west` can actually do way more than managing workspaces - there are e.g. options for adding new commands to it by providing additional information in the manifest files. In our opinion, its better to follow the UNIX philosophy here: A tool should do only one thing and it should do this thing in a great way.

So, unfortunately, `west` was also out...


Using A Package Manager
+++++++++++++++++++++++

Another option we considered was using a package manager like `conan <https://conan.io/>`_. In this scenario, instead of building a larger workspace consisting of multiple `git` repositories, we would break the project down into its components and consider every component as a standalone project which creates a (possibly *binary*) package as its output.

If a project requires other components, it would consume their released packages instead of including them in source form.

This approach has one obvious advantage: Reduced CI/CD run-times. Especially if there are parts of the project that rarely change, we avoid building them all over again for each push we make to the `git` server.

However, this approach as well has its downsides:

- First of all, not all projects have a structure where individual parts can be *compiled* on their own. A notable example is *hardware design*. In that case, we don't have any performance benefits.
- And second, a package based workflow does not necessarily make working on several components in parallel easy. While `conan` has some features for making a single package editable within a larger workspace, this feature is still not quite easy to use and can be confusing at times.


Monorepos
+++++++++

Lastly, we also revisited the option putting everything in one large repository - this approach is often coined *Monorepo*. Nowadays, there are some tweaks and tricks available to make working with such a setup easier and at least the project configuration would be really easy (as one commit in the main project fixes all the files that are there). But obviously, this approach had too many downsides:

- The single repository grows very large - operations like cloning will then take ages.
- It's all or nothing: Either a developer has access to the repo or not. There is no *in between*.
- And most obviously, there is no simple way to reuse parts of the project. Besides simple copy&paste, there are some neat tricks `git` can play here, but this really is nothing for a daily workflow.

So, it seemed we had to get our hands dirty...


The Birth of Git Workspace
--------------------------

After doing our homework and checking if we simply can use another existing tool, we came to the conclusion that we had to invest some development effort and bring up our own tool. Git Workspace was born!

If you carefully study the results of our research given above, you might find that we actually were pretty fond of `west`. So it comes to no surprise that Git Workspace is built in a similar way and even tries to be compatible with `west` as far as possible. In fact, the manifest files of `west` are to some degree compatible with Git Workspace and we try to behave similarly where possible. However, we also want to close the gap and implement the features we think are missing in `west`.


Comparison Matrix
-----------------

So, long story short: Here is a matrix of features vs the different tools we evaluated plus Git Workspace itself.

.. list-table:: Comparison
    :widths: 1 1 1 1 1 1
    :header-rows: 1

    * -
      - `git submodules`
      - `repo`
      - `west`
      - Monorepo
      - `git ws`
    * - Reusable Components
      - |:white_check_mark:|
      - |:white_check_mark:|
      - |:white_check_mark:|
      - |:heavy_minus_sign:|
      - |:white_check_mark:|
    * - Ease of Use
      - |:heavy_minus_sign:|
      - |:white_check_mark:|
      - |:white_check_mark:|
      - |:white_check_mark:|
      - |:white_check_mark:|
    * - Editable Components
      - |:heavy_minus_sign:| [#]_
      - |:white_check_mark:|
      - |:heavy_minus_sign:|
      - |:white_check_mark:|
      - |:white_check_mark:|
    * - Freezing Configurations
      - |:white_check_mark:|
      - |:white_check_mark:|
      - |:white_check_mark:|
      - |:white_check_mark:|
      - |:white_check_mark:|
    * - Transitive Dependencies
      - |:heavy_minus_sign:| [#]_
      - |:heavy_minus_sign:|
      - |:white_check_mark:|
      - |:heavy_minus_sign:|
      - |:white_check_mark:|
    * - Relative Dependency Paths
      - |:white_check_mark:|
      - |:white_check_mark:|
      - |:heavy_minus_sign:|
      - |:heavy_minus_sign:|
      - |:white_check_mark:|

.. [#] `git submodules` tend to check out repositories at a fixed revision (which is their job). However, this means that each `git submodule update -\-recursive` would then cause the submodules to be switched to a *read-only* state, where the user then has to first switch back to a branch to continue editing. This is basically the same behavior that `west` implements.
.. [#] `git submodules` can of course recurse - and via this, there is some *kind* of transitive dependencies. However, if there are two or more components that include the same transitive dependency, than that transitive dependency will be included several times in the workspace - and potentially checked out at different versions.

Please note that we don't claim that Git Workspace is the best choice for everyone: As usual, when looking for a tool, do your homework and make up your mind about *your* requirements and check them against the various available tools. Git Workspace might just be right for you - but chances are that depending on your concrete workflow one of the other tools or approaches simply works better.
