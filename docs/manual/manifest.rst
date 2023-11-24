.. _manifest_manual:

Manifest
========

The main purpose of Git Workspace is to be able to compose a workspace consisting of one or more ``git`` repositories.
For this, a single repository can define meta information including a list of dependencies to other ``git`` repositories. These information are stored in a file called ``git-ws.toml``.
To generate that file, all you need to do is running the following command inside your project:

.. code-block:: bash

    git ws manifest create

This will create a template for the manifest file that you can edit to fit your needs. It contains:

* :ref:`manifest_group_filters`
* :ref:`manifest_remotes`
* :ref:`manifest_defaults`
* :ref:`manifest_dependencies`
* :ref:`manifest_linkcopyfiles`

The standard file created is self-documenting, so it should be relatively easy to get started with it:


.. include:: ../static/git-ws.toml
    :code: toml

In the following, the various parts of a manifest file are described.


.. _manifest_group_filters:

The ``group-filters`` section
-----------------------------

Dependencies might get categorized by groups.
All groups in the main project are selected by default.
The ``group-filters`` list manipulates this default behaviour.
The last matching entry wins.

================  ===============================================
Statement         Effect
================  ===============================================
``-group``        deselect ``group``
``-group@path``   deselect ``group`` but only at ``path``
``+group``        reselect ``group``
``+group@path``   reselect ``group`` but only at ``path``
================  ===============================================

See :ref:`group_filtering` for more information about group filtering.

The command :ref:`git_ws_group_filters` manipulates this section.


.. _manifest_remotes:

The ``remotes`` section
-----------------------

Remotes are simply aliases to git servers.
A remote refers to a directory with git repositories.
A remote has the following attributes:

============  ======  =============================
Attribute     Type    Description
============  ======  =============================
``name``      string  Mandatory. Name of the Alias. Used by ``[defaults]`` and ``[[dependencies]]``
``url-base``  string  Mandatory. URL to a group of repositories. Not the repository itself!
============  ======  =============================

.. note::

    Local filesystem URLs **must** be prefixed by ``file://``.

Multiple remotes look like this:

.. code-block:: toml

    [[remotes]]
    name = "company"
    url-base = "https://git.company.com"

    [[remotes]]
    name = "github"
    url-base = "https://github.com/user"

The command :ref:`git_ws_remote` manipulates this section.


.. _manifest_defaults:

The ``defaults`` section
------------------------

The ``defaults`` section defines default values for all dependencies within the current manifest.
If a dependency specifies the attribute explicitly the given value takes precedence and the default value
is ignored.
The following attributes are taken as default values in the ``[[dependencies]]`` section.

================  ===============  =============================
Attribute         Type             Description
================  ===============  =============================
``remote``        string           Optional. Name of a remote from the ``[[remotes]]`` section.
``revision``      string           Optional. Git branch or tag to be checked out.
``groups``        list of strings  Optional. Categorization of the dependency.
``with-groups``   list of strings  Optional. Group selection of the dependency.
================  ===============  =============================

Example ``defaults`` section:

.. code-block:: toml

    [defaults]
    remote = "myserver"
    revision = "main"
    groups = ["test"]
    # with-groups = ["doc"]

The command :ref:`git_ws_default` manipulates this section.

.. note::

    It is strongly recommended to specify a default revision:

    .. code-block:: toml

        [defaults]
        revision = "main"

.. _manifest_dependencies:

The ``dependencies`` section
----------------------------


The ``dependencies`` section is the one, the one this is all about ---
the listing of all other git clones you need, next to the current git clone.
The following attributes provide all the freedom:

===================  ===========================  ===================================================================
 Attribute           Type                         Description
===================  ===========================  ===================================================================
| ``name``           | string                     | Mandatory. The name of it.
| ``remote``         | string                     | Optional. Name of a remote from the ``[[remotes]]`` section.
| ``sub-url``        | string                     | Optional. URL relative to ``remote.url_base``.
| ``url``            | string                     | Optional. URL. Absolute or Relative.
                                                  | Relative URLs are relative to repo containing the manifest.
                                                  | Default is ``../name`` if ``remote`` and ``sub-url`` are empty.
