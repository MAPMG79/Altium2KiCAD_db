# Configuration Guide

This guide provides detailed information about configuring the Altium to KiCAD Database Migration Tool to suit your specific needs.

## Configuration Overview

The Altium to KiCAD Database Migration Tool uses YAML configuration files to control its behavior. Configuration options allow you to customize:

- Input and output paths
- Performance settings
- Mapping behavior
- Validation rules
- Output formats

## Configuration File Structure

The configuration file is structured into several sections:

1. **Logging Configuration**: Control log verbosity and output
2. **Database Connection Settings**: Configure database connection parameters
3. **Migration Settings**: Control the migration process
4. **KiCAD Output Settings**: Configure KiCAD-specific output options
5. **Mapping Rules**: Define how components are mapped between formats

## Basic Configuration Example

Here's a basic configuration file example:

```yaml
# migration_config.yaml
altium_dblib_path: "input/components.DbLib"
output_directory: "output/"
enable_parallel_processing: true
max_worker_threads: 4
fuzzy_threshold: 0.7
create_views: true
validate_symbols: true
```

## Configuration Options Reference

### Logging Configuration

```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null  # Set to a path to enable file logging, null for console only
```

| Option | Description | Default | Valid Values |
|--------|-------------|---------|-------------|
| `level` | Log verbosity level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `format` | Log message format | See above | Any valid Python logging format string |
| `file` | Log file path | `null` | Path string or `null` for console output |

### Database Connection Settings

```yaml
database:
  timeout: 30
  max_retries: 3
  retry_delay: 2
```

| Option | Description | Default | Valid Values |
|--------|-------------|---------|-------------|
| `timeout` | Connection timeout in seconds | `30` | Positive integer |
| `max_retries` | Maximum number of retries for database operations | `3` | Non-negative integer |
| `retry_delay` | Delay between retries in seconds | `2` | Positive integer |

### Migration Settings

```yaml
migration:
  create_component_views: true
  include_confidence_scores: true
  validate_symbols: false
  batch_size: 1000
  min_confidence: 50
```

| Option | Description | Default | Valid Values |
|--------|-------------|---------|-------------|
| `create_component_views` | Create separate views for different component types | `true` | `true`, `false` |
| `include_confidence_scores` | Include confidence scores in the output | `true` | `true`, `false` |
| `validate_symbols` | Validate symbol and footprint existence in KiCAD libraries | `false` | `true`, `false` |
| `batch_size` | Maximum number of components to process in a batch | `1000` | Positive integer |
| `min_confidence` | Minimum confidence score (0-100) to accept a mapping | `50` | Integer between 0 and 100 |

### KiCAD Output Settings

```yaml
kicad:
  symbol_lib_path: ""
  footprint_lib_path: ""
  schema_version: "1.0"
  component_table: "components"
  field_mapping:
    "Comment": "Description"
    "Library Ref": "Symbol"
    "Footprint Ref": "Footprint"
    "Library Path": "SymbolLibrary"
    "Footprint Path": "FootprintLibrary"
    "Value": "Value"
    "ComponentLink1URL": "Datasheet"
```

| Option | Description | Default | Valid Values |
|--------|-------------|---------|-------------|
| `symbol_lib_path` | Default symbol library path | `""` | Valid path string |
| `footprint_lib_path` | Default footprint library path | `""` | Valid path string |
| `schema_version` | Database schema version | `"1.0"` | Valid version string |
| `component_table` | Default table name for components | `"components"` | Valid table name string |
| `field_mapping` | Mapping between Altium and KiCAD field names | See above | Key-value pairs |

### Mapping Rules

```yaml
mapping:
  symbol_rules: "config/symbol_mapping_rules.yaml"
  footprint_rules: "config/footprint_mapping_rules.yaml"
  category_rules: "config/category_mapping_rules.yaml"
```

| Option | Description | Default | Valid Values |
|--------|-------------|---------|-------------|
| `symbol_rules` | Symbol mapping rules file | `"config/symbol_mapping_rules.yaml"` | Valid path string |
| `footprint_rules` | Footprint mapping rules file | `"config/footprint_mapping_rules.yaml"` | Valid path string |
| `category_rules` | Category mapping rules file | `"config/category_mapping_rules.yaml"` | Valid path string |

## Advanced Configuration

### Performance Optimization

For large databases, you can optimize performance with these settings:

```yaml
enable_parallel_processing: true
max_worker_threads: 4  # Set based on your CPU cores
batch_size: 1000
enable_caching: true
vacuum_database: true
```

### Confidence Thresholds

Adjust mapping confidence thresholds to control the strictness of component matching:

```yaml
fuzzy_threshold: 0.7       # Higher values require more exact matches
confidence_threshold: 0.5  # Minimum confidence to accept a mapping
```

## Configuration Validation

The tool validates your configuration file on startup. Common validation errors include:

- Invalid file paths
- Out-of-range values
- Missing required fields
- Type mismatches (e.g., string instead of number)

If validation fails, the tool will output specific error messages to help you correct the issues.

## Environment-Specific Configurations

You can maintain different configuration files for different environments:

- `development_config.yaml`: For development and testing
- `production_config.yaml`: For production use
- `ci_config.yaml`: For continuous integration environments

## Using Configuration Files

Specify the configuration file when running the tool:

```bash
altium-kicad-migrate migrate --config migration_config.yaml
```

## Troubleshooting Configuration Issues

### Common Issues

1. **File Not Found Errors**:
   - Ensure all paths are correct and files exist
   - Use absolute paths if relative paths aren't working

2. **Permission Issues**:
   - Check file and directory permissions
   - Ensure the tool has write access to output directories

3. **Memory Errors**:
   - Reduce batch size
   - Disable parallel processing
   - Enable incremental processing

4. **Performance Issues**:
   - Increase batch size
   - Enable parallel processing
   - Adjust worker thread count

## See Also

- [Basic Usage Guide](basic_usage.md)
- [Advanced Features](advanced_features.md)
- [Configuration Examples](../examples/configuration/migration_config.yaml)
- [Troubleshooting Guide](troubleshooting.md)