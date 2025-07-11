Usage
=====

This guide explains how to use the Altium to KiCAD Database Migration Tool.

Command Line Interface
---------------------

The tool provides a command-line interface (CLI) for easy integration into scripts and automation workflows.

Basic Usage
~~~~~~~~~~

The most basic usage is to specify an input Altium .DbLib file and an output directory:

.. code-block:: bash

    altium2kicad --input path/to/altium.DbLib --output path/to/output/directory

This will:

1. Parse the Altium .DbLib file
2. Extract component data from the connected database
3. Map Altium components to KiCAD equivalents
4. Generate a KiCAD database library (.kicad_dbl) and SQLite database
5. Create a migration report

Advanced Options
~~~~~~~~~~~~~~

The CLI supports several advanced options:

.. code-block:: bash

    altium2kicad --input path/to/altium.DbLib \
                 --output path/to/output/directory \
                 --kicad-libs path/to/kicad/libraries \
                 --config path/to/config.yaml \
                 --create-views \
                 --validate-symbols \
                 --min-confidence 70 \
                 --log-level DEBUG

Options:

* ``--kicad-libs``: Path to KiCAD libraries for better symbol/footprint mapping
* ``--config``: Path to a custom configuration file
* ``--create-views``: Create database views for different component types
* ``--validate-symbols``: Validate symbol and footprint existence in KiCAD libraries
* ``--min-confidence``: Minimum confidence score (0-100) to accept a mapping
* ``--log-level``: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Getting Help
~~~~~~~~~~~

To see all available options:

.. code-block:: bash

    altium2kicad --help

To see help for a specific command:

.. code-block:: bash

    altium2kicad migrate --help

Graphical User Interface
-----------------------

The tool also provides a graphical user interface (GUI) for users who prefer a visual approach.

Launching the GUI
~~~~~~~~~~~~~~~

To launch the GUI:

.. code-block:: bash

    altium2kicad-gui

Or if installed from source:

.. code-block:: bash

    python -m migration_tool.gui

Using the GUI
~~~~~~~~~~~

The GUI is organized into tabs:

1. **Configuration**: Set input and output paths, and migration options
2. **Mapping Rules**: View and customize component mapping rules
3. **Results**: View migration statistics and logs
4. **About**: Information about the tool

Basic Workflow:

1. In the Configuration tab:
   - Select an Altium .DbLib file using the "Browse" button
   - Choose an output directory
   - Optionally specify KiCAD libraries path
   - Set migration options

2. Click "Test Connection" to verify database connectivity

3. Click "Start Migration" to begin the migration process

4. Once complete, the Results tab will show migration statistics and logs

5. Use "Export Report" to save a detailed migration report

6. Use "Open Output Folder" to view the generated files

Configuration
------------

The tool can be configured using YAML configuration files. See the :doc:`configuration` section for details.

Examples
-------

See the :doc:`examples` section for example usage scenarios.

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~

**Database Connection Errors**

If you encounter database connection errors:

1. Verify that the database path in the Altium .DbLib file is correct
2. Ensure you have the appropriate database drivers installed
3. Check that the database is accessible from your machine
4. For network databases, verify network connectivity

**Low Confidence Mappings**

If many components have low confidence scores:

1. Provide a path to your KiCAD libraries using ``--kicad-libs``
2. Customize mapping rules in the configuration files
3. Adjust the minimum confidence threshold

**Missing Symbols or Footprints**

If symbols or footprints are missing in the output:

1. Enable validation with ``--validate-symbols``
2. Check the migration report for details on missing items
3. Update your mapping rules or manually add the missing items

Logging
~~~~~~

For detailed logging, set the log level to DEBUG:

.. code-block:: bash

    altium2kicad --input path/to/altium.DbLib --output path/to/output/directory --log-level DEBUG

This will provide detailed information about each step of the migration process.

Getting Help
~~~~~~~~~~

If you encounter issues not covered in this documentation:

1. Check the GitHub repository for known issues
2. Open a new issue with detailed information about your problem
3. Include logs, error messages, and steps to reproduce the issue