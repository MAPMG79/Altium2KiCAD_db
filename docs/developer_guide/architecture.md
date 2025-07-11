# System Architecture

This document provides a comprehensive overview of the Altium to KiCAD Database Migration Tool architecture, explaining the core components, their interactions, and the design principles that guide the implementation.

## High-Level Architecture

The Altium to KiCAD Database Migration Tool follows a modular, layered architecture designed for flexibility, extensibility, and maintainability. The system is divided into several key components that work together to perform the migration process.

### Architecture Overview

The migration tool is built around a core set of components that handle different aspects of the migration process:

```python
# High-level architecture
class AltiumToKiCADMigrator:
    def __init__(self):
        self.altium_parser = AltiumDbLibParser()
        self.kicad_generator = KiCADDbLibGenerator()
        self.mapping_engine = ComponentMappingEngine()
        self.database_migrator = DatabaseMigrator()
    
    def migrate(self, altium_dblib_path, output_config):
        # Parse Altium configuration
        altium_config = self.altium_parser.parse(altium_dblib_path)
        
        # Extract database schema and data
        source_data = self.extract_altium_data(altium_config)
        
        # Map components and resolve libraries
        mapped_data = self.mapping_engine.map_components(source_data)
        
        # Generate KiCAD database and configuration
        return self.kicad_generator.generate(mapped_data, output_config)
```

This architecture addresses the key migration challenges:
1. Different database schemas
2. Symbol/footprint referencing systems
3. Field mapping and naming conventions
4. Library path resolution
5. Component parameter structures

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
│                                                             │
│  ┌───────────────┐                     ┌───────────────┐    │
│  │  Command Line │                     │  Graphical UI │    │
│  │   Interface   │                     │   Interface   │    │
│  └───────┬───────┘                     └───────┬───────┘    │
└─────────┬─────────────────────────────────────┬─────────────┘
          │                                     │
          ▼                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Migration API                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Core Migration Logic                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────┬─────────────────────────────────────────┬─────────┘
          │                                         │
          ▼                                         ▼
┌─────────────────────┐                 ┌─────────────────────┐
│                     │                 │                     │
│   Altium Parser     │                 │  KiCAD Generator    │
│                     │                 │                     │
└─────────┬───────────┘                 └─────────┬───────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────┐                 ┌─────────────────────┐
│                     │                 │                     │
│   Mapping Engine    │◄────────────────┤  Validation Engine  │
│                     │                 │                     │
└─────────┬───────────┘                 └─────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Utility Services                         │
│                                                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
│  │ Database  │  │   Config  │  │  Logging  │  │  Caching  │ │
│  │  Utils    │  │  Manager  │  │   Utils   │  │   Utils   │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. User Interfaces

The tool provides two main interfaces for user interaction:

#### Command Line Interface (CLI)

- Implemented in `migration_tool/cli.py`
- Provides command-line arguments for all migration options
- Designed for automation, scripting, and batch processing
- Uses argparse for argument parsing and validation

#### Graphical User Interface (GUI)

- Implemented in `migration_tool/gui.py`
- Provides a user-friendly interface with step-by-step workflow
- Built with Tkinter for cross-platform compatibility
- Includes progress visualization and interactive mapping

### 2. Migration API

- Implemented in `migration_tool/__init__.py`
- Serves as the main entry point for programmatic use
- Coordinates the migration process
- Provides a clean, high-level interface for all migration operations
- Handles configuration validation and error management

### 3. Altium Parser

- Implemented in `migration_tool/core/altium_parser.py`
- Responsible for parsing Altium DbLib files and connecting to databases
- Extracts component data, symbols, footprints, and metadata
- Supports multiple database types (SQLite, MySQL, PostgreSQL, MS SQL)
- Implements connection pooling and query optimization

#### Key Classes:

- `AltiumDbLibParser`: Parses DbLib files and extracts connection information
- `AltiumDatabaseConnector`: Manages database connections and query execution
- `AltiumComponentExtractor`: Extracts component data from the database

#### Implementation Details:

The Altium Parser is responsible for reading Altium's `.DbLib` files, which are essentially INI-format configuration files that define database connections and table mappings. The parser handles different database types and connection strings:

```python
def _detect_database_type(self) -> str:
    """Detect database type from connection string"""
    conn_str = self.connection_string.lower()
    if 'microsoft.ace.oledb' in conn_str or '.mdb' in conn_str:
        return 'access'
    elif 'sql server' in conn_str or 'sqlserver' in conn_str:
        return 'sqlserver'
    elif 'sqlite' in conn_str:
        return 'sqlite'
    elif 'mysql' in conn_str:
        return 'mysql'
    elif 'postgresql' in conn_str:
        return 'postgresql'
    else:
        return 'unknown'
```

For a complete implementation example, see [altium_parser.py](../examples/code_snippets/altium_parser.py).

