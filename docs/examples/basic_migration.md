# Basic Usage Guide

This guide covers the basic usage of the Altium to KiCAD Migration Tool for common migration scenarios.

## Prerequisites

Before starting a migration, ensure you have:

1. **Altium .DbLib file** and associated database
2. **Database connectivity** (ODBC drivers installed)
3. **Output directory** with write permissions
4. **KiCAD installed** (optional, for symbol/footprint validation)

## Basic Migration Workflow

### Step 1: Test Database Connection

Before running a full migration, test your database connection:

```bash
altium-kicad-migrate test-connection path/to/your.DbLib
````

This command will:

- Parse the .DbLib configuration
- Attempt to connect to the database
- Display table information
- Report any connection issues

### Step 2: Analyze Database Contents

Get information about your database structure:

```bash
altium-kicad-migrate info path/to/your.DbLib --detailed
```

This shows:

- Number of tables
- Component counts per table
- Sample component fields
- Database statistics

### Step 3: Run Basic Migration

Perform a basic migration with default settings:

```bash
altium-kicad-migrate migrate path/to/your.DbLib -o output_directory
```

This will:

- Extract all component data
- Map components to KiCAD format
- Generate SQLite database
- Create .kicad_dbl library file
- Generate migration report

### Step 4: Validate Results

After migration, validate the results:

```bash
altium-kicad-migrate validate output_directory/components.db original_data.json
```

## Migration Options

### Parallel Processing

For large databases, enable parallel processing:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --parallel --threads 8
```

### Caching

Enable caching for repeated migrations:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ --cache
```

### Symbol/Footprint Validation

Validate against KiCAD libraries:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ \
    --kicad-symbols /path/to/kicad/symbols \
    --validate-symbols --validate-footprints
```

### Confidence Thresholds

Set mapping confidence thresholds:

```bash
altium-kicad-migrate migrate input.DbLib -o output/ \
    --fuzzy-threshold 0.8 --confidence-threshold 0.6
```

## Configuration Files

### Creating Configuration

Create a configuration file for repeated use:

```yaml
# migration_config.yaml
altium_dblib_path: "input/components.DbLib"
output_directory: "output/"
enable_parallel_processing: true
max_worker_threads: 4
batch_size: 1000
enable_caching: true
fuzzy_threshold: 0.7
confidence_threshold: 0.5
validate_symbols: true
create_views: true
vacuum_database: true
```

### Using Configuration

```bash
altium-kicad-migrate migrate --config migration_config.yaml
```

## Understanding Output

### Generated Files

After migration, you'll find:

```
output_directory/
├── components.db              # SQLite database with components
├── components.kicad_dbl       # KiCAD database library file
├── migration_report.json     # Detailed migration report
└── migration.log            # Detailed log file
```

### Database Structure

The generated database contains:

#### Tables

- `components`: Main component data
- `categories`: Component categories

#### Views

- `resistors`: Resistive components
- `capacitors`: Capacitive components
- `inductors`: Inductive components
- `integrated_circuits`: IC components
- `diodes`: Diode components
- `transistors`: Transistor components

#### Key Fields

- `symbol`: KiCAD symbol reference
- `footprint`: KiCAD footprint reference
- `value`: Component value
- `description`: Component description
- `manufacturer`: Manufacturer name
- `mpn`: Manufacturer part number
- `confidence`: Migration confidence score

## Using in KiCAD

### Installing Library

1. Open KiCAD
2. Go to **Preferences → Manage Symbol Libraries**
3. Select **Global Libraries** tab
4. Click **Add Library** (folder icon)
5. Select the generated `.kicad_dbl` file
6. Click **OK**

### Browsing Components

1. Open Schematic Editor
2. Press **A** to add component
3. Your migrated library appears in the list
4. Browse and search components
5. Components include all metadata from original database

## Troubleshooting Common Issues

### Connection Problems

**Issue**: Database connection fails **Solutions**:

- Install required ODBC drivers
- Check database file permissions
- Verify connection string in .DbLib file
- Try read-only connection

### Low Confidence Mappings

**Issue**: Many components have low confidence scores **Solutions**:

- Specify KiCAD library paths for better matching
- Add custom mapping rules
- Review and update component descriptions
- Use advanced mapping algorithms

### Memory Issues

**Issue**: Migration fails with memory errors **Solutions**:

- Reduce batch size: `--batch-size 500`
- Disable caching temporarily
- Process tables individually
- Use 64-bit Python

### Performance Issues

**Issue**: Migration is very slow **Solutions**:

- Enable parallel processing: `--parallel`
- Increase thread count: `--threads 8`
- Enable caching: `--cache`
- Use SSD storage for better I/O

## Best Practices

### Before Migration

1. **Backup original data**
2. **Test with small subset** first
3. **Check database connectivity**
4. **Verify KiCAD library paths**
5. **Review component descriptions** for accuracy

### During Migration

1. **Monitor progress** through logs
2. **Check confidence scores** as migration proceeds
3. **Review error messages** immediately
4. **Use appropriate batch sizes** for your system

### After Migration

1. **Validate results** thoroughly
2. **Test library in KiCAD**
3. **Review low-confidence mappings**
4. **Create backup** of generated database
5. **Document custom mappings** for future use

## Next Steps

After completing basic migration:

- [Advanced Usage](advanced_usage.md): Explore ML mapping and custom rules
- [Batch Processing](batch_processing.md): Process multiple libraries at once
- [Custom Mapping](custom_mapping.md): Create specialized mapping rules
- [Enterprise Setup](enterprise_setup.md): Configure for large organizations