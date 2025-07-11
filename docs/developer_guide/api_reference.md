# API Reference

This document provides comprehensive documentation for the Altium to KiCAD Database Migration Tool API. It covers all public classes, methods, and functions that developers can use to integrate with or extend the tool.

## Core API

### MigrationAPI

The main entry point for programmatic use of the migration tool.

```python
from migration_tool import MigrationAPI

api = MigrationAPI()
result = api.run_migration(config)
```

#### Constructor

```python
MigrationAPI(logger=None, config_manager=None)
```

**Parameters:**
- `logger` (optional): Custom logger instance. If not provided, a default logger will be created.
- `config_manager` (optional): Custom configuration manager. If not provided, a default configuration manager will be created.

#### Methods

##### run_migration

```python
run_migration(config)
```

Runs a complete migration process with the provided configuration.

**Parameters:**
- `config`: Dictionary containing migration configuration or path to a YAML configuration file.

**Returns:**
- Dictionary with migration results containing:
  - `success`: Boolean indicating if migration was successful
  - `output_path`: Path to the generated output
  - `component_count`: Number of components processed
  - `success_count`: Number of components successfully migrated
  - `warning_count`: Number of warnings generated
  - `error_count`: Number of errors encountered
  - `report_path`: Path to the generated report
  - `log_path`: Path to the log file
  - `duration`: Migration duration in seconds
  - `error`: Error message if migration failed

**Example:**

```python
config = {
    'input_path': 'path/to/library.DbLib',
    'output_directory': 'output/',
    'library_name': 'MyLibrary',
    'parallel_processing': True,
    'max_workers': 4
}

result = api.run_migration(config)

if result['success']:
    print(f"Migration successful! Output at: {result['output_path']}")
    print(f"Processed {result['component_count']} components")
    print(f"Success: {result['success_count']}, Warnings: {result['warning_count']}")
else:
    print(f"Migration failed: {result['error']}")
```

##### parse_altium_database

```python
parse_altium_database(input_path, connection_params=None)
```

Parses an Altium database and returns the extracted components.

**Parameters:**
- `input_path`: Path to the Altium DbLib file or database connection string.
- `connection_params` (optional): Additional connection parameters.

**Returns:**
- List of extracted components.

**Example:**

```python
components = api.parse_altium_database('path/to/library.DbLib')
print(f"Found {len(components)} components")
```

##### map_components

```python
map_components(components, mapping_config=None)
```

Maps Altium components to KiCAD equivalents.

**Parameters:**
- `components`: List of components to map.
- `mapping_config` (optional): Mapping configuration.

**Returns:**
- List of mapped components.

**Example:**

```python
components = api.parse_altium_database('path/to/library.DbLib')
mapped_components = api.map_components(components)
```

##### generate_kicad_library

```python
generate_kicad_library(mapped_components, output_directory, library_name, output_format='sqlite')
```

Generates a KiCAD library from mapped components.

**Parameters:**
- `mapped_components`: List of mapped components.
- `output_directory`: Directory to save the generated library.
- `library_name`: Name of the generated library.
- `output_format` (optional): Output format (default: 'sqlite').

**Returns:**
- Path to the generated library.

**Example:**

```python
components = api.parse_altium_database('path/to/library.DbLib')
mapped_components = api.map_components(components)
output_path = api.generate_kicad_library(mapped_components, 'output/', 'MyLibrary')
```

##### validate_mapping

```python
validate_mapping(mapped_components, validation_config=None)
```

Validates component mappings against KiCAD libraries.

**Parameters:**
- `mapped_components`: List of mapped components to validate.
- `validation_config` (optional): Validation configuration.

**Returns:**
- Validation results.

**Example:**

```python
components = api.parse_altium_database('path/to/library.DbLib')
mapped_components = api.map_components(components)
validation_results = api.validate_mapping(mapped_components)
```

##### generate_report

```python
generate_report(migration_results, report_path, report_format='html')
```

Generates a migration report.

**Parameters:**
- `migration_results`: Results from the migration process.
- `report_path`: Path to save the report.
- `report_format` (optional): Report format (default: 'html').

**Returns:**
- Path to the generated report.

**Example:**

```python
result = api.run_migration(config)
report_path = api.generate_report(result, 'output/report.html')
```

## Parser Module

### AltiumDbLibParser

Parses Altium DbLib files and extracts connection information.

```python
from migration_tool.core.altium_parser import AltiumDbLibParser

parser = AltiumDbLibParser()
connection_info = parser.parse_dblib('path/to/library.DbLib')
```

#### Constructor

```python
AltiumDbLibParser(logger=None)
```

**Parameters:**
- `logger` (optional): Custom logger instance.

#### Methods

##### parse_dblib

```python
parse_dblib(dblib_path)
```

Parses an Altium DbLib file.

**Parameters:**
- `dblib_path`: Path to the DbLib file.

**Returns:**
- Dictionary with connection information.

##### extract_components

```python
extract_components(connection_info)
```

Extracts components using the connection information.

**Parameters:**
- `connection_info`: Connection information from parse_dblib.

