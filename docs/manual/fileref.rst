.. _fileref:

File Linking and Copying
========================

``git-ws`` places a main repository and all its dependencies by default into
a single shared workspace folder side-by-side. Typically, this isn't a problem
as for most use cases, one can use links from e.g. the main repository to a
sibling one.

However, there might be situations where it is handy to place some files
directly within the workspace folder itself. For example:

- Some documentation like a ``README``.
- A configuration file for e.g. IDEs or editors that shall apply for every
  repository within a workspace.
- A top level "project file" (e.g. a somewhat generic,
  ``CMakeLists.txt`` when working with ``CMake``).

To aid this, ``git-ws`` provides two mechanisms: File linking and file copying.

.. note:: Linking and Copying only works for the main repository

    Both mechanisms described here apply only to the main repo within a
    workspace. Copy and link files defined by dependencies of the main
    repo are ignored.


File Linking
++++++++++++

The first way to get a file into the workspace directory is by creating a
link to the real file within the main repository. This can easily be done by
adding the following to the main repo's manifest file:

.. code-block:: toml

    [[linkfiles]]
    src = "file-in-main-repo.txt"
    dest = "link-in-workspace.txt"

Assuming that this snipped is put into the main repo's manifest, the resulting
workspace might look somehow like this:

.. code-block::

    workspace
    ├── link-in-workspace.txt -> main-project/file-in-main-repo.txt
    └── main-project
        └── file-in-main-repo.txt

As you can see, the file ``link-in-workspace.txt`` is a symbolic link to the
actual file in the main repository. This has some nice side effect: You can
easily open the file in e.g. a text editor and make changes - they'll go
directly to the actual file (and hence, can be committed to version control
easily).

.. warning:: File Linking might not be supported by all operating systems

    In particular, Windows didn't support symbolic links for a long time.
    Users accounts might be configured to not have the privileges to create
    new symbolic links. Hence, although technically they should be preferred
    over file copying, if you seek complete compatibility across operating
    systems, you might prefer copying instead.


File Copying
++++++++++++

The second mechanism for getting files into the workspace folder is file
copying. It is equally simple as the file linking. Just put the following into
the main repo's manifest file:

.. code-block:: toml

    [[copyfiles]]
    src = "file-in-main-repo.txt"
    dest = "copy-in-workspace.txt"

With this, the resulting workspace would rather look like this:

.. code-block::

    workspace
    ├── copy-in-workspace.txt
    └── main-project
        └── file-in-main-repo.txt

Note that this time, ``copy-in-workspace.txt`` is a copy of the actual file
in the main repository. That also means that editing it will keep the original
file unchanged.
