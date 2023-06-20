
Welcome to Git Workspace's documentation!
=========================================

Git Workspace is a lightweight tool which can be used to stitch together complex
workspaces from arbitrary many ``git`` repositories. In that regard, it is similar
to tools like `Google's repo tool <https://gerrit.googlesource.com/git-repo/>`_
or the `west <https://docs.zephyrproject.org/latest/develop/west/index.html>`_
tool included in the Zephyr project.

Git Workspace is integrated as git subcommand ``git ws`` - this is what users mostly
use. The following chapters provide details and guide through the usage of the
``git ws`` tool:

Links
-----

- `PyPI - Python Package Index <https://pypi.org/project/git-ws/>`_
- `Source Code <https://github.com/c0fec0de/git-ws>`_
- `Issues <https://github.com/c0fec0de/git-ws/issues>`_


.. toctree::
   :maxdepth: 2
   :caption: User Manual:

   manual/why
   manual/use-case
   manual/nomenclature
   manual/manifest
   manual/dependency-resolution
   manual/group-filter
   manual/tagging
   manual/fileref
   manual/shallow
   manual/command-line-interface/index


Besides use on the command line, Git Workspace also has a public API which can be used
for more advanced automatization of your projects:

.. toctree::
   :maxdepth: 1
   :caption: Programmer's Manual:

   api/gitws


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