**Returns:**
- List of extracted components.

### DatabaseConnector

Base class for database connectors.

```python
from migration_tool.core.altium_parser import DatabaseConnector

# This is an abstract base class, use a concrete implementation
```

#### Methods

##### connect

```python
connect()
```

Establishes a database connection.

**Returns:**
- Database connection object.

##### execute_query

```python
execute_query(query, params=None)
```

Executes a database query.

**Parameters:**
- `query`: SQL query string.
- `params` (optional): Query parameters.

**Returns:**
- Query results.

### SQLiteDatabaseConnector

SQLite database connector implementation.

```python
from migration_tool.core.altium_parser import SQLiteDatabaseConnector

connector = SQLiteDatabaseConnector('path/to/database.sqlite')
connection = connector.connect()
```

## Mapping Module

### MappingEngine

Maps Altium components to KiCAD equivalents.

```python
from migration_tool.core.mapping_engine import MappingEngine

engine = MappingEngine(config_manager)
mapped_components = engine.map_components(components)
```

#### Constructor

```python
MappingEngine(config_manager, logger=None, cache_manager=None)
```

**Parameters:**
- `config_manager`: Configuration manager instance.
- `logger` (optional): Custom logger instance.
- `cache_manager` (optional): Cache manager for mapping results.

#### Methods

##### map_components

```python
map_components(components)
```

Maps a list of components.

**Parameters:**
- `components`: List of components to map.

**Returns:**
- List of mapped components.

##### load_mapping_rules

```python
load_mapping_rules(rules_path)
```

Loads mapping rules from a file.

**Parameters:**
- `rules_path`: Path to the mapping rules file.

**Returns:**
- Loaded mapping rules.

##### add_custom_rule

```python
add_custom_rule(rule_type, altium_pattern, kicad_value, confidence=0.8)
```

Adds a custom mapping rule.

**Parameters:**
- `rule_type`: Type of rule ('symbol', 'footprint', or 'category').
- `altium_pattern`: Regex pattern to match Altium values.
- `kicad_value`: Corresponding KiCAD value.
- `confidence`: Confidence score for this rule.

**Returns:**
- None

**Example:**

```python
engine = MappingEngine(config_manager)
engine.add_custom_rule('symbol', 'RES.*', 'Device:R', 0.9)
engine.add_custom_rule('footprint', 'SOIC-8', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 0.95)
```

## Generator Module

### KiCADDbLibGenerator

Generates KiCAD database libraries.

```python
from migration_tool.core.kicad_generator import KiCADDbLibGenerator

generator = KiCADDbLibGenerator(config_manager)
output_path = generator.generate_library(mapped_components, 'output/', 'MyLibrary')
```

#### Constructor

```python
KiCADDbLibGenerator(config_manager, logger=None)
```

**Parameters:**
- `config_manager`: Configuration manager instance.
- `logger` (optional): Custom logger instance.

#### Methods

##### generate_library

```python
generate_library(mapped_components, output_directory, library_name, output_format='sqlite')
```

Generates a KiCAD library.

**Parameters:**
- `mapped_components`: List of mapped components.
- `output_directory`: Directory to save the generated library.
- `library_name`: Name of the generated library.
- `output_format` (optional): Output format (default: 'sqlite').

**Returns:**
- Path to the generated library.

##### create_schema

```python
create_schema(connection)
```

Creates the database schema.

**Parameters:**
- `connection`: Database connection.

**Returns:**
- None

## Utility Modules

### ConfigManager

Manages configuration loading and validation.

```python
from migration_tool.utils.config_manager import ConfigManager

config_manager = ConfigManager()
config = config_manager.load_config('path/to/config.yaml')
```

#### Constructor

```python
ConfigManager(default_config_path=None)
```

**Parameters:**
- `default_config_path` (optional): Path to the default configuration file.

#### Methods

##### load_config

```python
load_config(config_path=None)
```

Loads configuration from a file.

**Parameters:**
- `config_path` (optional): Path to the configuration file.

**Returns:**
- Loaded configuration.

##### validate_config

```python
validate_config(config)
```

Validates a configuration.

**Parameters:**
- `config`: Configuration to validate.

**Returns:**
- Validated configuration.

##### merge_configs

```python
merge_configs(base_config, override_config)
```

Merges two configurations.

**Parameters:**
- `base_config`: Base configuration.
- `override_config`: Configuration to override base values.

**Returns:**
- Merged configuration.

### LoggingUtils

Configures logging for all components.

```python
from migration_tool.utils.logging_utils import setup_logger

logger = setup_logger('my_logger', log_level='INFO', log_file='migration.log')
```

#### Functions

##### setup_logger

```python
setup_logger(name, log_level='INFO', log_file=None, console=True)
```

Sets up a logger.

**Parameters:**
- `name`: Logger name.
- `log_level` (optional): Logging level (default: 'INFO').
- `log_file` (optional): Path to log file.
- `console` (optional): Whether to log to console (default: True).

**Returns:**
- Configured logger.

### DatabaseUtils

Provides database utility functions.

