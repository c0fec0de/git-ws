.. _group_filtering:

Group Filtering
===============

The code function of ``git-ws`` is to allow having ``git`` based projects to have dependencies that they can pull in easily, stashing everything together within a large workspace.

These workspaces quickly can grow large, especially when dependencies bring in transitive dependencies. To allow bringing down the size of workspaces, *group filtering* can be used. But, *what is* a group filter?

To understand this, let's step back and have a look at the dependencies a project might have:

Some of them will be *hard* dependencies, e.g. libraries that a project depends on that are absolutely needed for the project in question to be able to function.

On the other side, there are *soft* dependencies. These dependencies are not needed for the project to work. These could, for example, be dependencies used during testing the project. When a project is built, it needs to be tested as well in order to guarantee stability and functionality. But: Once tested (and released), when the project is used within another one as a dependency, then these tests don't necessarily need to be run.

To make this easier to grasp, let's consider the following scenario: We have a library ``PrintLib``, that has a dependency to another library called ``IOLib`` plus - for testing - a dependency towards ``SimpleUT`` for writing unit tests:

.. code-block::

    PrintLib
    ├── IOLib
    └── SimpleUT

Now, let's say we write a simple calculator tool, where we want to use ``PrintLib``. The dependency tree in this case would look like this:

.. code-block::

    Calculator
    └── PrintLib
        ├── IOLib
        └── SimpleUT

With this, the final workspace created would have four sub-folders:

* Calculator
* ``PrintLib``
* ``IOLib``
* ``SimpleUT``

But: What if for Calculator we don't want to use ``SimpleUT``? By default, we would still get it, even if we never run the unit tests of ``PrintLib``. This is where group filtering can help. In the manifest of ``PrintLib``, we can put ``SimpleUT`` into a group - let's call it ``dev``:

.. code-block:: toml

    [[dependencies]]
    name = "IOLib"
    revision = "v42.0"

    [[dependencies]]
    name = "SimpleUT"
    revision = "v3.2.0"
    # Put this dependency into a group called "dev":
    groups = ["dev"]

Without further ado, what would happen now? It's as simple as that:

* When we create a workspace for ``PrintLib``, all of its dependencies will be included.
* But when creating a workspace for our Calculator app, the ``SimpleUT`` dependency would *not* get installed!

Perfect! So, for simple cases, these simple rules apply:

1. Direct dependencies of a project will always be pulled into the workspace.
2. All transitive dependencies that are in any group will be skipped.

With these simple rules, creating efficient modules is quite easy: Whatever is a strict dependency should get no group assigned. Everything *optional* in turn could get assigned any group (or groups). You can use any group you like for this, e.g. you could have a group used for unit testing, another one for linters and code formatters used in your project, and so on.


Enabling Groups
---------------

So now you know how to create efficient projects which hide parts of their dependencies to contribute to smaller workspaces. But, what *if* you want to install groups that got deselected due to the group filtering? There are two ways to do so.


Filtering Groups on the Command Line
++++++++++++++++++++++++++++++++++++

A lot of the commands of ``git-ws`` tool allow you to specify *group filters* via the ``--group-filter`` (or ``-G``) option:

.. code-block:: bash

    git ws clone -G +dev https://example.com/Calculator.git

This would create a workspace for the Calculator project, including also transitive dependencies that are in the ``dev`` group.

When the ``--group-filter`` option is used during the ``git ws init`` or ``git ws clone`` operations, the filter is stored in the workspace settings (and can be updated using the ``git ws config set`` command). The option can be used multiple times to specify additional groups. And, you are not limited to enabling groups. A group filter string is structured like this:

.. code-block::

    (+|-) group [ @ path]

So in more prose:

* A group filter expression always starts with a ``+`` (to select) or a ``-`` (to deselect) a group.
* It is followed by a group name, where group names are valid identifier names.
* Optionally, there can be an ``@`` character, followed by a path. In this case, the filter is applied only to the project specified by the path. 


Here are some examples:

* As shown above, a group filter of ``+dev`` would enable the group of development dependencies also for transitive dependencies.
* On the other side, we could disable dependencies e.g. for generating documentation via ``-doc``. If explicitly specified, this would exclude dependencies of the main project.
* Finally, we could selectively select groups, e.g. like ``+network@PrintLib``. This would enable the ``network`` group of our ``PrintLib`` dependency (which could e.g. be used to pull in optional libraries that allow it to provide input and output via network connections).


Filtering Groups Via The Manifest
+++++++++++++++++++++++++++++++++

Sometimes, controlling groups via the command line might not be convenient. Consider the last example from the previous section: Assuming the ``PrintLib`` library has optional dependencies for networking input/output, if we mark them as optional by putting them into a ``network`` group, they would - by default - not be installed into a workspace of our Calculator app. But what if we actually want this dependency in most cases? Telling everyone to use a special, non-standard command for initializing a workspace is certainly a bad idea. In this case, we can specify the appropriate dependency directly in the manifest of our Calculator app:

.. code-block::  toml

    group-filters = ["+network@PrintLib"]

With this, everyone would - by default - also get the networking dependencies of ``PrintLib`` in their workspace (unless they override the group filter on the command line).

