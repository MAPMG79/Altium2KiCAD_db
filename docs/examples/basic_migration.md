# Basic Migration Example

This tutorial provides a step-by-step guide for performing a basic migration from an Altium DbLib to a KiCAD database library using the Altium to KiCAD Database Migration Tool.

## Prerequisites

Before starting this tutorial, ensure you have:

1. Installed the Altium to KiCAD Database Migration Tool (see [Installation Guide](../user_guide/installation.md))
2. Access to an Altium DbLib file or database
3. Appropriate database drivers installed (if applicable)
4. Basic familiarity with both Altium and KiCAD

## Example Scenario

In this tutorial, we'll migrate a simple resistor library from Altium to KiCAD. We'll use:

- An Altium DbLib file named `resistors.DbLib`
- A SQLite database as the output format
- Basic mapping rules for resistor components

## Step 1: Prepare Your Environment

First, let's create a working directory for our migration:

```bash
# Create a working directory
mkdir altium2kicad_migration
cd altium2kicad_migration

# Create an output directory
mkdir output
```

## Step 2: Analyze the Altium Database

Before performing the full migration, it's a good idea to analyze the Altium database to understand its structure and contents:

```bash
# Analyze the database
altium2kicad --analyze --input path/to/resistors.DbLib
```

This will generate a report showing:

```
Database Analysis Report
=======================

Connection Information:
- Database Type: SQLite
- Database Path: resistors.db
- Tables: Components, Parameters, ComponentParameters

Component Statistics:
- Total Components: 150
- Component Categories: Resistors (150)

Field Statistics:
- Common Fields: LibRef, Comment, Description, Footprint, Value, Tolerance, Power
- Optional Fields: Temperature Coefficient, Manufacturer, Manufacturer Part Number

Potential Issues:
- No issues detected
```

## Step 3: Create a Configuration File

Create a file named `migration_config.yaml` with the following content:

```yaml
# Input configuration
input:
  path: path/to/resistors.DbLib
  connection_timeout: 30

# Output configuration
output:
  directory: output/
  library_name: Resistors
  format: sqlite
  create_report: true

# Mapping settings
mapping:
  confidence_threshold: 0.7
  use_custom_rules: true
  custom_rules_path: custom_rules.yaml

# Validation settings
validation:
  validate_symbols: true
  validate_footprints: true
  report_missing: true

# Performance settings
performance:
  parallel_processing: true
  max_workers: 4
  batch_size: 100
  cache_results: true
```

## Step 4: Create Custom Mapping Rules

Create a file named `custom_rules.yaml` with the following content:

```yaml
# Custom mapping rules for resistors
symbols:
  - altium_pattern: "RES.*"
    kicad_symbol: "Device:R"
    confidence: 0.9
  
  - altium_pattern: "RESISTOR.*"
    kicad_symbol: "Device:R"
    confidence: 0.9
  
  - altium_pattern: "R-.*"
    kicad_symbol: "Device:R"
    confidence: 0.9

footprints:
  - altium_pattern: "AXIAL-.*"
    kicad_footprint: "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
    confidence: 0.9
  
  - altium_pattern: "SMD-.*0603.*"
    kicad_footprint: "Resistor_SMD:R_0603_1608Metric"
    confidence: 0.9
  
  - altium_pattern: "SMD-.*0805.*"
    kicad_footprint: "Resistor_SMD:R_0805_2012Metric"
    confidence: 0.9
  
  - altium_pattern: "SMD-.*1206.*"
    kicad_footprint: "Resistor_SMD:R_1206_3216Metric"
    confidence: 0.9

categories:
  - altium_pattern: "Resistors"
    kicad_category: "Passive Components/Resistors"
    confidence: 1.0
```

## Step 5: Run the Migration

Now, run the migration using the configuration file:

```bash
# Run the migration
altium2kicad --config migration_config.yaml
```

You should see output similar to:

