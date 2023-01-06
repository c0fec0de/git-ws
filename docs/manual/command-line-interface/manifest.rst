Manifest
========

The :ref:`manifest <nomenclature_manifest>` is one of the core aspects of ``git ws``: It contains the needed meta information of a project about its dependencies as well as other configurations. ``git ws`` provides several commands that allow to work with manifest files, create them as well as alter them.


.. _git_ws_manifest:

``git ws manifest``
-------------------

Work with manifest files.

.. include:: ../../static/cli.manifest.txt
    :code: bash

Git Workspace extensively uses manifest files to store meta information and manage dependencies. The ``git ws manifest`` command allows working with these manifest files, creating them and play other tricks needed in the daily workflow.

.. _git_ws_manifest_create:

``git ws manifest create``
++++++++++++++++++++++++++

Create a new manifest.

.. include:: ../../static/cli.manifest.create.txt
    :code: bash

This command generates a new manifest file. The generated file comes with some built-in documentation, hence, editing the file should be quite easy. Refer to :ref:`manifest_manual` to learn more about the general structure of the manifest file.

.. code-block:: bash

    # Generate a new manifest and write it to file git-ws.toml
    git ws manifest create

    # Create a new manifest, writing it to my-custom-manifest.toml
    git ws manifest create --manifest my-custom-manifest.toml


.. _git_ws_manifest_freeze:

``git ws manifest freeze``
++++++++++++++++++++++++++

Freeze a project.

.. include:: ../../static/cli.manifest.freeze.txt
    :code: bash

This command is useful to create a *frozen* state of a project. Often, projects will pull in dependencies on branches or tags. This means that - depending on when the workspace is created, the concrete content might differ. However, there are use cases where a particular state of a workspace needs to be conserved, e.g. when running a CI/CD pipeline for a particular snapshot of the project. This is exactly what the ``freeze`` command does. It creates a new manifest from the current one but fixes each dependency on its specific ``git`` commit hash. Also transitive dependencies are recorded.

.. code-block:: bash

    # Create a frozen manifest and write it to standard output:
    git ws manifest freeze

    # Create a frozen manifest but write it to a file:
    git ws manifest freeze --output git-ws-v2.3.4.toml

The freezing mechanism is internally used by the :ref:`git_ws_tag` command as well.

To recreate a historic state of the project, one can use the ``--manifest`` option of the various ``git ws`` commands to use the alternative, frozen manifest, e.g.:

.. code-block:: bash

    # Example 1: Clone a project and build a workspace using a frozen manifest:
    git ws clone https://example.com/my-project --manifest git-ws-v1.2.3.toml

    # Example 2: Freeze the project state in a CI/CD pipeline and use it throughout the jobs.
    #
    # Typically, we would have a pipeline which in the very beginning creates a frozen manifest
    # which is then uploaded as artifact:
    git ws manifest freeze --output git-ws-current-version.toml

    # Any later job in the pipeline would then first update the workspace to the frozen state:
    git ws update --manifest git-ws-current-version.toml


.. _git_ws_manifest_path:

``git ws manifest path``
++++++++++++++++++++++++

Print the path to the main manifest:

.. include:: ../../static/cli.manifest.path.txt
    :code: bash

This command prints the path to the manifest of the main project.

.. code-block:: bash

    git ws manifest path
    ## Should print something like:
    # /home/User/Projects/my_workspace/my_project/git-ws.toml


.. _git_ws_manifest_paths:

``git ws manifest paths``
+++++++++++++++++++++++++

Print the paths of all manifest files (i.e. the main project and all, also transitive, dependencies).

.. include:: ../../static/cli.manifest.paths.txt
    :code: bash

This commands prints the paths to the main manifest file as well as any manifest files of dependencies:

.. code-block:: bash

    git ws manifest paths
    ## Should print something like
    # /home/User/Projects/my_workspace/my_project/git-ws.toml
    # /home/User/Projects/my_workspace/my_lib1/git-ws.toml
    # /home/User/Projects/my_workspace/my_lib2/git-ws.toml


.. _git_ws_manifest_resolve:

``git ws manifest resolve``
+++++++++++++++++++++++++++

Create a merged manifest.

.. include:: ../../static/cli.manifest.resolve.txt
    :code: bash

This command creates a new manifest from the current one, merging all the dependencies such that everything is contained stand-alone in one file.

.. code-block:: bash

    # Create a resolved manifest, writing it to standard output:
    git ws manifest resolve

    # Same, but write to a file:
    git ws manifest resolve --output git-ws-resolved.toml

Such a resolved manifest can be useful to understand the layout of the created workspace. In addition, it can be used to quickly create a tweaked workspace as it allows to easily point (transitive) dependencies to another revision.


.. _git_ws_manifest_upgrade:

``git ws manifest upgrade``
+++++++++++++++++++++++++++

Upgrade an existing manifest.

