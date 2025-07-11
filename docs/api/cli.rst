Command Line Interface (CLI)
===========================

The Altium to KiCAD Database Migration Tool provides a comprehensive command-line interface for performing migrations and related operations without a graphical user interface.

Overview
--------

The CLI provides several commands for different operations:

* ``migrate``: Migrate Altium database to KiCAD format
* ``validate``: Validate existing migration results
* ``test-connection``: Test connection to Altium database
* ``generate-sample``: Generate sample data for testing
* ``info``: Show information about Altium database

The CLI is implemented through the ``MigrationCLI`` class, which handles command-line arguments, logging, and execution of the appropriate operations.

Basic Usage
----------

.. code-block:: bash

   # Basic migration
   python run_cli.py migrate input.DbLib -o output_dir
   
   # Migration with custom settings
   python run_cli.py migrate input.DbLib -o output_dir --parallel --cache --fuzzy-threshold 0.8
   
   # Validate existing migration
   python run_cli.py validate output_dir/components.db original_data.json
   
   # Test database connection
   python run_cli.py test-connection input.DbLib
   
   # Generate sample data for testing
   python run_cli.py generate-sample sample_output

CLI Architecture
---------------

The CLI is built using Python's ``argparse`` module and follows a command-subcommand pattern. Each subcommand has its own set of arguments and options.

MigrationCLI Class
-----------------

.. code-block:: python

   class MigrationCLI:
       """Command Line Interface for migration operations"""
       
       def __init__(self):
           self.logger = self._setup_logging()
           self.config_manager = None

The ``MigrationCLI`` class is the main entry point for the CLI. It handles:

* Setting up logging
* Parsing command-line arguments
* Loading and validating configuration
* Executing the appropriate command
* Handling errors and generating reports

Methods
~~~~~~~

setup_logging
^^^^^^^^^^^^^

.. code-block:: python

   def _setup_logging(self, level: str = "INFO") -> logging.Logger:
       """Setup logging configuration"""

Sets up logging with appropriate handlers and log level.

**Parameters:**

* ``level``: Logging level (DEBUG, INFO, WARNING, ERROR)

**Returns:**

* Logger instance

create_parser
^^^^^^^^^^^^

.. code-block:: python

   def create_parser(self) -> argparse.ArgumentParser:
       """Create command line argument parser"""

Creates and configures the argument parser for the CLI.

**Returns:**

* Configured ArgumentParser instance

run
^^^

.. code-block:: python

   def run(self, args: Optional[list] = None) -> int:
       """Main entry point for CLI"""

Main entry point for the CLI. Parses arguments and executes the appropriate command.

**Parameters:**

* ``args``: Optional list of command-line arguments (if None, uses sys.argv)

**Returns:**

* Exit code (0 for success, non-zero for errors)

Commands
--------

migrate
~~~~~~~

Migrates an Altium database to KiCAD format.

**Arguments:**

* ``input``: Path to Altium .DbLib file
* ``--output, -o``: Output directory for KiCAD database files
* ``--kicad-symbols``: Path to KiCAD symbol libraries
* ``--kicad-footprints``: Path to KiCAD footprint libraries
* ``--parallel``: Enable parallel processing
* ``--threads``: Number of worker threads for parallel processing (default: 4)
* ``--batch-size``: Batch size for processing components (default: 1000)
* ``--cache``: Enable caching for improved performance
* ``--fuzzy-threshold``: Threshold for fuzzy matching (0.0-1.0, default: 0.7)
* ``--confidence-threshold``: Minimum confidence threshold for mappings (default: 0.5)
* ``--validate-symbols``: Validate symbol existence in KiCAD libraries
* ``--validate-footprints``: Validate footprint existence in KiCAD libraries
* ``--create-views``: Create component type views in database (default: True)
* ``--no-optimize``: Skip database optimization step
* ``--advanced-mapping``: Use advanced mapping algorithms
* ``--ml-mapping``: Enable machine learning-based mapping
* ``--export-report``: Export detailed migration report to file

**Example:**

.. code-block:: bash

   python run_cli.py migrate library.DbLib -o output_dir --parallel --threads 8 --cache

validate
~~~~~~~~

Validates existing migration results.

**Arguments:**

* ``database``: Path to KiCAD database file to validate
* ``original_data``: Path to original Altium data (JSON format)
* ``--report``: Output validation report to file

**Example:**

.. code-block:: bash

   python run_cli.py validate output_dir/components.db original_data.json --report validation_report.json

test-connection
~~~~~~~~~~~~~~

Tests connection to an Altium database.

**Arguments:**

* ``dblib_file``: Path to Altium .DbLib file
* ``--timeout``: Connection timeout in seconds (default: 30)

**Example:**

.. code-block:: bash

   python run_cli.py test-connection library.DbLib --timeout 60

generate-sample
~~~~~~~~~~~~~~

Generates sample data for testing.

**Arguments:**

* ``output_dir``: Output directory for sample data
* ``--components``: Number of sample components to generate (default: 100)
* ``--tables``: Number of component tables to generate (default: 3)

**Example:**

.. code-block:: bash

   python run_cli.py generate-sample test_data --components 200 --tables 5

info
~~~~

Shows information about an Altium database.

**Arguments:**

* ``dblib_file``: Path to Altium .DbLib file
* ``--detailed``: Show detailed information about each table

**Example:**

.. code-block:: bash

   python run_cli.py info library.DbLib --detailed

Global Options
-------------

These options can be used with any command:

* ``--config, -c``: Configuration file path (YAML, JSON, or INI)
* ``--log-level``: Set logging level (DEBUG, INFO, WARNING, ERROR)
* ``--quiet, -q``: Suppress non-error output
* ``--verbose, -v``: Enable verbose output

Return Codes
-----------

The CLI returns the following exit codes:

* ``0``: Success
* ``1``: General error
* ``130``: Operation cancelled by user (KeyboardInterrupt)

Integration with Other Modules
-----------------------------

The CLI integrates with other modules of the migration tool:

* ``AltiumDbLibParser``: For parsing Altium database files
* ``ComponentMappingEngine`` and ``AdvancedMappingEngine``: For mapping components
* ``KiCADDbLibGenerator``: For generating KiCAD database files
* ``ConfigurationManager``: For managing configuration
* ``MigrationValidator``: For validating migration results

See Also
--------

* :doc:`core` - Core API documentation
* :doc:`gui` - GUI API documentation
* :doc:`utils` - Utility functions documentation