```
Altium to KiCAD Database Migration Tool v1.0.0
==============================================

Loading configuration from migration_config.yaml
Connecting to Altium database: resistors.DbLib
Successfully connected to database
Extracting components...
Found 150 components
Mapping components...
[====================] 100% (150/150)
Mapping complete: 150 components mapped
Generating KiCAD library...
Creating SQLite database: output/Resistors.sqlite
Creating tables and views...
Writing components...
[====================] 100% (150/150)
Library generation complete
Generating report...
Report saved to: output/migration_report.html

Migration Summary:
- Components Processed: 150
- Successfully Mapped: 150 (100.0%)
- High Confidence Mappings: 145 (96.7%)
- Low Confidence Mappings: 5 (3.3%)
- Warnings: 0
- Errors: 0

Output Files:
- KiCAD Library: output/Resistors.sqlite
- Migration Report: output/migration_report.html
- Log File: migration_20250710_193045.log

Migration completed successfully in 5.2 seconds
```

## Step 6: Review the Migration Report

Open the generated HTML report (`output/migration_report.html`) in a web browser to review the migration results. The report includes:

- Migration summary statistics
- Component mapping details
- Any warnings or errors encountered
- Visualization of mapping confidence
- Recommendations for improving results

## Step 7: Verify the Output

Examine the generated SQLite database to ensure it contains the expected data:

```bash
# Install sqlite3 if not already available
# sudo apt-get install sqlite3  # For Ubuntu/Debian

# Open the database
sqlite3 output/Resistors.sqlite

# List tables
.tables

# View component count
SELECT COUNT(*) FROM components;

# View component details
SELECT * FROM component_details LIMIT 10;

# Exit SQLite
.exit
```

## Step 8: Import the Library into KiCAD

1. Open KiCAD
2. Go to Preferences > Manage Symbol Libraries
3. Click "Add existing library to table"
4. Select "Database Library (*.sqlite)"
5. Browse to `output/Resistors.sqlite` and select it
6. Give the library a nickname (e.g., "Resistors")
7. Click OK to add the library

## Step 9: Test the Library

1. Create a new schematic in KiCAD
2. Click the "Add Symbol" button or press 'A'
3. Select the "Resistors" library from the list
4. Browse or search for a resistor component
5. Select a component and place it on the schematic
6. Verify that the component properties match the expected values

## Using the Python API

Alternatively, you can perform the same migration using the Python API:

```python
from migration_tool import MigrationAPI

# Initialize the API
api = MigrationAPI()

# Configure the migration
config = {
    'input': {
        'path': 'path/to/resistors.DbLib',
        'connection_timeout': 30
    },
    'output': {
        'directory': 'output/',
        'library_name': 'Resistors',
        'format': 'sqlite',
        'create_report': True
    },
    'mapping': {
        'confidence_threshold': 0.7,
        'use_custom_rules': True,
        'custom_rules_path': 'custom_rules.yaml'
    },
    'validation': {
        'validate_symbols': True,
        'validate_footprints': True,
        'report_missing': True
    },
    'performance': {
        'parallel_processing': True,
        'max_workers': 4,
        'batch_size': 100,
        'cache_results': True
    }
}

# Run the migration
result = api.run_migration(config)

# Print summary
print(f"Migration complete! {result['success_count']} components migrated successfully.")
print(f"Output files located at: {result['output_path']}")
```

## Troubleshooting Common Issues

### Connection Issues

If you encounter connection issues:

1. Verify the DbLib file path is correct
2. Check that the database referenced in the DbLib file is accessible
3. Ensure you have the appropriate database drivers installed
4. Try increasing the connection timeout

### Mapping Issues

If components aren't mapping correctly:

1. Review the custom mapping rules
2. Adjust the confidence threshold
3. Add more specific mapping rules for your components
4. Check the component names and descriptions in the Altium database

### Output Issues

If the output library doesn't work in KiCAD:

1. Verify the SQLite database was created successfully
2. Check that KiCAD can access the database file
3. Ensure the library is properly added to KiCAD
4. Verify that the required symbols and footprints exist in KiCAD

## Next Steps

After completing this basic migration, you might want to explore:

- [Batch Processing](batch_processing.md) for handling multiple libraries
- [Custom Mapping](custom_mapping.md) for more advanced mapping rules
- [Enterprise Setup](enterprise_setup.md) for large-scale deployments
- [Advanced Features](../user_guide/advanced_features.md) for optimizing the migration process