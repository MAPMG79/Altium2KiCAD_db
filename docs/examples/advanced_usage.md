# Advanced Usage Guide

This guide covers advanced features and techniques for the Altium to KiCAD Migration Tool, building on the [Basic Usage Guide](basic_migration.md).

## Advanced Mapping Techniques

### Machine Learning Mapping

For complex component libraries, enable machine learning-based mapping:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --use-ml --training-data path/to/training_data.json
```

The ML mapping engine:
- Analyzes component descriptions and attributes
- Compares with known KiCAD components
- Learns from previous mappings
- Improves accuracy over time

### Custom Mapping Rules

Create advanced mapping rules for specialized components:

```yaml
# advanced_mapping_rules.yaml
symbols:
  - altium_pattern: "^IC_([A-Z0-9]+)_(.+)$"
    kicad_symbol: "IC:$1_$2"
    confidence: 0.95
    description_match: ".*microcontroller.*"
    
  - altium_pattern: "^XTAL-([0-9.]+)MHZ-([A-Z0-9]+)$"
    kicad_symbol: "Device:Crystal"
    kicad_value: "$1MHz"
    confidence: 0.9
    
footprints:
  - altium_pattern: "^QFP([0-9]+)$"
    kicad_footprint: "Package_QFP:QFP-$1_10x10mm_P0.5mm"
    confidence: 0.9
    
  - altium_pattern: "^([A-Z]+)-([0-9]+)-([0-9]+)$"
    kicad_footprint: "Package_$1:$1-$2_$3"
    confidence: 0.85
    field_match:
      package_type: "QFP|SOIC|TSSOP"
```

Apply custom rules:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --mapping-rules advanced_mapping_rules.yaml
```

## Database Optimization

### Indexing and Views

Create optimized database views and indexes:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --create-views --create-indexes
```

This creates:
- Specialized views for component types
- Full-text search indexes
- Performance-optimized queries

### Database Compression

Optimize database size:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --compress --vacuum
```

This:
- Removes redundant data
- Compresses text fields
- Optimizes database structure
- Reduces file size by 30-50%

## Advanced Filtering

### Component Selection

Migrate specific component types:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --component-types resistors,capacitors
```

Filter by component attributes:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --filter "value > 100 AND tolerance <= 0.01"
```

### Field Mapping

Create custom field mappings:

```yaml
# field_mapping.yaml
fields:
  - altium_field: "Comment"
    kicad_field: "Reference"
    
  - altium_field: "ComponentLink1URL"
    kicad_field: "Datasheet"
    
  - altium_field: "ComponentLink2URL"
    kicad_field: "Documentation"
    
  - altium_field: "HelpURL"
    kicad_field: "Info"
```

Apply field mappings:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --field-mapping field_mapping.yaml
```

## Integration Features

### Version Control Integration

Generate Git-friendly output:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --vcs-friendly --split-by-category
```

This creates:
- Separate files per component category
- Text-based formats for diffing
- Metadata for tracking changes

### CI/CD Pipeline Integration

Run in CI/CD environments:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --ci-mode --exit-code-on-error --report-format json
```

Example GitLab CI configuration:

```yaml
library_migration:
  stage: build
  script:
    - altium-kicad-migrate migrate input.DbLib -o output/ --ci-mode --report-format json
  artifacts:
    paths:
      - output/
    reports:
      junit: output/migration_report.xml
```

## Advanced API Usage

### Programmatic Migration

```python
from migration_tool import MigrationAPI
from migration_tool.mapping import CustomMapper
from migration_tool.validators import ComponentValidator

# Initialize API with custom components
api = MigrationAPI(
    custom_mapper=CustomMapper(rules_file="custom_rules.yaml"),
    validator=ComponentValidator(kicad_libs_path="/path/to/kicad/libs")
)

# Configure advanced options
config = {
    'input': {
        'path': 'input.DbLib',
        'connection_timeout': 60,
        'query_batch_size': 1000
    },
    'output': {
        'directory': 'output/',
        'format': 'sqlite',
        'create_report': True,
        'compression_level': 9
    },
    'mapping': {
        'use_ml': True,
        'confidence_threshold': 0.8,
        'fuzzy_match_threshold': 0.7,
        'field_mapping': 'field_mapping.yaml'
    },
    'filters': {
        'component_types': ['resistors', 'capacitors'],
        'value_filter': 'value > 100 AND tolerance <= 0.01',
        'include_patterns': ['.*SMD.*', '.*0603.*'],
        'exclude_patterns': ['.*obsolete.*', '.*DNP.*']
    },
    'performance': {
        'parallel_processing': True,
        'max_workers': 8,
        'cache_results': True,
        'memory_limit': '4G'
    }
}

