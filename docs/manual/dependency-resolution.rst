Dependency Resolution
=====================

One of the core tasks of ``git ws`` is to allow describing dependencies of a particular project to other (possibly related) projects (which are all maintained as ``git`` repositories) and assemble them in a single workspace. But, how exactly does this *dependency resolution* procedure work? This chapter describes the core mechanisms that ``git ws`` employs to get its job done.


The Manifest
------------

When working with ``git ws``, one of the core ingredients used is the :ref:`manifest <manifest_manual>`. Besides some informational meta information, one of the tasks of a manifest is to specify dependencies to other projects. Consider a project ``HelloWorld``, which in turn depends on a library ``FooLib`` it needs to work. The manifest of the ``HelloWorld`` project could look like that:

.. code-block:: toml

    [[dependencies]]
    name = "FooLib"
    revision = "v2.3.4"

In this case, the assumption is that the projects ``HelloWorld`` and ``FooLib`` are stored both side-by-side on the same server. In addition, ``HelloWorld`` pulls in a specific version - ``v2.3.4`` of the library. Dependency resolution in this case is pretty much straightforward: ``git ws`` starts with the :ref:`main project <nomenclature_main_project>` and reads its manifest. That manifest points to ``FooLib``, so the dependency tree would look like this:

.. code-block::

    HelloWorld
    └── FooLib (revision='v2.3.4')

And the resulting (very simplified) workspace created for that project would look like this:

.. code-block::

    HelloWorld
    ├── FooLib
    │   └── git-ws.toml
    └── HelloWorld
        └── git-ws.toml


So far, so good. However, most projects are not as simple as that.


Transitive Dependencies
-----------------------

In the very simple example given above, we assumed that the dependencies of the main project in turn are simple and self-contained. However, more often than not this is *not* the case. So, what if the ``FooLib`` needed by ``HelloWorld`` needs yet another library - ``BarLib`` - to work? ``git ws`` has us covered here by allowing dependencies to be *transitive*: If a project pulled in as a dependency also has a valid manifest and - in it - specifies further dependencies, these dependencies are pulled in as well and are made a part of the resulting workspace! Assume that a newer version of ``FooLib`` has the following manifest:

.. code-block:: toml

    [[dependencies]]
    name = "BarLib"
    revision = "v42.0"

The resulting dependency tree now would rather look like this:

.. code-block::

    HelloWorld
    └── FooLib (revision='v2.4.0')
        └── BarLib (revision='v42.0')

And the (simplified) workspace would look like this:

.. code-block::

    HelloWorld
    ├── BarLib
    │   └── README.md
    ├── FooLib
    │   └── git-ws.toml
    └── HelloWorld
        └── git-ws.toml


The First Wins Rule
-------------------

In an ideal world, a main project and all of its dependencies - direct as well as transitive ones - would form a `tree structure <https://en.wikipedia.org/wiki/Tree_(graph_theory)>`_. However, often it is not as simple as that. Consider the following:

We need to extend ``HelloWorld`` again, adding a dependency to yet another library ``BazLib``:


.. code-block:: toml

    [[dependencies]]
    name = "FooLib"
    revision = "v2.4.0"

    [[dependencies]]
    name = "BazLib"
    revision = "v5.6.7"

That library also specifies ``BarLib`` as a dependency, but at another revision:

.. code-block:: toml

    [[dependencies]]
    name = "BarLib"
    revision = "v44.0"

So, what will happen in this scenario? Let's check the dependency tree:

.. code-block::

    HelloWorld
    ├── FooLib (revision='v2.4.0')
    │   └── BarLib (revision='v42.0')
    └── BazLib (revision='v5.6.7')
        └── BarLib (revision='v44.0')*

The tree looks somehow as expected, however, note that the second occurrence of ``BarLib`` is annotated with a ``*``. This means that it is not used! We can easily prove this showing the checked out revisions of all projects in the workspace:

.. code-block:: bash

    git ws git describe -- --all
    # ===== ../HelloWorld (MAIN 'HelloWorld', revision='main') =====
    # heads/main
    # ===== ../FooLib ('FooLib', revision='v2.4.0') =====
    # tags/v2.4.0
    # ===== ../BazLib ('BazLib', revision='v5.6.7') =====
    # tags/v5.6.7
    # ===== . ('BarLib', revision='v42.0') =====
    # tags/v42.0

This is because of the *First Wins* rule ``git ws`` uses for resolving (conflicting) dependencies: If there are two dependencies specified to be mounted to the same path but referring to different revisions, the tool will pick whichever revision has been specified first. Manifests are evaluated via a *breadth first* search over the tree structure, where the dependencies of one manifest are evaluated in order as seen in the manifest. In the example, this means:

* Evaluation starts at the ``HelloWorld`` project.

  * First, we find ``FooLib`` at ``v2.4.0`` and add it to the workspace. As this project has a manifest on its own, we start evaluating it.

  * Next at this level, we find ``BazLib`` at ``v5.6.7``, which we also add.

  * This concludes this manifest, so we continue checking the dependencies of our first level dependencies:

    * The first (and only) dependency we find for ``FooLib`` is ``BarLib`` at revision ``v42.0``, so we add it to the workspace.

    * Next, we check ``BarLib`` again, this time at ``v44.0``, but as it already has been added to the workspace, we skip it.


This leads us to an interesting pattern that can be used in ``git ws``.


Dependency Overriding
---------------------

If you closely check the example again, you might notice something: ``HelloWorld`` pulls in both ``FooLib`` and ``BazLib``. Both of them require ``BarLib`` to work, but at different revisions. By the order of dependencies in the main project, we see ``v42.0`` of ``BarLib`` first, but ``BazLib`` explicitly needs it at ``v44.0``. Usually, libraries (or programs) tend to be *forward compatible*, i.e. using ``FooLib`` with a newer version of ``BarLib`` would work. But in the workspace that will be constructed, we end up with a version of ``BazLib`` that will need to build and run against an older version of ``BarLib`` than expected. This - in turn - might fail quite quickly on us.

However, with the *First Win Rules* at hand, we can easily *fix* such a workspace by explicitly pulling in a dependency directly in the manifest of the main project:

.. code-block:: toml

    [[dependencies]]
    name = "FooLib"
    revision = "v2.4.0"

    [[dependencies]]
    name = "BazLib"
    revision = "v5.6.7"

    [[dependencies]]
    name = "BarLib"
    revision = "v44.0"

By putting the dependency towards ``BarLib`` directly into the manifest of the main project, we can pin its version to whatever is needed - in our case, we can explicitly set it to ``v44.0``, which should work for both ``FooLib`` and ``BarLib``.

An extreme form of this approach is when using :ref:`manifest freezing <git_ws_manifest_freeze>`: Creating a frozen manifest basically creates a manifest with all pulled in dependencies resolved in one flat list with their revision set to a fixed version. This will cause ``git ws`` to ignore any of the dependencies coming in transitively to be ignored (as they already are specified in the manifest of the main project).