### 4. Mapping Engine

- Implemented in `migration_tool/core/mapping_engine.py`
- Maps Altium components to KiCAD equivalents
- Uses pattern matching, heuristics, and custom rules
- Calculates confidence scores for each mapping
- Supports custom mapping rules via YAML configuration

#### Key Classes:

- `MappingEngine`: Main class that orchestrates the mapping process
- `SymbolMapper`: Maps Altium symbols to KiCAD symbols
- `FootprintMapper`: Maps Altium footprints to KiCAD footprints
- `CategoryMapper`: Maps Altium categories to KiCAD categories
- `MappingRule`: Represents a single mapping rule
- `MappingResult`: Contains the result of a mapping operation

#### Implementation Details:

The Mapping Engine is the heart of the migration process, responsible for translating Altium component references to KiCAD equivalents. It uses a combination of techniques:

```python
@dataclass
class ComponentMapping:
    """Data class for component mapping information"""
    altium_symbol: str
    altium_footprint: str
    kicad_symbol: str
    kicad_footprint: str
    confidence: float
    field_mappings: Dict[str, str]
```

The engine employs a multi-strategy approach for mapping symbols and footprints:

```python
def map_symbol(self, altium_symbol: str, component_data: Dict[str, Any]) -> str:
    """Map Altium symbol to KiCAD symbol"""
    # Direct mapping check
    if altium_symbol in self.symbol_mappings:
        return self.symbol_mappings[altium_symbol]
    
    # Component type-based mapping
    description = component_data.get('Description', '').lower()
    value = component_data.get('Value', '').lower()
    
    for comp_type, mapping in self.component_type_mappings.items():
        for pattern in mapping.get('symbol_patterns', []):
            if re.search(pattern, description) or re.search(pattern, value):
                kicad_symbol = mapping['kicad_symbol']
                # Cache the mapping
                self.symbol_mappings[altium_symbol] = kicad_symbol
                return kicad_symbol
    
    # Fallback: try to find similar KiCAD symbol
    return self._find_similar_symbol(altium_symbol, component_data)
```

The engine also handles field mapping between Altium and KiCAD formats, ensuring that component metadata is properly transferred.

For a complete implementation example, see [mapping_engine.py](../examples/code_snippets/mapping_engine.py) and [advanced_mapping.py](../examples/code_snippets/advanced_mapping.py).
### 5. KiCAD Generator

- Implemented in `migration_tool/core/kicad_generator.py`
- Generates KiCAD-compatible database libraries
- Creates SQLite database with proper schema
- Handles field mapping and data transformation
- Supports multiple output formats

#### Key Classes:

- `KiCADDbLibGenerator`: Main class for generating KiCAD database libraries
- `SQLiteGenerator`: Generates SQLite database files
- `SchemaManager`: Manages database schema creation and updates
- `ComponentWriter`: Writes component data to the output database

#### Implementation Details:

The KiCAD Generator is responsible for creating KiCAD-compatible database libraries from the mapped component data. It handles database schema creation, component categorization, and configuration file generation:

```python
def create_database_schema(self) -> None:
    """Create SQLite database with KiCAD-compatible schema"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Create categories table
    cursor.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            parent_id INTEGER REFERENCES categories(id)
        )
    """)
    
    # Create main components table
    cursor.execute("""
        CREATE TABLE components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            footprint TEXT NOT NULL,
            reference TEXT NOT NULL,
            value TEXT,
            description TEXT,
            keywords TEXT,
            manufacturer TEXT,
            mpn TEXT,
            datasheet TEXT,
            # Additional fields...
        )
    """)
```

The generator also creates specialized views for different component types, making it easier to browse and search for specific components in KiCAD:

```python
def _create_component_views(self, cursor) -> None:
    """Create views for different component categories"""
    
    # Resistors view
    cursor.execute("""
        CREATE VIEW resistors AS
        SELECT * FROM components
        WHERE LOWER(description) LIKE '%resistor%'
           OR symbol LIKE '%:R%'
           OR LOWER(keywords) LIKE '%resistor%'
    """)
    
    # Additional views for other component types...
```

For a complete implementation example, see [kicad_generator.py](../examples/code_snippets/kicad_generator.py).
### 6. Validation Engine

- Integrated within the mapping and generation components
- Validates symbols and footprints against KiCAD libraries
- Checks for missing or invalid references
- Generates validation reports
- Provides suggestions for fixing validation issues

### 7. Utility Services

#### Database Utilities

- Implemented in `migration_tool/utils/database_utils.py`
- Provides database connection management
- Implements query builders and executors
- Handles database-specific quirks and optimizations

#### Configuration Manager

- Implemented in `migration_tool/utils/config_manager.py`
- Manages configuration loading and validation
- Handles default configurations
- Supports environment-specific configurations
- Validates user-provided configuration

