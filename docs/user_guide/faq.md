# Frequently Asked Questions

This document answers common questions about the Altium to KiCAD Database Migration Tool.

## General Questions

### Q: What is the Altium to KiCAD Database Migration Tool?

**A:** The Altium to KiCAD Database Migration Tool is a specialized utility that helps you convert component libraries from Altium's DbLib format to KiCAD's database library format. It handles the mapping of symbols, footprints, and component metadata between the two EDA platforms.

### Q: Is this an official tool from Altium or KiCAD?

**A:** No, this is an independent, open-source tool developed by the community to facilitate migration between the two platforms. It is not officially affiliated with or endorsed by either Altium or KiCAD.

### Q: Is the tool free to use?

**A:** Yes, the tool is open-source and free to use under the MIT license. You can use it for both personal and commercial projects without restrictions.

## Compatibility Questions

### Q: What Altium database formats are supported?

**A:** The tool supports:
- Altium DbLib files (.DbLib)
- Direct connections to databases referenced by DbLib files
- Direct connections to SQLite, MySQL, PostgreSQL, and Microsoft SQL Server databases

### Q: What KiCAD versions are supported?

**A:** The tool is compatible with KiCAD 6.0 and newer. Limited support is available for KiCAD 5.x, but some advanced features may not work correctly.

### Q: Can I migrate multiple databases at once?

**A:** Yes, the tool supports batch processing of multiple databases. You can either:
- Use the batch mode in the GUI
- Use the command line with a batch configuration file
- Write a script using the Python API

### Q: Does it work with cloud-hosted databases?

**A:** Yes, the tool can connect to cloud-hosted databases as long as:
- You have the proper connection credentials
- The necessary database drivers are installed
- Network connectivity and firewall settings allow the connection

## Installation Questions

### Q: What are the system requirements?

**A:** The minimum requirements are:
- Python 3.8 or higher
- 4 GB RAM (8 GB recommended for large databases)
- 500 MB disk space
- Internet connection for installation

### Q: How do I install ODBC drivers?

**A:** The installation process depends on your database type and operating system:

