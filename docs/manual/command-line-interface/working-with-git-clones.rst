Working With ``git`` Clones
===========================

:ref:`Workspaces <nomenclature_workspace>` consist of one or more ``git`` clones. ``git ws`` provides several commands that can be used to conveniently work with these clones in the scope of the overall project.

.. _git_ws_foreach:

``git ws foreach``
------------------

Run a command once for every ``git`` clone in a workspace.

.. literalinclude:: ../../static/cli.foreach.txt
   :language: text

This command is useful to run a shell command once for each ``git`` clone in a workspace. For example, the following would run a ``git status`` in all clones:

.. code-block:: bash

    git ws foreach git status

- The command can be fine tuned similarly to the :ref:`git_ws_update` command using the ``--project``, ``--manifest`` and ``--group-filter`` options.
- By default, the projects are traversed from the main project down to its dependencies. By using the ``--reverse`` option, the order in which the projects are visited are inverted.


.. _git_ws_git:

``git ws git``
--------------

Run a ``git`` command for all clones within a workspace.

.. literalinclude:: ../../static/cli.git.txt
   :language: text

This is similar to the :ref:`git_ws_foreach`, but automatically calls ``git``. It is basically a shorthand for ``git ws foreach git``.

.. code-block:: bash

    # Run a git status in all projects:
    git ws git status

    # This is the equivalent for:
    git ws foreach git status


.. _git_ws_pull:

``git ws pull``
---------------

Run a ``git pull`` in all clones within a workspace.

.. literalinclude:: ../../static/cli.pull.txt
   :language: text


.. _git_ws_push:

``git ws push``
---------------

Run a ``git push`` in all clones within a workspace.

.. literalinclude:: ../../static/cli.push.txt
   :language: text


.. _git_ws_rebase:

``git ws rebase``
-----------------

Run a ``git rebase`` in all clones within a workspace.

.. literalinclude:: ../../static/cli.rebase.txt
   :language: text


.. _git_ws_fetch:

``git ws fetch``
----------------

Run a ``git fetch`` in all clones within a workspace.

.. literalinclude:: ../../static/cli.fetch.txt
   :language: text


.. _git_ws_diff:

``git ws diff``
---------------

Run a ``git diff`` in all clones within a workspace.

.. literalinclude:: ../../static/cli.diff.txt
   :language: text

This command can be used to show the differences in clones in all clones within a workspace. Note that this command is not equivalent to calling ``git ws git diff``: The command will show paths relative to the workspace folder. This is useful if you want to e.g. create a patch for an entire workspace:

.. code-block:: bash

    cd Projects/my-workspace
    git ws diff > changes.patch

    cd ../another-workspace-version
    patch -p1 < ../my-workspace/changes.diff


.. _git_ws_checkout:

``git ws checkout``
-------------------

Check out all projects to the revision specified in the manifest.

.. literalinclude:: ../../static/cli.checkout.txt
   :language: text

This command can be used to check out all dependencies to the revision which has been specified in the manifest file. This can be useful if some repositories have been manually checked out to other revisions, as the command will ensure all repositories are on their well defined version.

.. code-block:: bash

    cd Projects/my-workspace

    # Switch some repository to a new branch:
    cd some-dependency
    git switch -c my-branch

    # Now restore the state of the workspace:
    git ws checkout


.. warning::

    If no revision has been specified for some dependencies, this command will not change these dependencies, even if they are checked out on a revision other than the default branch.


.. _git_ws_status:

``git ws status``
-----------------

Show repository status of all projects within a workspace.

.. literalinclude:: ../../static/cli.status.txt
   :language: text

This is similar to running ``git ws git status``, but the file paths shown will be modified such that they can be used with commands such as :ref:`git_ws_add`, :ref:`git_ws_reset` and :ref:`git_ws_commit`.

.. _git_ws_add:

``git ws add``
--------------

Run a ``git add`` on the specified paths.

.. literalinclude:: ../../static/cli.add.txt
   :language: text