```python
from migration_tool.utils.database_utils import create_connection

connection = create_connection('sqlite:///database.sqlite')
```

#### Functions

##### create_connection

```python
create_connection(connection_string)
```

Creates a database connection.

**Parameters:**
- `connection_string`: Database connection string.

**Returns:**
- Database connection.

##### execute_query

```python
execute_query(connection, query, params=None)
```

Executes a database query.

**Parameters:**
- `connection`: Database connection.
- `query`: SQL query string.
- `params` (optional): Query parameters.

**Returns:**
- Query results.

## Configuration Reference

### Complete Configuration Example

```yaml
# Input configuration
input:
  path: path/to/library.DbLib
  connection_timeout: 30
  credentials:
    username: user
    password: pass
    use_environment_vars: false

# Output configuration
output:
  directory: output/
  library_name: MyLibrary
  format: sqlite
  backup_existing: true
  create_report: true
  report_format: html

# Mapping settings
mapping:
  confidence_threshold: 0.7
  use_custom_rules: true
  custom_rules_path: path/to/custom_rules.yaml
  low_confidence_action: warn  # warn, skip, or placeholder

# Validation settings
validation:
  validate_symbols: true
  validate_footprints: true
  kicad_symbol_lib_path: /path/to/kicad/symbols
  kicad_footprint_lib_path: /path/to/kicad/footprints
  report_missing: true
  create_missing: false

# Performance settings
performance:
  parallel_processing: true
  max_workers: 4
  batch_size: 100
  cache_results: true
  cache_path: cache/
  memory_limit: 2048  # MB

# Logging settings
logging:
  log_level: INFO
  log_file: migration.log
  console: true
  log_format: detailed  # simple or detailed
```

## Error Handling

### Exception Hierarchy

```
MigrationError
├── ConfigurationError
├── DatabaseError
│   ├── ConnectionError
│   └── QueryError
├── ParsingError
├── MappingError
├── ValidationError
└── GenerationError
```

### Handling Errors

```python
from migration_tool import MigrationAPI
from migration_tool.exceptions import MigrationError, DatabaseError

api = MigrationAPI()

try:
    result = api.run_migration(config)
except DatabaseError as e:
    print(f"Database error: {e}")
    # Handle database-specific errors
except MigrationError as e:
    print(f"Migration error: {e}")
    # Handle general migration errors
```

## Advanced Usage Examples

### Custom Mapping Algorithm

```python
from migration_tool import MigrationAPI
from migration_tool.core.mapping_engine import MappingEngine, MappingRule

class CustomMappingEngine(MappingEngine):
    def __init__(self, config_manager, logger=None, cache_manager=None):
        super().__init__(config_manager, logger, cache_manager)
        
    def map_component(self, component):
        # Custom mapping logic
        # ...
        return mapped_component

# Use the custom mapping engine
api = MigrationAPI()
components = api.parse_altium_database('path/to/library.DbLib')

# Create custom mapping engine
custom_engine = CustomMappingEngine(api._config_manager, api._logger)
mapped_components = custom_engine.map_components(components)

# Continue with generation
output_path = api.generate_kicad_library(mapped_components, 'output/', 'MyLibrary')
```

### Batch Processing with Progress Reporting

```python
from migration_tool import MigrationAPI
from tqdm import tqdm
import os

api = MigrationAPI()

# Get list of DbLib files
dblib_files = [f for f in os.listdir('libraries/') if f.endswith('.DbLib')]

# Process each file with progress bar
for dblib_file in tqdm(dblib_files, desc="Processing libraries"):
    config = {
        'input_path': f'libraries/{dblib_file}',
        'output_directory': 'output/',
        'library_name': os.path.splitext(dblib_file)[0]
    }
    
    try:
        result = api.run_migration(config)
        if result['success']:
            tqdm.write(f"Successfully migrated {dblib_file}")
        else:
            tqdm.write(f"Failed to migrate {dblib_file}: {result['error']}")
    except Exception as e:
        tqdm.write(f"Error processing {dblib_file}: {str(e)}")
```

### Integration with Web Application

```python
from flask import Flask, request, jsonify
from migration_tool import MigrationAPI
import os

app = Flask(__name__)
api = MigrationAPI()

@app.route('/migrate', methods=['POST'])
def migrate():
    # Get parameters from request
    input_path = request.form.get('input_path')
    output_dir = request.form.get('output_directory', 'output/')
    library_name = request.form.get('library_name')
    
    # Validate inputs
    if not input_path or not os.path.exists(input_path):
        return jsonify({'error': 'Invalid input path'}), 400
    
    if not library_name:
        library_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # Create configuration
    config = {
        'input_path': input_path,
        'output_directory': output_dir,
        'library_name': library_name
    }
    
    # Run migration
    try:
        result = api.run_migration(config)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

## API Versioning

The API follows semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR version changes indicate incompatible API changes
- MINOR version changes add functionality in a backward-compatible manner
- PATCH version changes make backward-compatible bug fixes

To check the current API version:

```python
from migration_tool import __version__

print(f"Migration Tool API version: {__version__}")