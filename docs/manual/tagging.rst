.. _tagging:

Tagging
=======

In plain ``git``,  creating a (named) version of a project is as simple as running

.. code-block:: bash

    git tag -m "Releasing v1.2.3" v1.2.3

But, what if your project is larger? Using ``git-ws`` helps you organize it and its dependencies in workspaces conveniently. And - by default - it will pull in dependencies of the main project on their main branches, so you can easily co-develop all modules together.

Eventually, though, you will need to push out a version of your main project. In this case, you will also have to *fix* the versions of all dependencies of it, such that later on you can easily reconstruct a workspace (e.g. to reproduce issues observed with that release).

Fortunately, ``git-ws`` has built-in support for both tagging a main project including all of its dependencies as well as restoring a workspace for such a tagged version.


Creating a Tag
--------------

In fact, tagging a workspace is as easy as running something like:

.. code-block:: bash

    git ws tag -m "Releasing v1.2.3" v1.2.3

This command will run the following steps:

1. Create a frozen manifest (cf :ref:`git_ws_manifest_freeze`) and store it in ``.git-ws/manifests/v1.2.3.toml`` within the main project.
2. Commit that frozen manifest to the main project.
3. Create a tag ``v1.2.3`` in the main project.

That's it! By that, you will have a tag in the main project with a suitable manifest associated with it. But... how to restore a workspace to a particular tag?


Checking out a Tagged Workspace
-------------------------------

In fact, creating a workspace for a tag of the main project is equally simple:

.. code-block:: bash

    cd ./main-project/
    git checkout v1.2.3
    git ws update

Yes, it's as simple as that! If ``git-ws`` detects that you currently have a tag checked out on the main project, it will look for a suitable (frozen) manifest within the ``.git-ws/manifests/`` sub-folder in the main project. If such a manifest is found, it will be used instead of the main manifest.
