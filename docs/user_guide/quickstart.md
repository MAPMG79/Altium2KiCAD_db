# Quickstart Guide

This guide will help you quickly get started with the Altium to KiCAD Database Migration Tool. Follow these steps to perform your first migration from an Altium DbLib to a KiCAD database library.

## Prerequisites

Before starting, ensure you have:

- Installed the Altium to KiCAD Database Migration Tool (see [Installation Guide](installation.md))
- Access to your Altium DbLib file or database
- Appropriate database drivers installed (if applicable)
- Basic familiarity with both Altium and KiCAD

## 5-Minute Migration Tutorial

### Step 1: Launch the Application

#### Using the GUI

```bash
# Launch the graphical interface
altium2kicad --gui
```

#### Using the Command Line

```bash
# Basic command line usage
altium2kicad --input path/to/your/library.DbLib --output output_directory
```

### Step 2: Configure Input Source

1. **Select Input Type**:
   - Choose "DbLib File" if you have an Altium DbLib file
   - Choose "Direct Database Connection" if connecting directly to a database

2. **For DbLib File**:
   - Click "Browse" and select your .DbLib file
   - The tool will automatically extract connection information

3. **For Direct Database Connection**:
   - Select your database type (SQLite, MySQL, PostgreSQL, MS SQL)
   - Enter connection details (server, port, username, password, database name)
   - Test the connection to ensure it works

### Step 3: Configure Output

1. **Select Output Directory**:
   - Choose where to save the generated KiCAD library files

2. **Configure Library Name**:
   - Enter a name for your KiCAD library (default: based on input name)

3. **Select Output Format**:
   - SQLite (recommended for most users)
   - Other formats (if available)

### Step 4: Run Migration

1. Click the "Start Migration" button
2. Monitor the progress in the status window
3. Review the summary when complete

## Example: Migrating a Simple Component Library

Here's a complete example of migrating a resistor library from Altium to KiCAD:

```python
from migration_tool import MigrationAPI

# Initialize the API
api = MigrationAPI()

# Configure the migration
config = {
    'input_path': 'examples/resistors.DbLib',
    'output_directory': 'output/',
    'library_name': 'Resistors',
    'mapping_confidence_threshold': 0.7,
    'validate_symbols': True,
    'validate_footprints': True
}

# Run the migration
result = api.run_migration(config)

# Print summary
print(f"Migration complete! {result['success_count']} components migrated successfully.")
print(f"Output files located at: {result['output_path']}")
```

## Verifying the Results

After migration completes:

1. **Check the Output Directory**:
   - You should see a SQLite database file (e.g., `Resistors.sqlite`)
   - Log files with details of the migration process

2. **Open KiCAD and Add the Library**:
   - In KiCAD, go to Preferences > Manage Symbol Libraries
   - Add a new library pointing to your generated SQLite file
   - Test by placing a component from the new library

3. **Review the Migration Report**:
   - Open the generated HTML report to see details about the migration
   - Pay attention to any warnings or low-confidence mappings

## Common First-Time Issues

- **Connection Failed**: Check your database credentials and ensure the server is accessible
- **Missing Symbols/Footprints**: Review the mapping rules or add custom mappings
- **Low Confidence Scores**: Adjust the confidence threshold or add custom mapping rules

## Next Steps

Now that you've completed your first migration, you can:

- Learn about [advanced features](advanced_features.md) for more complex migrations
- Customize the [mapping rules](../examples/custom_mapping.md) for better results
- Set up [batch processing](../examples/batch_processing.md) for multiple libraries
- Check the [troubleshooting guide](troubleshooting.md) if you encounter issues

For a more detailed walkthrough, see the [Basic Usage Guide](basic_usage.md).