#### Implementation Details:

The Configuration Manager provides a centralized way to manage application settings, supporting multiple configuration formats and validation:

```python
@dataclass
class MigrationConfig:
    """Configuration settings for migration"""
    # Input settings
    altium_dblib_path: str = ""
    altium_db_type: str = "auto"  # auto, access, sqlserver, mysql, postgresql, sqlite
    connection_timeout: int = 30
    
    # Output settings
    output_directory: str = ""
    database_name: str = "components.db"
    dblib_name: str = "components.kicad_dbl"
    
    # Mapping settings
    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.7
    enable_semantic_matching: bool = True
    
    # Performance settings
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    batch_size: int = 1000
    enable_caching: bool = True
```

The manager supports loading configuration from various formats:

```python
def load_config(self) -> MigrationConfig:
    """Load configuration from file"""
    if self.config_path.exists():
        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.suffix.lower() == '.yaml':
                    config_data = yaml.safe_load(f)
                elif self.config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    # Try INI format
                    config_parser = configparser.ConfigParser()
                    config_parser.read(self.config_path)
                    config_data = {section: dict(config_parser[section])
                                  for section in config_parser.sections()}
```

For a complete implementation example, see [config_manager.py](../examples/code_snippets/config_manager.py).
#### Logging Utilities

- Implemented in `migration_tool/utils/logging_utils.py`
- Configures logging for all components
- Provides structured logging
- Supports multiple output formats (console, file, syslog)
- Implements log rotation and management

#### Caching Utilities

- Integrated within various components
- Implements caching for expensive operations
- Manages cache invalidation and expiration
- Supports disk-based and memory-based caching

## Data Flow

The migration process follows this general data flow:

1. **Configuration**: User provides configuration via CLI, GUI, or API
2. **Parsing**: Altium parser extracts component data from the source
3. **Mapping**: Mapping engine maps Altium components to KiCAD equivalents
4. **Validation**: Validation engine checks mappings for correctness
5. **Generation**: KiCAD generator creates the output library
6. **Reporting**: System generates reports and logs

## Design Principles

The architecture adheres to the following design principles:

### 1. Separation of Concerns

Each component has a well-defined responsibility, making the system easier to understand, test, and maintain.

### 2. Dependency Injection

Components receive their dependencies through constructors or methods, facilitating testing and allowing for flexible configuration.

```python
class MappingEngine:
    def __init__(self, config_manager, logger, cache_manager=None):
        self.config_manager = config_manager
        self.logger = logger
        self.cache_manager = cache_manager
```

### 3. Interface-Based Design

Components interact through well-defined interfaces, reducing coupling and enabling component substitution.

```python
class DatabaseConnector(ABC):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def execute_query(self, query, params=None):
        pass
```

### 4. Configuration Over Convention

The system uses explicit configuration rather than implicit conventions, making behavior more predictable and customizable.

### 5. Fail Fast and Validate Early

Input validation happens as early as possible, providing clear error messages and preventing cascading failures.

### 6. Comprehensive Logging

All components log their operations at appropriate levels, facilitating debugging and monitoring.

## Advanced Mapping Algorithms

The Altium to KiCAD Database Migration Tool implements sophisticated mapping algorithms to accurately match Altium components to their KiCAD equivalents. These algorithms are crucial for ensuring high-quality migrations with minimal manual intervention.

### Multi-Strategy Symbol Mapping

The mapping engine employs a multi-strategy approach to symbol mapping:

1. **Exact Matching**: Attempts to find direct 1:1 matches between Altium and KiCAD symbols
2. **Fuzzy String Matching**: Uses string similarity algorithms to find close matches
3. **Semantic Matching**: Analyzes component descriptions and attributes to determine appropriate symbols
4. **Pattern-Based Matching**: Applies regex patterns to identify component types
5. **Fallback Mechanism**: Provides sensible defaults when no good match is found

This layered approach ensures that even when exact matches aren't available, the system can still provide high-confidence mappings.

```python
def find_symbol_match(self, altium_symbol: str, component_data: Dict[str, any]) -> SymbolMatch:
    """Find best KiCAD symbol match using multiple strategies"""
    
    # Strategy 1: Exact match
    exact_match = self._find_exact_symbol_match(altium_symbol)
    if exact_match:
        return SymbolMatch(
            kicad_symbol=exact_match,
            confidence=1.0,
            match_type='exact',
            reasoning=f'Exact match found for {altium_symbol}'
        )
    
    # Strategy 2: Fuzzy string matching
    fuzzy_match = self._find_fuzzy_symbol_match(altium_symbol)
    if fuzzy_match and fuzzy_match[1] > 0.8:
        return SymbolMatch(
            kicad_symbol=fuzzy_match[0],
            confidence=fuzzy_match[1],
            match_type='fuzzy',
            reasoning=f'High confidence fuzzy match'
        )
    
    # Additional strategies follow...
```

