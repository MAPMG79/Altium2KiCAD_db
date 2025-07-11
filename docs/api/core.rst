Core API
=======

The Core API provides the fundamental functionality for the Altium to KiCAD Database Migration Tool. It includes classes for parsing Altium databases, mapping components, generating KiCAD libraries, and handling errors.

Overview
--------

The Core API consists of several key components:

* **Main Migration Application**: The central application that coordinates the migration process
* **Sample Data Generation**: Utilities for generating test data
* **Error Handling**: Advanced error handling and recovery mechanisms
* **Component Type Definitions**: Enumerations and data classes for component types

Main Migration Application
-------------------------

The main migration application is implemented in Python using Tkinter for the GUI. It imports several key modules:

.. code-block:: python

   import tkinter as tk
   from tkinter import ttk, filedialog, messagebox, scrolledtext
   import threading
   import json
   import os
   from pathlib import Path
   import sys
   import logging
   from datetime import datetime

Component Types
--------------

The ``ComponentType`` enumeration defines the types of components that can be migrated:

.. code-block:: python

   class ComponentType(Enum):
       """Enumeration of component types for sample generation"""
       RESISTOR = "resistor"
       CAPACITOR = "capacitor"
       INDUCTOR = "inductor"
       DIODE = "diode"
       TRANSISTOR = "transistor"
       IC = "ic"
       CONNECTOR = "connector"
       CRYSTAL = "crystal"

This enumeration is used throughout the application for categorizing components, generating sample data, and applying appropriate mapping rules.

Error Handling
-------------

The ``ErrorInfo`` data class stores information about errors that occur during migration:

.. code-block:: python

   @dataclass
   class ErrorInfo:
       """Information about an error that occurred during migration"""
       error_type: str
       message: str
       component_data: Optional[Dict[str, Any]]
       table_name: Optional[str]
       timestamp: str
       traceback_info: Optional[str]
       severity: str  # 'low', 'medium', 'high', 'critical'

The ``ErrorHandler`` class provides advanced error handling and recovery mechanisms:

.. code-block:: python

   class ErrorHandler:
       """Advanced error handling and recovery for migration operations"""
       
       def __init__(self, log_file: str = "migration_errors.json"):
           self.log_file = Path(log_file)
           self.errors: List[ErrorInfo] = []
           self.error_stats = {
               'total_errors': 0,
               'by_severity': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
               'by_type': {},
               'by_table': {}
           }
           self.recovery_strategies = self._initialize_recovery_strategies()

Key methods of the ``ErrorHandler`` class include:

* ``handle_error``: Handles an error with automatic recovery attempts
* ``_determine_severity``: Determines error severity based on type and message
* ``_log_error``: Logs error information
* ``_attempt_recovery``: Attempts to recover from an error
* ``save_error_log``: Saves error log to file
* ``generate_error_report``: Generates a comprehensive error report

Sample Data Generation
--------------------

The ``SampleDataGenerator`` class generates realistic sample data for testing:

.. code-block:: python

   class SampleDataGenerator:
       """Generate realistic sample data for testing migration tools"""
       
       def __init__(self, output_dir: str):
           self.output_dir = Path(output_dir)
           self.output_dir.mkdir(parents=True, exist_ok=True)
           
           # Component specifications
           self.component_specs = self._initialize_component_specs()
           
           # Manufacturers
           self.manufacturers = [
               "Vishay", "Yageo", "Murata", "TDK", "Samsung", "Panasonic",
               "Texas Instruments", "Analog Devices", "Maxim", "Linear Technology",
               "STMicroelectronics", "NXP", "Infineon", "ON Semiconductor",
               "Microchip", "Atmel", "Intel", "Broadcom", "Qualcomm"
           ]

Key methods of the ``SampleDataGenerator`` class include:

* ``generate_component``: Generates a single realistic component
* ``generate_table_data``: Generates a table of components
* ``create_sample_database``: Creates a sample SQLite database with realistic data
* ``create_sample_dblib``: Creates a sample Altium .DbLib file
* ``generate_complete_sample``: Generates a complete sample project with database and DbLib file