# Run migration with progress callback
def progress_callback(current, total, stage):
    print(f"Progress: {current}/{total} ({stage})")

result = api.run_migration(config, progress_callback=progress_callback)

# Process results
if result['success']:
    print(f"Migration successful: {result['success_count']} components migrated")
    
    # Post-process the database
    api.optimize_database(result['output_path'])
    api.validate_library(result['output_path'])
    
    # Generate reports
    api.generate_report(result['output_path'], 'html')
    api.generate_report(result['output_path'], 'json')
    api.generate_report(result['output_path'], 'csv')
else:
    print(f"Migration failed: {result['error']}")
```

### Custom Component Processing

```python
from migration_tool import MigrationAPI
from migration_tool.components import Component

# Initialize API
api = MigrationAPI()

# Define custom component processor
def process_component(component):
    # Add custom fields
    component.fields['Verified'] = 'Yes'
    component.fields['Internal_ID'] = f"INT-{component.id}"
    
    # Modify description
    if 'description' in component.fields:
        component.fields['description'] = f"[VERIFIED] {component.fields['description']}"
    
    # Custom categorization
    if 'resistor' in component.fields.get('description', '').lower():
        component.category = 'Passive/Resistors'
    
    return component

# Run migration with custom processor
api.run_migration(
    config={'input': {'path': 'input.DbLib'}, 'output': {'directory': 'output/'}},
    component_processor=process_component
)
```

## Performance Optimization

### Memory Management

For very large databases:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --memory-limit 4G --stream-results
```

### Distributed Processing

Process large libraries across multiple machines:

```bash
# Machine 1: Process resistors and capacitors
altium-kicad-migrate migrate input.DbLib -o output/ --component-types resistors,capacitors

# Machine 2: Process ICs and transistors
altium-kicad-migrate migrate input.DbLib -o output/ --component-types ics,transistors

# Merge results
altium-kicad-migrate merge output1/components.db output2/components.db -o final/merged.db
```

## Advanced Validation

### Symbol and Footprint Validation

Perform comprehensive validation:

```bash
altium-kicad-migrate validate output/components.db \
    --kicad-symbols /path/to/kicad/symbols \
    --kicad-footprints /path/to/kicad/footprints \
    --check-3d-models \
    --validate-parameters
```

### Electrical Rule Checking

Validate component electrical properties:

```bash
altium-kicad-migrate validate output/components.db --electrical-rules rules.json
```

Example rules file:

```json
{
  "resistors": {
    "power_rating": ">= 0.125",
    "tolerance": "<= 0.05"
  },
  "capacitors": {
    "voltage_rating": ">= 10",
    "temperature_coefficient": "X7R|X5R"
  }
}
```

## Troubleshooting Advanced Issues

### Database Connection Problems

For complex database setups:

```bash
# Test connection with detailed diagnostics
altium-kicad-migrate test-connection input.DbLib --verbose --timeout 120

# Use alternative connection method
altium-kicad-migrate migrate input.DbLib -o output/ --connection-method odbc --connection-string "DSN=MyDSN;UID=user;PWD=pass"
```

### Mapping Failures

Diagnose mapping issues:

```bash
# Generate detailed mapping report
altium-kicad-migrate analyze-mapping input.DbLib --detailed-report mapping_analysis.html

# Test specific component mapping
altium-kicad-migrate test-mapping "IC_MICROCHIP_PIC16F877" --mapping-rules custom_rules.yaml
```

## Conclusion

These advanced techniques allow you to:
- Handle complex component libraries
- Optimize migration performance
- Integrate with enterprise workflows
- Customize the migration process
- Validate results thoroughly

For even more specialized scenarios, see:
- [Batch Processing](batch_processing.md) for handling multiple libraries
- [Custom Mapping](custom_mapping.md) for specialized mapping rules
- [Enterprise Setup](enterprise_setup.md) for large-scale deployments