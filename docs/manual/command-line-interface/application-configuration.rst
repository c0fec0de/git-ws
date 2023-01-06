Application Configuration
=========================

A part of the aspects of ``git ws`` can be configured at various levels. Programmatically, the :class:`AppConfig <gitws.appconfig.AppConfig>` class can be used to retrieve and set configuration values. On the command line, the ``git ws config`` command with its various sub-commands provides the same capabilities.


.. _git_ws_config:

``git ws config``
-----------------

Get and set application configuration options.

.. include:: ../../static/cli.config.txt
    :code: bash

The ``config`` sub-command can be used to retrieve and modify configuration values for the system wide, per user and workspace configuration.

Configuration values can be stored in three locations:

- System wide configuration applies to all users on a given system.
- User configuration applies to the current user.
- Finally, workspace configuration applies only to the current workspace.

The values from these locations are merged (in the given order), i.e. the system configuration has the lowest priority and can be overridden by the user configuration which in turn can be overridden by the workspace configuration.

In addition to persistently set options in these configuration files, options also can be overridden by setting appropriate environment options. For example, to override the ``color_ui`` option, one can set the environment variable ``GIT_WS_COLOR_UI``.

To interact with the configuration, a set of sub-commands are available. By default, these commands either operate on the merged configuration options or (in case of commands that modify configurations) on the configuration files from highest to lowest priority (i.e. if one runs such a command from within a workspace, the workspace configuration file is modified, otherwise, the user configuration file is written). This can be changed by using the options ``--system``, ``--user`` or ``--workspace`` to read from or write to a specific file.


.. _git_ws_config_delete:

``git ws config delete``
++++++++++++++++++++++++

Delete an option.

.. include:: ../../static/cli.config.delete.txt
    :code: bash

This deletes the given option from the configuration such that the implicit default will be used instead:

.. code-block:: bash

    # Delete the color_ui option:
    git ws config delete color_ui


.. _git_ws_config_files:

``git ws config files``
+++++++++++++++++++++++

Get the location of the configuration files.

.. include:: ../../static/cli.config.files.txt
    :code: bash

This prints the locations of the configuration files. The location of these files are system dependent, so this command is useful to learn where to put configuration files on a concrete system:

.. code-block:: bash

    git ws config files
    ## Should print something like:
    # system: /etc/xdg/GitWS/config.toml
    # user: /home/User/.config/GitWS/config.toml
    # workspace: /home/User/Projects/my-workspace/.git-ws/config.toml



.. _git_ws_config_get:

``git ws config get``
+++++++++++++++++++++

Read a single configuration option.

.. include:: ../../static/cli.config.get.txt
    :code: bash

This reads and prints the value of the given configuration option.

.. code-block:: bash

    git ws config get color_ui
    ## Should print e.g.:
    # True


.. _git_ws_config_list:

``git ws config list``
++++++++++++++++++++++

Read all configuration values.

.. include:: ../../static/cli.config.list.txt
    :code: bash

This reads and prints all configuration options, including a short description
for each option:

.. code-block:: bash

    git ws config list
    ## Should print something like:
    # # The path (relative to the project's root folder) to the manifest file.
    # manifest_path = git-ws.toml
    #
    # # If set to true, the output the tool generates will be colored.
    # color_ui = True
    #
    # # The groups to operate on.
    # groups

.. _git_ws_config_set:

``git ws config set``
+++++++++++++++++++++

Set a configuration option.

.. include:: ../../static/cli.config.set.txt
    :code: bash

This command sets the given option to the specified value. By default, if an unknown option is given, the command terminates with an error. Using the ``--ignore-unknown`` option, writing any option can be enforced.

.. code-block:: bash

    # Setting a standard option:
    git ws config set color_ui True

    ## Setting a custom option requires a special flag:
    git ws config set --ignore-unknown my_option "Hello world!"