This command can be used to conveniently add files to the index for later commit. It is mostly useful if there are modifications in multiple repositories. So instead of the following:

.. code-block:: bash

    cd Projects/my-workspace

    # Change into one project first:
    cd some-project
    git add ./some-file.txt

    # Change into another project and stage more files:
    cd ../another-project
    git add ./another-file.txt

The following can be used:

.. code-block:: bash

    cd Projects/my-workspace

    git ws add ./some-project/some-file.txt ./another-project/another-file.txt

Use :ref:`git_ws_status` to display all changes using paths suitable for use with this command.


.. _git_ws_rm:

``git ws rm``
-------------------

Run ``git rm`` on specified files within the workspace.


.. literalinclude:: ../../static/cli.rm.txt
   :language: text

This command can be used to conveniently run a ``git rm`` on file spread across several ``git`` clones within a workspace. So instead of the following:

.. code-block:: bash

    cd Projects/my-workspace/some-project
    git rm ./some-file.txt

    cd ../another-project
    git rm ./another-file.txt

You can use this:

.. code-block:: bash

    cd Projects/my-workspace
    git ws rm ./some-project/some-file.txt ./another-project/another-file.txt

.. _git_ws_reset:

``git ws reset``
----------------

Run a ``git reset`` on the given paths.

.. literalinclude:: ../../static/cli.reset.txt
   :language: text

Similarly to the :ref:`git_ws_add` command, this allows conveniently running a ``git reset`` on files spread across repositories in a workspace. So instead of this:


.. code-block:: bash

    cd Projects/my-workspace

    # Change into one project first:
    cd some-project
    git reset ./some-file.txt

    # Change into another project and stage more files:
    cd ../another-project
    git reset ./another-file.txt

This can be used:

.. code-block:: bash

    cd Projects/my-workspace

    git ws reset ./some-project/some-file.txt ./another-project/another-file.txt

Use :ref:`git_ws_status` to display all changes using paths suitable for use with this command.


.. _git_ws_commit:

``git ws commit``
-----------------

Runs a ``git commit`` in the projects within a workspace.

.. literalinclude:: ../../static/cli.commit.txt
   :language: text

This command can be used in two ways (similar to the use of ``git commit`` itself). In the first form, when no file paths are specified, the command runs a commit in all repositories which have staged changes:

.. code-block:: bash

    git ws commit -m "A commit in all repos with staged changes"

For staging, use either ``git add`` or ``git ws add``.

In the second form, a ``git commit`` will be run in the repositories where the given files are stored:

.. code-block:: bash

    cd Projects/my-workspace

    git ws commit \
        ./some-project/some-file.txt ./another-project/another-file.txt \
        -m "A commit in two projects"

In this form, only the files given on the command line will be included in the commits.


.. _git_ws_submodule:

``git ws submodule``
--------------------

Run a ``git submodule`` in all clones within a workspace.


.. literalinclude:: ../../static/cli.submodule.txt
   :language: text

This command can be used to conveniently work with ``git submodules`` that are included by some of the projects within a workspace. For example, to initialize and checkout submodules in all of the projects in a workspace, the following can be used:

.. code-block:: bash

    git ws submodule -- update --init --recursive


.. _git_ws_tag:

``git ws tag``
-------------------

Create a tag in the main project including a connected, frozen manifest.


.. literalinclude:: ../../static/cli.tag.txt
   :language: text

This command can be used to create a (named) tag in the workspace by:

- Creating a frozen manifest of the project's current state in the main project.
- Committing that manifest.
- And finally creating a ``git`` tag in the main repository.

The details of the tagging process are described in :ref:`tagging`.

.. note::

    This command solely applies changes in the main project. This is enough to be able to reproduce a given state of the project later on. In particular, this command will not create tags on any of the other projects. If this is what you intent, you can use something like that instead:

    .. code-block:: bash

        git ws git tag -m "Releasing v1.2.3.4" v1.2.3.4