Component Generation
~~~~~~~~~~~~~~~~~~

The ``generate_component`` method creates realistic component data:

.. code-block:: python

   def generate_component(self, comp_type: ComponentType, part_number_prefix: str = None) -> Dict[str, Any]:
       """Generate a single realistic component"""
       specs = self.component_specs[comp_type]
       manufacturer = random.choice(self.manufacturers)
       package = random.choice(self.packages[comp_type])
       
       # Generate part number
       if not part_number_prefix:
           part_number_prefix = f"{comp_type.value[:3].upper()}"
       
       part_number = f"{part_number_prefix}-{random.randint(1000, 9999)}-{package}"
       
       # Base component data
       component = {
           'Part Number': part_number,
           'Symbol': specs['symbol'],
           'Footprint': package,
           'Manufacturer': manufacturer,
           'Manufacturer Part Number': f"{manufacturer[:3].upper()}{random.randint(1000, 9999)}",
           'Package': package,
           'Description': self._generate_description(comp_type, specs),
           'Datasheet': f"https://www.{manufacturer.lower().replace(' ', '')}.com/ds/{part_number}.pdf",
           'Supplier': random.choice(['Digi-Key', 'Mouser', 'Arrow', 'Avnet', 'RS Components']),
           'Supplier Part Number': f"SP{random.randint(100000, 999999)}",
           'Comment': f"{comp_type.value.title()} component"
       }

Database Creation
~~~~~~~~~~~~~~~

The ``create_sample_database`` method creates a SQLite database with sample data:

.. code-block:: python

   def create_sample_database(self, db_path: str, table_configs: Dict[str, Dict[str, Any]]) -> str:
       """Create sample SQLite database with realistic data"""
       conn = sqlite3.connect(db_path)
       cursor = conn.cursor()
       
       for table_name, config in table_configs.items():
           component_count = config.get('component_count', 50)
           component_types = config.get('component_types', list(ComponentType))
           
           # Generate component data
           components = self.generate_table_data(table_name, component_count, component_types)
           
           if components:
               # Create table based on first component's fields
               fields = list(components[0].keys())
               escaped_fields = [f'[{field}]' for field in fields]
               
               create_sql = f"""
                   CREATE TABLE IF NOT EXISTS [{table_name}] (
                       {', '.join(f'{field} TEXT' for field in escaped_fields)}
                   )
               """
               cursor.execute(create_sql)
               
               # Insert components
               placeholders = ', '.join(['?' for _ in fields])
               insert_sql = f"INSERT INTO [{table_name}] VALUES ({placeholders})"
               
               for component in components:
                   values = [component.get(field, '') for field in fields]
                   cursor.execute(insert_sql, values)

DbLib File Creation
~~~~~~~~~~~~~~~~~

The ``create_sample_dblib`` method creates an Altium .DbLib file:

.. code-block:: python

   def create_sample_dblib(self, dblib_path: str, db_path: str, 
                          table_configs: Dict[str, Dict[str, Any]]) -> str:
       """Create sample Altium .DbLib file"""
       config = configparser.ConfigParser()
       
       # Database connection section
       config['DatabaseLinks'] = {
           'ConnectionString': f'Driver=SQLite3;Database={db_path};',
           'AddMode': '3',
           'RemoveMode': '1',
           'UpdateMode': '2',
           'ViewMode': '0',
           'LeftQuote': '[',
           'RightQuote': ']',
           'QuoteTableNames': '1',
           'UseTableSchemaName': '0',
           'DefaultColumnType': 'VARCHAR(255)',
           'LibraryDatabaseType': '',
           'LibraryDatabasePath': '',
           'DatabasePathRelative': '0'
       }

Error Recovery Strategies
-----------------------

The ``ErrorHandler`` class implements several recovery strategies for different types of errors:

Database Connection Errors
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def _recover_database_connection(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
       """Attempt to recover from database connection errors"""
       # Try alternative connection methods
       attempts = [
           {'timeout': 60},  # Increase timeout
           {'readonly': True},  # Try read-only access
           {'pooling': False}  # Disable connection pooling
       ]
       
       for attempt in attempts:
           try:
               # This would use actual connection logic
               logging.info(f"Attempting database recovery with: {attempt}")
               # return recovered_connection
               pass
           except Exception:
               continue
       
       return None

Component Mapping Errors
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def _recover_component_mapping(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
       """Attempt to recover from component mapping errors"""
       if context and 'component_data' in context:
           component = context['component_data']
           
           # Provide fallback mapping
           fallback_mapping = {
               'altium_symbol': component.get('Symbol', 'Unknown'),
               'kicad_symbol': 'Device:R',  # Safe fallback
               'kicad_footprint': 'Resistor_SMD:R_0603_1608Metric',  # Safe fallback
               'confidence': 0.1,  # Low confidence for fallback
               'field_mappings': {
                   'Description': component.get('Description', 'Unknown Component'),
                   'Value': component.get('Value', ''),
                   'MPN': component.get('Manufacturer Part Number', '')
               },
               'recovery_used': True
           }
           
           return fallback_mapping

Symbol and Footprint Errors
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def _recover_symbol_not_found(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
       """Recover from symbol not found errors"""
       # Return generic symbol based on component type
       generic_symbols = {
           'resistor': 'Device:R',
           'capacitor': 'Device:C', 
           'inductor': 'Device:L',
           'diode': 'Device:D',
           'transistor': 'Device:Q_NPN_BCE'
       }
       
       if context and 'component_data' in context:
           description = context['component_data'].get('Description', '').lower()
           for comp_type, symbol in generic_symbols.items():
               if comp_type in description:
                   return symbol
       
       return 'Device:R'  # Ultimate fallback

Data Validation Errors
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def _recover_data_validation(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
       """Recover from data validation errors"""
       if context and 'component_data' in context:
           component = context['component_data']
           
           # Clean and validate data
           cleaned_component = {}
           for key, value in component.items():
               if value is not None and str(value).strip():
                   # Remove problematic characters
                   cleaned_value = str(value).replace('\x00', '').strip()
                   if len(cleaned_value) > 255:  # Truncate long values
                       cleaned_value = cleaned_value[:252] + '...'
                   cleaned_component[key] = cleaned_value
           
           return cleaned_component

Error Reporting
-------------

The ``generate_error_report`` method generates a comprehensive error report:

.. code-block:: python

   def generate_error_report(self) -> Dict[str, Any]:
       """Generate comprehensive error report"""
       return {
           'summary': self.error_stats,
           'recent_errors': [
               {
                   'type': e.error_type,
                   'message': e.message,
                   'severity': e.severity,
                   'timestamp': e.timestamp
               }
               for e in self.errors[-10:]  # Last 10 errors
           ],
           'recommendations': self._generate_recommendations()
       }

The ``_generate_recommendations`` method generates recommendations based on error patterns:

.. code-block:: python

   def _generate_recommendations(self) -> List[str]:
       """Generate recommendations based on error patterns"""
       recommendations = []
       
       # Check for common error patterns
       if self.error_stats['by_severity']['critical'] > 0:
           recommendations.append("Critical errors detected. Check database connectivity and file permissions.")
       
       if self.error_stats['by_type'].get('ConnectionError', 0) > 5:
           recommendations.append("Frequent connection errors. Consider increasing timeout values.")
       
       if self.error_stats['by_type'].get('MappingError', 0) > 10:
           recommendations.append("Many mapping errors. Consider updating symbol/footprint libraries.")
       
       if self.error_stats['total_errors'] > 100:
           recommendations.append("High error count. Consider preprocessing data or using batch mode.")
       
       return recommendations

Integration with Other Modules
-----------------------------

The Core API integrates with other modules of the migration tool:

* ``CLI``: Command-line interface for migration operations
* ``GUI``: Graphical user interface for migration operations
* ``Utils``: Utility functions for logging, configuration, and database operations

See Also
--------

* :doc:`cli` - Command Line Interface documentation
* :doc:`gui` - Graphical User Interface documentation
* :doc:`utils` - Utility functions documentation