.. include:: ../../static/cli.manifest.upgrade.txt
    :code: bash

The intention of this command is to update existing manifest files when new versions of ``git ws`` introduce new options. In addition, the comments in the file will be updated to the current version.

.. code-block:: bash


    git ws manifest upgrade

Any user specific values are kept as-is, however, comments are stripped from the file.

.. _git_ws_manifest_validate:

``git ws manifest validate``
++++++++++++++++++++++++++++

Validate a manifest file.

.. include:: ../../static/cli.manifest.validate.txt
    :code: bash

This command reads and validates a manifest file. If the file is valid, the command exits with an exit code of ``0``. In case the file is not valid, the error is printed and the command exits with an error code.

.. code-block:: bash

    # Validate a file:
    git ws manifest validate

    ## In case an error occurs, something like this might get printed:
    # Error: Manifest 'my_project/git-ws.toml' is broken: 1 validation error for ManifestSpec
    # dependencies -> 0 -> groups
    #   value is not a valid tuple (type=type_error.tuple)


.. _git_ws_default:

``git ws default``
-------------------

Update the defaults in a manifest.


.. include:: ../../static/cli.default.txt
    :code: bash

This command can be used to update values in the :ref:`defaults <manifest_defaults>` section of a manifest. For example, if one wants to use a branch called `stable` in all projects in their environment as default one, this could be done like this:

.. code-block:: bash

    git ws default revision stable



.. _git_ws_dep:

``git ws dep``
-------------------

Programmatically edit dependencies of a project.


.. include:: ../../static/cli.dep.txt
    :code: bash

This is a complex command with - via its sub-commands - allows to edit the :ref:`dependencies of a project <manifest_dependencies>` on the command line.

.. _git_ws_dep_add:

``git ws dep add``
+++++++++++++++++++++++

Add a new dependency to the project.

.. include:: ../../static/cli.dep.add.txt
    :code: bash

This command can be used to add new dependencies to a project. At least, the name of the dependency is required - other information is - if not explicitly specified - derived from the name.

.. code-block:: bash

    # Add a new dependency
    git ws dep add some-library

    # Add a new dependency which is located on a different server,
    # hence, specify its clone URL as well:
    git ws dep add another-library --url https://example.com/another-library.git

    # Add yet another dependency, on the same server but include it with a
    # specific revision:
    git ws dep add yet-another-library --revision v1.2.3


.. _git_ws_dep_delete:

``git ws dep delete``
++++++++++++++++++++++++++

Remove a dependency.

.. include:: ../../static/cli.dep.delete.txt
    :code: bash

This removes a dependency from the manifest:

.. code-block:: bash

    git ws dep delete some-library


.. _git_ws_dep_list:

``git ws dep list``
++++++++++++++++++++++++

List dependencies specified in the manifest.

.. include:: ../../static/cli.dep.list.txt
    :code: bash

This prints the list of dependencies as specified in the manifest file.

.. _git_ws_dep_set:

``git ws dep set``
+++++++++++++++++++++++

Update properties of a dependency.

.. include:: ../../static/cli.dep.set.txt
    :code: bash

This command can be used to update the properties of a property. It takes the name of a dependency, the name of a property and a new value for it.

.. code-block:: bash

    # Update the URL of a dependency:
    git ws dep set some-library url https://new-server.org/some-library.git

    # Update the revision of a dependency:
    git ws dep set another-library revision v2.3.4


.. _git_ws_group_filters:

``git ws group-filters``
------------------------

Edit :ref:`group filters <manifest_group_filters>` specified in a manifest.


.. include:: ../../static/cli.group-filters.txt
    :code: bash

This command allows setting the  groups filters in the manifest:

.. code-block:: bash

    git ws group-filters +some-group,-another-group


.. _git_ws_remote:

``git ws remote``
-------------------

Edit :ref:`remotes <manifest_remotes>` in a manifest.

.. include:: ../../static/cli.remote.txt
    :code: bash

This complex command allows editing values in the remotes section of a manifest.



.. _git_ws_remote_add:

``git ws remote add``
++++++++++++++++++++++++++

Add a new remote.


.. include:: ../../static/cli.remote.add.txt
    :code: bash

This command adds a new remote to the manifest:

.. code-block:: bash

    # Add a remote "my-remote" pointing to the given base URL:
    git ws remote add my-remote https://some.server.com/



.. _git_ws_remote_delete:

``git ws remote delete``
+++++++++++++++++++++++++++++

Remove a remote.

.. include:: ../../static/cli.remote.delete.txt
    :code: bash


This removes the named remote from the manifest:

.. code-block:: bash

    git ws remote delete my-remote


.. _git_ws_remote_list:

``git ws remote list``
+++++++++++++++++++++++++++

List defined remotes.

.. include:: ../../static/cli.remote.list.txt
    :code: bash


This command simply lists the remotes that are defined in the manifest file.