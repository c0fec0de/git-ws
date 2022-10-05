.. anyrepo documentation master file, created by
   sphinx-quickstart on Mon Sep 19 12:15:54 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to anyrepo's documentation!
===================================

`AnyRepo` is a lightweight tool which can be used to stitch together complex
workspaces from arbitrary many `git` repositories. In that regard, it is similar
to tools like `Google's repo tool <https://gerrit.googlesource.com/git-repo/>`_
or the `west <https://docs.zephyrproject.org/latest/develop/west/index.html>`_
tool included in the Zephyr project.

`AnyRepo` comes with the `anyrepo` command line tool - this is what users mostly
use. The following chapters provide details and guide through the usage of the
`anyrepo` command line tool:

.. toctree::
   :maxdepth: 2
   :caption: User Manual:

   manual/why
   manual/nomenclature


Besides use on the command line, AnyRepo also has a public API which can be used
for more advanced automatization of your projects:

.. toctree::
   :maxdepth: 2
   :caption: Programmer's Manual:

   api/modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
