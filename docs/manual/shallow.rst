.. shallow_manual:

Shallow Clone Support
=====================

Sometimes, ``git`` repositories can grow over time. Typically, this is not a
problem. However, if a user needs to clone such a grown repository, the download
can take quite a while.

Naturally, when working with tools like ``git-ws`` which accumulate potentially
many such large repositories, an operation like the initial ``git ws clone -U``
might take quite a bit.

To help in such situations, ``git-ws`` supports *shallow cloning*. Using it
is quite simple and follows how ``git`` itself implements it:

Commands like ``git-ws init`` and ``git-ws clone`` support a ``--depth`` option.
Simply set this to the desired number of commits you want to include in each
repository of the workspace:

.. code-block:: bash

    git ws clone -U --depth=1 https://example.com/my-project

That's it!

.. note:: The depth is stored in the workspace

    ``git-ws`` saves the initially specified depth in the workspace
    configuration. This means, that - e.g. after updates or if you specify
    a different group filer - when additional repositories are added to
    the workspace after its initial creation, the same depth will be
    used when cloning them.

    To change this, unset the depth in the settings or unshallow the complete
    workspace.


Unshallowing A Workspace
------------------------

Sometimes, working with a shallow workspace can be challenging. Naturally,
a shallow repository contains only part of the ``git`` history. That means that
some operations and tools might not work as expected.

Fortunately, ``git-ws`` has you covered here as well: If you realize you need
to *upgrade* a complete workspace, you can use the ``unshallow`` command to
pull the full history of each repository and also ensure that any future
repository that might get added to the workspace will be cloned in its
entirety:

.. code-block:: bash

    git ws unshallow

That's it!

.. warning:: This operation might take a while to complete!

    If you used shallow cloning initially, it might have been for a reason.
    So if you unshallow a workspace consisting of multiple, potentially
    very large repositories, get a coffee, lean back and be patient.