### Confidence Scoring

Each mapping is assigned a confidence score between 0.0 and 1.0, indicating the system's certainty in the mapping. This allows:

- Automatic acceptance of high-confidence mappings
- Flagging of low-confidence mappings for manual review
- Prioritization of mapping issues to address

### Footprint Mapping

Similar to symbol mapping, footprint mapping employs multiple strategies:

1. **Package Size Extraction**: Identifies standard package sizes (0603, SOT-23, etc.)
2. **Library-Based Matching**: Maps to standard KiCAD footprint libraries
3. **Dimensional Analysis**: Compares physical dimensions when available

## Configuration Management

The system implements a robust configuration management approach to handle the complexity of migration settings and ensure reproducible results.

### Configuration Structure

Configuration is managed through a centralized `MigrationConfig` data class that includes settings for:

- Input/output paths and formats
- Database connection parameters
- Mapping algorithm settings
- Performance optimization options
- Field mapping rules
- Validation criteria

```python
@dataclass
class MigrationConfig:
    """Configuration settings for migration"""
    # Input settings
    altium_dblib_path: str = ""
    altium_db_type: str = "auto"
    connection_timeout: int = 30
    
    # Output settings
    output_directory: str = ""
    database_name: str = "components.db"
    dblib_name: str = "components.kicad_dbl"
    
    # Mapping settings
    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.7
    enable_semantic_matching: bool = True
    
    # Performance settings
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    batch_size: int = 1000
    enable_caching: bool = True
    
    # Additional settings...
```

### Configuration Loading

The system supports multiple configuration formats:

- YAML (preferred for human readability)
- JSON (for programmatic generation)
- INI (for compatibility with older systems)

Configuration can be loaded from files, environment variables, or programmatically set.

### Performance Optimization

The configuration system includes settings for performance optimization:

- Parallel processing options
- Batch size control
- Caching mechanisms
- Memory usage limits

These settings allow the system to be tuned for different environments, from developer laptops to high-performance servers.

## Extension Points

The architecture includes several extension points for customization:

### 1. Custom Mapping Rules

Developers can create custom mapping rules to improve mapping accuracy for specific components.

```yaml
symbols:
  - altium_pattern: "CUSTOM_.*"
    kicad_symbol: "Custom:Symbol"
    confidence: 0.9
```

### 2. Database Adapters

New database adapters can be added to support additional database types.

```python
@register_database_adapter("new_db_type")
class NewDatabaseAdapter(DatabaseAdapter):
    def connect(self, connection_string):
        # Implementation
```

### 3. Output Generators

Additional output generators can be implemented to support new formats.

```python
@register_output_generator("new_format")
class NewFormatGenerator(OutputGenerator):
    def generate(self, components, output_path):
        # Implementation
```

### 4. Validation Rules

Custom validation rules can be added to implement specific validation requirements.

```python
@register_validation_rule("custom_rule")
class CustomValidationRule(ValidationRule):
    def validate(self, component):
        # Implementation
```

## Performance Considerations

The architecture includes several features to optimize performance:

1. **Parallel Processing**: Component mapping and validation can run in parallel
2. **Connection Pooling**: Database connections are pooled for efficiency
3. **Caching**: Expensive operations like symbol mapping use caching
4. **Batch Processing**: Components are processed in batches to manage memory usage
5. **Query Optimization**: Database queries are optimized for performance

## Security Considerations

The architecture addresses security through:

1. **Credential Management**: Database credentials can be provided via environment variables
2. **Input Validation**: All user inputs are validated to prevent injection attacks
3. **Minimal Permissions**: Database connections use the minimum required permissions
4. **Secure Defaults**: Default configurations prioritize security

## Error Handling

The system implements a comprehensive error handling strategy:

1. **Hierarchical Error Types**: Specific error types inherit from base exceptions
2. **Contextual Information**: Errors include context to aid in troubleshooting
3. **Recovery Mechanisms**: The system can recover from certain types of failures
4. **Graceful Degradation**: Non-critical errors don't halt the entire process

```python
class MigrationError(Exception):
    """Base class for all migration errors."""
    pass

class DatabaseConnectionError(MigrationError):
    """Error connecting to a database."""
    pass

class MappingError(MigrationError):
    """Error during component mapping."""
    pass
```

## Testing Strategy

The architecture supports comprehensive testing:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Functional Tests**: Test end-to-end workflows
4. **Performance Tests**: Test system performance with large datasets
5. **Mock Objects**: Use mock objects to simulate dependencies

## Conclusion

The Altium to KiCAD Database Migration Tool architecture provides a solid foundation for reliable, efficient, and extensible migration of component libraries. Its modular design, clear separation of concerns, and well-defined extension points make it adaptable to a wide range of migration scenarios while maintaining code quality and performance.