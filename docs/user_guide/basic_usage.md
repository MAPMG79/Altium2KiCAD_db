# Basic Usage Guide

This guide provides detailed instructions for using the Altium to KiCAD Database Migration Tool. It covers all the basic features and workflows for successfully migrating your component libraries.

## Getting Started

The Altium to KiCAD Database Migration Tool provides both a graphical user interface (GUI) and a command-line interface (CLI). Choose the interface that best suits your workflow.

### Step 1: Launch the Application

```bash
python migration_app.py
```

Or if you installed via pip:

```bash
altium2kicad --gui
```

### Using the Graphical Interface

The GUI provides a step-by-step workflow:

1. **Welcome Screen**: Introduction and basic information
2. **Input Configuration**: Configure your Altium database source
3. **Output Configuration**: Set up your KiCAD library destination
4. **Migration Options**: Configure mapping and validation settings
5. **Review & Run**: Review settings and start the migration
6. **Results**: View migration results and access the generated files

### Using the Command Line Interface

For automation or batch processing, use the CLI:

```bash
# Basic usage
altium2kicad --input <input_path> --output <output_directory>

# With additional options
altium2kicad --input path/to/library.DbLib \
             --output output_directory \
             --library-name MyLibrary \
             --config path/to/config.yaml \
             --log-level INFO
```

## Step-by-Step Workflow

### Step 1: Test Database Connection

Before starting a full migration, it's a good idea to test your database connection:

```bash
altium2kicad --test-connection --input path/to/library.DbLib
```

In the GUI, use the "Test Connection" button on the Input Configuration screen.

### Step 2: Analyze Database Contents

You can analyze your database to understand its structure and contents:

```bash
altium2kicad --analyze --input path/to/library.DbLib
```

This will generate a report showing:
- Number of components
- Component categories
- Field names and data types
- Potential mapping issues

### Step 3: Configure Migration Settings

#### Using a Configuration File

Create a `migration_config.yaml` file to customize your migration:

```yaml
# Input configuration
input:
  path: path/to/library.DbLib
  connection_timeout: 30

# Output configuration
output:
  directory: output/
  library_name: MyLibrary
  format: sqlite

# Mapping settings
mapping:
  confidence_threshold: 0.7
  use_custom_rules: true
  custom_rules_path: path/to/custom_rules.yaml

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

Then run with:

```bash
altium2kicad --config path/to/migration_config.yaml
```

#### Using Command Line Arguments

Alternatively, specify settings directly as command line arguments:

```bash
altium2kicad --input path/to/library.DbLib \
             --output output_directory \
             --library-name MyLibrary \
             --confidence-threshold 0.7 \
             --validate-symbols \
             --validate-footprints \
             --parallel-processing \
             --max-workers 4
```

### Step 4: Run Basic Migration

Once your settings are configured, run the migration:

```bash
altium2kicad --input path/to/library.DbLib --output output_directory
```

In the GUI, click the "Start Migration" button on the Review & Run screen.

### Step 5: Validate Results

After migration completes:

1. Check the console output or log file for any warnings or errors
2. Open the generated HTML report to review migration details
3. Verify the generated SQLite database file
4. Test the library in KiCAD

## Understanding Migration Results

### Generated Files

A successful migration will generate:

- **components.db**: SQLite database containing all migrated components
- **components.kicad_dbl**: KiCAD database library configuration file
- **migration_report.json**: Detailed migration report with statistics
- **migration.log**: Detailed log file of the migration process
- **Log File**: Detailed log of the migration process (e.g., `migration_20250710_192200.log`)
- **HTML Report**: Visual report of the migration results (e.g., `migration_report.html`)
- **Mapping Cache**: Cache file for future migrations (e.g., `mapping_cache.json`)

### Database Structure

The generated SQLite database includes:

#### Tables

- `components`: Main component data
- `categories`: Component categories (resistors, capacitors, etc.)
- `symbols`: Symbol definitions
- `footprints`: Footprint definitions
- `fields`: Component field definitions

#### Views

- `resistors`: Filtered view of resistive components
- `capacitors`: Filtered view of capacitive components
- `inductors`: Filtered view of inductive components
- `integrated_circuits`: Filtered view of ICs
- `diodes`: Filtered view of diodes
- `transistors`: Filtered view of transistors
- `component_details`: Combined view of components with their fields
- `symbol_footprint_map`: Mapping between symbols and footprints

#### Key Fields

- `symbol`: KiCAD symbol reference (e.g., "Device:R")
- `footprint`: KiCAD footprint reference (e.g., "Resistor_SMD:R_0603_1608Metric")
- `value`: Component value
- `description`: Component description
- `manufacturer`: Manufacturer name
- `mpn`: Manufacturer part number
- `datasheet`: Link to datasheet
- `confidence`: Migration confidence score (0.0-1.0)

## Using the Migrated Library in KiCAD

### Step 1: Install in KiCAD

1. Open KiCAD
2. Go to **Preferences → Manage Symbol Libraries**
3. Click **Global Libraries** tab
4. Click **Add Library** (folder icon)
5. Select the generated `.kicad_dbl` file
6. Click **OK**

### Step 2: Verify Installation

1. Open Schematic Editor
2. Press **A** to add component
3. Look for your migrated library in the list
4. Browse components to verify successful migration

### Step 3: Handle Missing Symbols/Footprints

The migration tool may map some components to generic symbols or use wildcard footprints. To fix these:

1. Review components with low confidence scores
2. Create custom symbols/footprints as needed
3. Update the database with correct references
4. Re-import the library in KiCAD

### Browsing Components

1. Open the Schematic Editor
2. Click the "Add Symbol" button or press 'A'
3. Select your library from the list
4. Browse or search for components
5. Select a component and place it on the schematic

## Common Issues and Solutions

### Connection Problems

If you have trouble connecting to your database:

1. Verify your connection credentials
2. Check that the database server is running and accessible
3. Ensure you have the correct database drivers installed
4. Try increasing the connection timeout

### Low Confidence Mappings

If many components have low confidence scores:

1. Review the mapping rules in the configuration
2. Create custom mapping rules for your specific components
3. Adjust the confidence threshold
4. Check for inconsistencies in your Altium database

### Missing Symbols or Footprints

If symbols or footprints are missing:

1. Check the KiCAD library path settings
2. Verify that the referenced symbols/footprints exist
3. Add custom mapping rules for missing items
4. Use the `--create-missing` option to generate placeholders

## Next Steps

After mastering the basic usage, you can explore:

- [Advanced Features](advanced_features.md) for more complex migrations
- [Troubleshooting](troubleshooting.md) for solving common issues
- [FAQ](faq.md) for answers to frequently asked questions
- [Custom Mapping](../examples/custom_mapping.md) for creating custom mapping rules
- [Batch Processing](../examples/batch_processing.md) for handling multiple libraries