**For Microsoft SQL Server:**
- Windows: Download and install the [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Linux: Follow the [Linux installation instructions](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)
- macOS: Use Homebrew: `brew tap microsoft/mssql-release && brew update && brew install msodbcsql17`

**For MySQL:**
- Windows: Download and install the [MySQL Connector/ODBC](https://dev.mysql.com/downloads/connector/odbc/)
- Linux: `sudo apt-get install unixodbc-dev libmyodbc` (Ubuntu/Debian)
- macOS: `brew install unixodbc mysql-connector-c++`

**For PostgreSQL:**
- Windows: Download and install the [PostgreSQL ODBC Driver](https://www.postgresql.org/ftp/odbc/versions/)
- Linux: `sudo apt-get install odbc-postgresql` (Ubuntu/Debian)
- macOS: `brew install psqlodbc`

### Q: Can I run this without installing Python?

**A:** Yes, for Windows users, a standalone executable is available that doesn't require Python installation. Download it from the [GitHub Releases page](https://github.com/yourusername/Altium2KiCAD_db/releases).

## Usage Questions

### Q: How long does migration take?

**A:** Migration time depends on several factors:
- Database size (number of components)
- Connection speed (for remote databases)
- Computer performance
- Enabled features (validation, parallel processing)

Typical migration times:
- Small library (1,000 components): 30 seconds
- Medium library (10,000 components): 5 minutes
- Large library (50,000 components): 20 minutes
- Very large library (100,000+ components): 45+ minutes

### Q: What happens if migration fails?

**A:** If a migration fails:
1. Check the log file for error details
2. Fix the identified issues
3. Resume the migration using the `--resume-from-checkpoint` option
4. If needed, use the `--clean-output` option to remove partial outputs before retrying

The tool creates checkpoints during migration, allowing you to resume from where it left off.

### Q: Can I customize component mappings?

**A:** Yes, you can customize mappings in several ways:
1. Create custom mapping rule files (YAML format)
2. Use the interactive mapping mode to manually map components
3. Edit the mapping cache file to adjust existing mappings
4. Use the Python API to implement custom mapping algorithms

## Output Questions

### Q: What format is the output database?

**A:** The primary output format is a SQLite database (.sqlite) that KiCAD can directly use as a symbol library. Additional output formats include:
- CSV files (for manual inspection or import to other systems)
- JSON files (for programmatic processing)
- HTML reports (for documentation)

### Q: How do I use the migrated library in KiCAD?

**A:** To use the migrated library in KiCAD:
1. Open KiCAD
2. Go to Preferences > Manage Symbol Libraries
3. Click "Add existing library to table"
4. Select "Database Library (*.sqlite)"
5. Browse to your generated SQLite file and select it
6. Give the library a nickname
7. Click OK to add the library

The library will now appear in the symbol selector when you place components.

### Q: Can I edit the migrated database?

**A:** Yes, you can edit the migrated SQLite database using:
1. KiCAD's built-in library editor (limited functionality)
2. SQLite database tools like DB Browser for SQLite
3. The migration tool's database editor (if available)
4. SQL commands via the SQLite command line

However, it's generally better to edit the source database and re-run the migration if you need to make substantial changes.

## Troubleshooting Questions

### Q: "Connection failed" error - what do I do?

**A:** For connection errors:
1. Verify your database credentials
2. Check that the database server is running and accessible
3. Ensure you have the correct database drivers installed
4. Check firewall settings
5. Try increasing the connection timeout
6. Use the `--verbose` option to get more detailed error information

### Q: Many components have low confidence scores - why?

**A:** Low confidence scores usually indicate:
1. Non-standard component naming in your Altium database
2. Missing mapping rules for your specific components
3. Inconsistent data in the source database
4. Symbols or footprints that don't have close matches in KiCAD

Solutions include:
1. Creating custom mapping rules
2. Adjusting the confidence threshold
3. Using the interactive mapping mode
4. Adding more KiCAD libraries to match against

### Q: Migration runs out of memory - how to fix?

**A:** To resolve memory issues:
1. Reduce the batch size (`--batch-size 100`)
2. Disable parallel processing or reduce worker count
3. Split the migration into multiple runs by component category
4. Increase your system's available memory
5. Use the 64-bit version of the tool

### Q: Some components are missing - why?

**A:** Components might be missing due to:
1. Filtering applied during migration
2. Components failing validation checks
3. Confidence scores below the threshold
4. Database query issues

Check the log file and migration report for details on skipped components.

## Advanced Questions

### Q: Can I use machine learning for better mapping?

**A:** Yes, the tool has experimental support for machine learning-based mapping:
1. Enable with `--use-ml` option
2. Provide training data with `--ml-training-data`
3. Adjust minimum confidence with `--ml-min-confidence`

This feature may require additional Python packages and is considered experimental.

### Q: How do I create custom mapping rules?

**A:** Create a YAML file with mapping patterns:

```yaml
symbols:
  - altium_pattern: "RES.*"
    kicad_symbol: "Device:R"
    confidence: 0.9

footprints:
  - altium_pattern: "SOIC-8"
    kicad_footprint: "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    confidence: 0.95
```

Then use it with `--custom-rules path/to/rules.yaml`

### Q: Can I integrate this into my workflow?

**A:** Yes, integration options include:
1. Command-line usage for scripts and automation
2. Python API for programmatic control
3. Docker container for CI/CD pipelines
4. Webhook notifications for workflow integration
5. Batch processing for scheduled migrations

## Performance Questions

### Q: How can I make migration faster?

**A:** To improve performance:
1. Enable parallel processing (`--parallel-processing`)
2. Increase worker count (`--max-workers 8`)
3. Enable caching (`--cache-results`)
4. Use a faster storage device for output
5. Connect to the database via a fast network or locally
6. Optimize database queries (`--optimize-queries`)
7. Disable validation for initial runs

### Q: Is there a size limit for databases?

**A:** There's no hard limit, but practical considerations:
- Very large databases (>100,000 components) may require:
  - More memory (8+ GB recommended)
  - Batch processing
  - Parallel processing
  - SSD storage for better performance
  - 64-bit operating system

The largest successfully tested database contained approximately 500,000 components.

## Support Questions

### Q: Where can I get help?

**A:** Support resources include:
1. Documentation (this FAQ and other guides)
2. [GitHub Issues](https://github.com/yourusername/Altium2KiCAD_db/issues)
3. [Community Forum](https://forum.example.com)
4. Email support: support@example.com

### Q: How can I contribute?

**A:** You can contribute by:
1. Reporting bugs and suggesting features on GitHub
2. Submitting pull requests with code improvements
3. Improving documentation
4. Creating custom mapping rules and sharing them
5. Helping other users on the forum

See the [Contributing Guide](../developer_guide/contributing.md) for details.

### Q: Is commercial support available?

**A:** Commercial support options include:
1. Priority email support
2. Custom feature development
3. On-site training and implementation
4. Integration with enterprise systems

Contact sales@example.com for commercial support inquiries.

## Legal Questions

### Q: What license is the tool released under?

**A:** The tool is released under the MIT License, which is a permissive open-source license that allows for use, modification, and distribution with minimal restrictions.

### Q: Can I use this in my commercial product?

**A:** Yes, the MIT License allows for commercial use. You can use the tool in commercial products or services without restrictions.

### Q: Is this tool affiliated with Altium or KiCAD?

**A:** No, this is an independent, community-developed tool. It is not officially affiliated with, endorsed by, or supported by either Altium or KiCAD. It is developed by third-party contributors to facilitate interoperability between the two platforms.