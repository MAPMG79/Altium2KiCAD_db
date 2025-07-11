# Quick Reference Guide

This guide provides a quick reference for the most common operations, commands, and troubleshooting steps for the Altium to KiCAD Database Migration Tool.

## Common Operations

### Basic Migration Workflow

1. **Launch the application**
   ```bash
   python migration_app.py
   # Or if installed via pip:
   altium2kicad --gui
   ```

2. **Configure input**
   - Select Altium .DbLib file
   - Test database connection

3. **Configure output**
   - Select output directory
   - Specify KiCAD libraries path (optional)

4. **Set migration options**
   - Component type views
   - Confidence scores
   - Symbol/footprint validation

5. **Run migration**
   - Click "Start Migration"
   - Monitor progress

6. **Review results**
   - Check migration statistics
   - Verify generated files

### Command Line Quick Reference

#### Basic Usage

```bash
# Basic migration
altium2kicad --input path/to/library.DbLib --output output_directory

# Test database connection
altium2kicad --test-connection --input path/to/library.DbLib

# Analyze database contents
altium2kicad --analyze --input path/to/library.DbLib

# Run with configuration file
altium2kicad --config path/to/migration_config.yaml
```

#### Common Options

```bash
# Set confidence threshold
altium2kicad --input path/to/library.DbLib --output output_directory --confidence-threshold 0.7

# Enable parallel processing
altium2kicad --input path/to/library.DbLib --output output_directory --parallel-processing --max-workers 4

# Validate symbols and footprints
altium2kicad --input path/to/library.DbLib --output output_directory --validate-symbols --validate-footprints

# Resume from checkpoint
altium2kicad --input path/to/library.DbLib --output output_directory --resume-from-checkpoint

# Verbose logging
altium2kicad --input path/to/library.DbLib --output output_directory --log-level DEBUG
```

## File Locations

| File | Description | Location |
|------|-------------|----------|
| `.DbLib` | Altium database library file | Input source |
| `components.db` | SQLite database with migrated components | Output directory |
| `components.kicad_dbl` | KiCAD database library configuration | Output directory |
| `migration_report.json` | Detailed migration report | Output directory |
| `migration.log` | Log file with detailed messages | Output directory |
| `mapping_cache.json` | Cache of symbol/footprint mappings | Output directory |

## KiCAD Integration

### Adding the Library to KiCAD

1. Open KiCAD
2. Go to **Preferences → Manage Symbol Libraries**
3. Click **Global Libraries** tab
4. Click **Add Library** (folder icon)
5. Select the generated `.kicad_dbl` file
6. Click **OK**

### Using Components

1. Open Schematic Editor
2. Press **A** to add component
3. Look for your migrated library in the list
4. Browse components to verify successful migration

## Troubleshooting Quick Fixes

### Database Connection Issues

| Problem | Quick Fix |
|---------|-----------|
| Connection failed | Check database path and credentials |
| Missing ODBC driver | Install appropriate driver (see [Installation Guide](installation.md)) |
| Network database unreachable | Check network connectivity and firewall settings |
| Database file locked | Close any applications using the database |

### Migration Issues

| Problem | Quick Fix |
|---------|-----------|
| Low confidence scores | Add custom mapping rules or adjust confidence threshold |
| Missing components | Check log file for skipped components and their reasons |
| Out of memory | Reduce batch size with `--batch-size 100` |
| Slow migration | Enable parallel processing with `--parallel-processing` |

### KiCAD Integration Issues

| Problem | Quick Fix |
|---------|-----------|
| Library not showing in KiCAD | Verify path in Preferences → Manage Symbol Libraries |
| Missing symbols | Check symbol library paths in KiCAD preferences |
| Missing footprints | Check footprint library paths in KiCAD preferences |
| Component placement fails | Verify symbol references in the database |

## Common Error Messages

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Failed to connect to database" | Database connection issue | Check credentials and drivers |
| "No components found in table" | Empty or inaccessible table | Verify table name and permissions |
| "Symbol not found" | KiCAD symbol missing | Add symbol library or create custom mapping |
| "Footprint not found" | KiCAD footprint missing | Add footprint library or create custom mapping |
| "Confidence below threshold" | Low mapping confidence | Adjust threshold or add custom mapping |

## Performance Tips

- Use local database copies for faster access
- Enable parallel processing for large databases
- Use SSD storage for better performance
- Increase batch size for faster processing (if memory allows)
- Use caching for repeated migrations