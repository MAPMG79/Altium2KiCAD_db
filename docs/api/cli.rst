Command Line Interface API
========================

This section provides detailed API documentation for the command-line interface of the Altium to KiCAD Database Migration Tool.

CLI Module
---------

.. automodule:: migration_tool.cli
   :members:
   :undoc-members:
   :show-inheritance:

Command Line Arguments
--------------------

The command-line interface provides the following arguments:

.. code-block:: text

   usage: altium2kicad [-h] [--version] [--input INPUT] [--output OUTPUT]
                      [--library-name LIBRARY_NAME] [--config CONFIG]
                      [--custom-rules CUSTOM_RULES] [--confidence-threshold THRESHOLD]
                      [--validate-symbols] [--validate-footprints]
                      [--parallel-processing] [--max-workers MAX_WORKERS]
                      [--batch-size BATCH_SIZE] [--cache-results]
                      [--cache-path CACHE_PATH] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                      [--log-file LOG_FILE] [--verbose] [--gui] [--analyze]
                      [--test-connection] [--component-limit COMPONENT_LIMIT]
                      [--component-filter COMPONENT_FILTER] [--generate-mapping-report]
                      [--validate-output VALIDATE_OUTPUT] [--batch-config BATCH_CONFIG]
                      [--resume-from-checkpoint] [--clean-output] [--force-regenerate]
                      [--diagnostic-report]

Arguments
--------

General Arguments
~~~~~~~~~~~~~~~

``--help, -h``
  Show the help message and exit

``--version``
  Show the version number and exit

``--gui``
  Launch the graphical user interface

Input Arguments
~~~~~~~~~~~~~

``--input INPUT``
  Path to the Altium DbLib file or database connection string

``--config CONFIG``
  Path to the configuration file

``--custom-rules CUSTOM_RULES``
  Path to the custom mapping rules file

Output Arguments
~~~~~~~~~~~~~~

``--output OUTPUT``
  Directory to save the generated KiCAD library

``--library-name LIBRARY_NAME``
  Name of the generated KiCAD library

Mapping Arguments
~~~~~~~~~~~~~~~

``--confidence-threshold THRESHOLD``
  Minimum confidence score to accept a mapping (0.0-1.0)

``--validate-symbols``
  Validate symbols against KiCAD libraries

``--validate-footprints``
  Validate footprints against KiCAD libraries

Performance Arguments
~~~~~~~~~~~~~~~~~~

``--parallel-processing``
  Enable parallel processing

``--max-workers MAX_WORKERS``
  Maximum number of worker processes for parallel processing

``--batch-size BATCH_SIZE``
  Number of components to process in each batch

``--cache-results``
  Cache mapping results for faster repeated migrations

``--cache-path CACHE_PATH``
  Path to the cache directory

Logging Arguments
~~~~~~~~~~~~~~~

``--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}``
  Set the logging level

``--log-file LOG_FILE``
  Path to the log file

``--verbose``
  Enable verbose output

Utility Arguments
~~~~~~~~~~~~~~~

``--analyze``
  Analyze the Altium database without performing migration

``--test-connection``
  Test the database connection

``--component-limit COMPONENT_LIMIT``
  Limit the number of components to process

``--component-filter COMPONENT_FILTER``
  SQL WHERE clause to filter components

``--generate-mapping-report``
  Generate a detailed mapping report

``--validate-output VALIDATE_OUTPUT``
  Validate a previously generated KiCAD library

``--batch-config BATCH_CONFIG``
  Path to the batch configuration file

``--resume-from-checkpoint``
  Resume migration from the last checkpoint

``--clean-output``
  Clean the output directory before migration

``--force-regenerate``
  Force regeneration of the KiCAD library

``--diagnostic-report``
  Generate a diagnostic report for troubleshooting