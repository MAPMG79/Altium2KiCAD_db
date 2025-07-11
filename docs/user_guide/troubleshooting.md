# Troubleshooting Guide

This guide helps you diagnose and resolve common issues that may occur when using the Altium to KiCAD Database Migration Tool.

## Common Issues

### Connection Problems

#### Issue: "Connection failed" or "Unable to connect to database"

**Possible causes:**
- Incorrect database credentials
- Database server is not running
- Network connectivity issues
- Missing database drivers
- Firewall blocking connection

**Solutions:**

1. **Verify credentials:**
   ```bash
   altium2kicad --test-connection --input path/to/library.DbLib --verbose
   ```

2. **Check database server status:**
   - For MySQL/MariaDB: `mysql -u username -p -h hostname -e "SELECT 1"`
   - For PostgreSQL: `psql -U username -h hostname -c "SELECT 1"`
   - For MS SQL Server: `sqlcmd -U username -P password -S hostname -Q "SELECT 1"`

3. **Install required drivers:**
   ```bash
   # For MySQL
   pip install mysqlclient
   
   # For PostgreSQL
   pip install psycopg2-binary
   
   # For MS SQL Server
   pip install pyodbc
   ```

4. **Check firewall settings:**
   - Ensure your firewall allows connections to the database port
   - Common ports: MySQL (3306), PostgreSQL (5432), MS SQL (1433)

5. **Increase connection timeout:**
   ```bash
   altium2kicad --input path/to/library.DbLib --connection-timeout 60
   ```

### Mapping Issues

#### Issue: "Low confidence mappings" or "Many components have low confidence scores"

**Possible causes:**
- Non-standard component naming in Altium
- Missing mapping rules
- Inconsistent data in the source database

**Solutions:**

1. **Create custom mapping rules:**
   ```yaml
   # custom_mapping_rules.yaml
   symbols:
     - altium_pattern: "Your_Custom_Pattern.*"
       kicad_symbol: "Matching_KiCAD_Symbol"
       confidence: 0.9
   ```

   ```bash
   altium2kicad --input path/to/library.DbLib --custom-rules custom_mapping_rules.yaml
   ```

2. **Adjust confidence threshold:**
   ```bash
   altium2kicad --input path/to/library.DbLib --confidence-threshold 0.6
   ```

3. **Generate a mapping report for analysis:**
   ```bash
   altium2kicad --input path/to/library.DbLib --generate-mapping-report
   ```

4. **Use the interactive mapping mode:**
   ```bash
   altium2kicad --input path/to/library.DbLib --interactive-mapping
   ```

#### Issue: "Missing symbols or footprints"

**Possible causes:**
- KiCAD libraries not found
- Symbols/footprints don't exist in KiCAD libraries
- Incorrect mapping

**Solutions:**

1. **Specify KiCAD library paths:**
   ```bash
   altium2kicad --input path/to/library.DbLib \
                --kicad-symbol-lib-path /path/to/kicad/symbols \
                --kicad-footprint-lib-path /path/to/kicad/footprints
   ```

2. **Create missing symbols/footprints:**
   ```bash
   altium2kicad --input path/to/library.DbLib --create-missing
   ```

3. **Import additional KiCAD libraries:**
   ```bash
   altium2kicad --input path/to/library.DbLib --import-kicad-libs path/to/additional/libs
   ```

### Performance Issues

#### Issue: "Migration runs slowly" or "High memory usage"

**Possible causes:**
- Large database size
- Insufficient system resources
- Inefficient database queries
- No parallel processing

**Solutions:**

1. **Enable parallel processing:**
   ```bash
   altium2kicad --input path/to/library.DbLib --parallel-processing --max-workers 8
   ```

2. **Process in batches:**
   ```bash
   altium2kicad --input path/to/library.DbLib --batch-size 500
   ```

3. **Enable caching:**
   ```bash
   altium2kicad --input path/to/library.DbLib --cache-results
   ```

4. **Optimize database queries:**
   ```bash
   altium2kicad --input path/to/library.DbLib --optimize-queries
   ```

5. **Limit component selection:**
   ```bash
   altium2kicad --input path/to/library.DbLib --component-filter "Category='Resistors'"
   ```

#### Issue: "Out of memory error"

**Possible causes:**
- Trying to process too many components at once
- Memory leak in the application
- System has insufficient RAM

**Solutions:**

1. **Reduce batch size:**
   ```bash
   altium2kicad --input path/to/library.DbLib --batch-size 100
   ```

2. **Set memory limit:**
   ```bash
   altium2kicad --input path/to/library.DbLib --memory-limit 2048
   ```

