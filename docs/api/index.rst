API Reference
=============

This section provides detailed API documentation for the Altium to KiCAD Database Migration Tool.

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   
   core
   utils
   cli
   gui

Main API
-------

.. automodule:: migration_tool
   :members:
   :undoc-members:
   :show-inheritance:

The main entry point for programmatic use of the migration tool is the ``MigrationAPI`` class:

.. code-block:: python

   from migration_tool import MigrationAPI
   
   # Initialize the API
   api = MigrationAPI()
   
   # Configure migration
   config = {
       'input_path': 'path/to/library.DbLib',
       'output_directory': 'output/',
       'library_name': 'MyLibrary',
       'validate_symbols': True,
       'validate_footprints': True
   }
   
   # Run migration
   result = api.run_migration(config)
   
   # Print summary
   print(f"Migration complete! {result['success_count']} components migrated successfully.")

Module Structure
--------------

The migration tool is organized into the following modules:

- **Core Modules**: Core functionality for parsing, mapping, and generating
  - ``migration_tool.core.altium_parser``: Parsing Altium DbLib files and databases
  - ``migration_tool.core.mapping_engine``: Mapping Altium components to KiCAD equivalents
  - ``migration_tool.core.kicad_generator``: Generating KiCAD database libraries

- **Utility Modules**: Supporting functionality
  - ``migration_tool.utils.config_manager``: Configuration management
  - ``migration_tool.utils.database_utils``: Database connection and query utilities
  - ``migration_tool.utils.logging_utils``: Logging configuration and utilities

- **Interface Modules**: User interfaces
  - ``migration_tool.cli``: Command-line interface
  - ``migration_tool.gui``: Graphical user interface

Exception Hierarchy
-----------------

The migration tool defines a hierarchy of exceptions for error handling:

.. code-block:: python

   class MigrationError(Exception):
       """Base class for all migration errors."""
       pass
   
   class ConfigurationError(MigrationError):
       """Error in configuration."""
       pass
   
   class DatabaseError(MigrationError):
       """Error with database operations."""
       pass
   
   class ConnectionError(DatabaseError):
       """Error connecting to a database."""
       pass
   
   class QueryError(DatabaseError):
       """Error executing a database query."""
       pass
   
   class ParsingError(MigrationError):
       """Error parsing Altium data."""
       pass
   
   class MappingError(MigrationError):
       """Error during component mapping."""
       pass
   
   class ValidationError(MigrationError):
       """Error during validation."""
       pass
   
   class GenerationError(MigrationError):
       """Error generating KiCAD library."""
       pass