| ``revision``       | string                     | Optional. Git branch, tag or SHA to be checked out.
| ``path``           | string                     | Optional. Filesystem Path.
                                                  | Relative to Workspace Root Directory.
                                                  | ``name`` by default.
| ``manifest-path``  | string                     | Optional. Path to the manifest file.
                                                  | Relative to ``path``.
                                                  | ``git-ws.toml`` by default.
| ``groups``         | list of strings            | Optional. Categorization of the dependency.
| ``with-groups``    | list of strings            | Optional. Group selection of the dependency.
| ``submodules``     | bool                       | Optional. Initialize ``git submodule`` s.
                                                  | ``True`` by default.
| ``linkfiles``      | list of ``src``/``dest``   | Optional. List of links to be created.
                                                  | ``src`` is relative to ``path``.
                                                  | ``dest`` is relative to workspace.
                                                  | See :ref:`fileref` for more information
| ``copyfiles``      | list of ``src``/``dest``   | Optional. List of files to be copied.
                                                  | ``src`` is relative to ``path``.
                                                  | ``dest`` is relative to workspace.
                                                  | See :ref:`fileref` for more information
===================  ===========================  ===================================================================

Please note:

* ``remote`` and ``url`` are mutually exclusive. Do not specify both.
* ``sub-url`` requires a ``remote`` and is always relative to ``remote.url_base``.
* ``url`` can be absolute or relative.
* A relative ``url`` is relative to the remote which contains the current manifest file.
  More precise: it is relative to the url returned by ``git remote get-url origin`` in the git clone containing the manifest file
* If the dependency is located on the same server in the same directory, ``name`` is the only required attribute.
  ``remote``, ``sub-url`` and ``url`` can be simply left blank.
* A manifest file located outside a git clone does not support relative ``url`` s.
* Local filesystem URLs **must** be prefixed by ``file://``.
* ``linkfiles`` and ``copyfiles`` are only applied for dependencies in the main manifest.
  ``linkfiles`` and ``copyfiles`` in manifests referenced in the dependencies section are ignored.

A minimal dependency to a repo on the same server:

.. code-block:: toml

     [[dependencies]]
     name = "my"

A full flavored dependency using a ``remote``:

.. code-block:: toml

    [[dependencies]]
    name = "myname"
    remote = "remote"
    sub-url = "my.git"
    revision = "main"
    path = "mydir"
    groups = ["group"]

    [[dependencies.linkfiles]]
    src = "file0-in-mydir.txt"
    dest = "link0-in-workspace.txt"

    [[dependencies.copyfiles]]
    src = "file1-in-mydir.txt"
    dest = "file1-in-workspace.txt"

A full flavored dependency using a ``url``:

.. code-block:: toml

    [[dependencies]]
    name = "myname"
    url = "https://github.com/myuser/my.git"
    revision = "main"
    path = "mydir"
    groups = ["group"]

    [[dependencies.linkfiles]]
    src = "file0-in-mydir.txt"
    dest = "link0-in-workspace.txt"

    [[dependencies.copyfiles]]
    src = "file1-in-mydir.txt"
    dest = "file1-in-workspace.txt"


The command :ref:`git_ws_dep` manipulates this section.


.. _manifest_linkcopyfiles:

The ``linkfiles`` and ``copyfiles`` sections
--------------------------------------------

The ``linkfiles`` section lists files to be linked over from the main project - the project which contains the manifest file.
``copyfiles`` are copied and *not* symbolic linked. Everything else is the same.

``linkfiles`` and ``copyfiles`` entries have two mandatory attributes:

============  ===============  ==============================================================================
Attribute     Type             Description
============  ===============  ==============================================================================
``src``       string           Mandatory. Source file path, relative to the main project root directory
``dest``      string           Mandatory. Destination file path, relative to the workspace directory
 ``groups``   list of strings  Optional. Categorization. Just create if the group is selected.
============  ===============  ==============================================================================

Multiple entries look like that:

.. code-block:: toml

    [[linkfiles]]
    src = "file-in-main-clone0.txt"
    dest = "link-in-workspace0.txt"

    [[linkfiles]]
    src = "file-in-main-clone1.txt"
    dest = "link-in-workspace1.txt"
    groups = ['test']

.. note::

    ``linkfiles`` and ``copyfiles`` are also supported on standalone manifest files. ``src`` is relative to the workspace directory then.