3. **Split the migration into multiple runs:**
   ```bash
   # First run - process resistors
   altium2kicad --input path/to/library.DbLib --output output/resistors/ --component-filter "Category='Resistors'"
   
   # Second run - process capacitors
   altium2kicad --input path/to/library.DbLib --output output/capacitors/ --component-filter "Category='Capacitors'"
   ```

### Output Issues

#### Issue: "Generated library doesn't work in KiCAD"

**Possible causes:**
- Incompatible KiCAD version
- Corrupted output file
- Missing required fields
- Incorrect database structure

**Solutions:**

1. **Specify KiCAD version:**
   ```bash
   altium2kicad --input path/to/library.DbLib --kicad-version 6.0
   ```

2. **Validate the output:**
   ```bash
   altium2kicad --validate-output output/library.sqlite
   ```

3. **Add required fields:**
   ```bash
   altium2kicad --input path/to/library.DbLib --add-required-fields
   ```

4. **Check KiCAD library path configuration:**
   - In KiCAD, go to Preferences > Manage Symbol Libraries
   - Ensure the path to your library is correct
   - Check that the library type is set to "Database Library (*.sqlite)"

## Debugging Techniques

### Log Analysis

The tool generates detailed logs that can help diagnose issues:

```bash
# Enable verbose logging
altium2kicad --input path/to/library.DbLib --log-level DEBUG --log-file migration.log
```

Key log sections to check:

1. **Connection logs:** Look for database connection issues
2. **Parsing logs:** Check for problems reading the Altium database
3. **Mapping logs:** Identify component mapping issues
4. **Generation logs:** Find problems creating the KiCAD library

### Database Validation

Validate your database structure:

```bash
# Check Altium database structure
altium2kicad --validate-input path/to/library.DbLib

# Check generated KiCAD database
altium2kicad --validate-output output/library.sqlite
```

### Component Testing

Test specific components to isolate issues:

```bash
# Test migration of a single component
altium2kicad --input path/to/library.DbLib --test-component "R1" --verbose
```

## Advanced Troubleshooting

### Database Driver Issues

#### Microsoft SQL Server

If you're having issues with MS SQL Server:

```bash
# Check ODBC drivers
odbcinst -q -d

# Test connection with ODBC
isql -v "DRIVER={ODBC Driver 17 for SQL Server};SERVER=hostname;DATABASE=dbname;UID=username;PWD=password"
```

On Windows, check the ODBC Data Source Administrator.

#### MySQL/MariaDB

For MySQL connection issues:

```bash
# Test MySQL connection
python -c "import MySQLdb; MySQLdb.connect(host='hostname', user='username', passwd='password', db='dbname')"
```

#### PostgreSQL

For PostgreSQL connection issues:

```bash
# Test PostgreSQL connection
python -c "import psycopg2; psycopg2.connect('host=hostname dbname=dbname user=username password=password')"
```

### Recovering from Failed Migrations

If a migration fails partway through:

1. **Resume from checkpoint:**
   ```bash
   altium2kicad --input path/to/library.DbLib --resume-from-checkpoint
   ```

2. **Clean up partial outputs:**
   ```bash
   altium2kicad --clean-output output/
   ```

3. **Force regeneration:**
   ```bash
   altium2kicad --input path/to/library.DbLib --force-regenerate
   ```

## Getting Help

If you've tried the solutions above and still have issues:

1. **Generate a diagnostic report:**
   ```bash
   altium2kicad --diagnostic-report
   ```

2. **Check GitHub issues:**
   - Search for similar issues on the [GitHub repository](https://github.com/yourusername/Altium2KiCAD_db/issues)
   - If no solution is found, create a new issue with your diagnostic report

3. **Contact support:**
   - Email: support@example.com
   - Include your diagnostic report and detailed steps to reproduce the issue

## Common Error Messages

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `Error: Unable to connect to database` | Connection issue | Check credentials and network |
| `Error: DbLib file not found` | Incorrect file path | Verify the file path |
| `Error: No components found` | Empty database or query issue | Check database content and queries |
| `Error: Symbol mapping failed` | Missing mapping rules | Add custom mapping rules |
| `Error: Out of memory` | Insufficient RAM | Reduce batch size or increase memory |
| `Error: KiCAD library generation failed` | Output format issue | Check KiCAD version compatibility |
| `Error: Database driver not found` | Missing driver | Install required database driver |
| `Warning: Low confidence mapping` | Uncertain component match | Add custom mapping rules |
| `Warning: Missing footprint` | Footprint not found | Create missing footprint or adjust mapping |