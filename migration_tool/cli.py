#!/usr/bin/env python3
"""
Command Line Interface for Altium to KiCAD Database Migration Tool.

This module provides a comprehensive command-line interface for the migration tool
using the Click framework.
"""

import os
import sys
import json
import click
import logging
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.mapping_engine import ComponentMappingEngine
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager
from migration_tool.utils.database_utils import create_connection, execute_query, table_exists
from migration_tool.utils.logging_utils import setup_logging, ProgressLogger, get_logger


# Common options for multiple commands
def common_options(function):
    """Common CLI options decorator."""
    function = click.option(
        '--config', '-c',
        type=click.Path(exists=True),
        help='Path to configuration file (YAML or JSON)'
    )(function)
    function = click.option(
        '--verbose', '-v',
        is_flag=True,
        help='Enable verbose output'
    )(function)
    function = click.option(
        '--log-level',
        type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False),
        default='INFO',
        help='Set logging level'
    )(function)
    function = click.option(
        '--log-file',
        type=click.Path(),
        help='Log file path'
    )(function)
    return function


# Progress bar helper function
def create_progress_bar(total, label="Processing"):
    """Create a Click progress bar."""
    return click.progressbar(
        length=total,
        label=label,
        fill_char=click.style('█', fg='green'),
        empty_char=click.style('░', fg='white')
    )


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Altium to KiCAD Database Migration Tool.
    
    This tool helps migrate component databases from Altium Designer's .DbLib format
    to KiCAD's .kicad_dbl format.
    """
    pass


@cli.command('migrate')
@click.argument('dblib_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(), default='output', help='Output directory for KiCAD database files')
@click.option('--kicad-symbols', type=click.Path(exists=True), help='Path to KiCAD symbol libraries')
@click.option('--kicad-footprints', type=click.Path(exists=True), help='Path to KiCAD footprint libraries')
@click.option('--parallel/--no-parallel', default=True, help='Enable/disable parallel processing')
@click.option('--threads', type=int, default=4, help='Number of worker threads for parallel processing')
@click.option('--batch-size', type=int, default=1000, help='Batch size for processing components')
@click.option('--cache/--no-cache', default=True, help='Enable/disable caching for improved performance')
@click.option('--fuzzy-threshold', type=float, default=0.7, help='Threshold for fuzzy matching (0.0-1.0)')
@click.option('--ml-mapping/--no-ml-mapping', default=False, help='Enable/disable machine learning-based mapping')
@click.option('--validate-symbols/--no-validate-symbols', default=False, help='Validate symbol existence in KiCAD libraries')
@click.option('--validate-footprints/--no-validate-footprints', default=False, help='Validate footprint existence in KiCAD libraries')
@click.option('--create-views/--no-views', default=True, help='Enable/disable creation of component type views')
@click.option('--optimize/--no-optimize', default=True, help='Enable/disable database optimization')
@click.option('--dry-run', is_flag=True, help='Preview migration without creating files')
@common_options
def migrate(dblib_file, output_dir, kicad_symbols, kicad_footprints, parallel, threads, batch_size, 
           cache, fuzzy_threshold, ml_mapping, validate_symbols, validate_footprints, create_views, 
           optimize, dry_run, config, verbose, log_level, log_file):
    """Migrate Altium database to KiCAD format.
    
    DBLIB_FILE is the path to the Altium .DbLib file to migrate.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else log_level
    logger = setup_logging(
        log_level=log_level,
        log_file=log_file
    )
    
    click.secho("Starting Altium to KiCAD migration", fg='green')
    
    try:
        # Load configuration
        config_manager = ConfigManager(config)
        
        # Override config with command line arguments
        config_updates = {
            'altium_dblib_path': dblib_file,
            'output_directory': output_dir,
            'enable_parallel_processing': parallel,
            'max_worker_threads': threads,
            'batch_size': batch_size,
            'enable_caching': cache,
            'fuzzy_threshold': fuzzy_threshold,
            'enable_ml_mapping': ml_mapping,
            'validate_symbols': validate_symbols,
            'validate_footprints': validate_footprints,
            'create_views': create_views,
            'vacuum_database': optimize,
            'log_level': log_level
        }
        
        if kicad_symbols:
            config_updates['kicad_symbol_libraries'] = [kicad_symbols]
        if kicad_footprints:
            config_updates['kicad_footprint_libraries'] = [kicad_footprints]
        
        config_manager.update(config_updates)
        config = config_manager.config
        
        # Validate configuration
        issues = config_manager.validate()
        if issues:
            for key, issue in issues.items():
                click.secho(f"Configuration error - {key}: {issue}", fg='red')
            return 1
        
        # Parse Altium database
        click.secho(f"Parsing Altium database: {config['altium_dblib_path']}", fg='blue')
        parser = AltiumDbLibParser(config_manager)
        altium_config = parser.parse_dblib_file(config['altium_dblib_path'])
        
        # Extract data
        click.secho("Extracting component data...", fg='blue')
        altium_data = parser.extract_all_data(altium_config)
        
        total_components = sum(len(table_data.get('data', [])) 
                             for table_data in altium_data.values())
        click.secho(f"Found {total_components} components in {len(altium_data)} tables", fg='green')
        
        # Map components
        click.secho("Mapping components to KiCAD format...", fg='blue')
        mapper = ComponentMappingEngine(config.get('kicad_symbol_libraries', []), config_manager)
        
        all_mappings = {}
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                click.secho(f"Processing table: {table_name}", fg='blue')
                
                # Create progress bar
                with create_progress_bar(len(table_data['data']), f"Mapping {table_name}") as bar:
                    # Map components
                    mappings = mapper.map_table_data(table_name, table_data)
                    all_mappings[table_name] = mappings
                    
                    # Update progress bar to completion
                    bar.update(len(table_data['data']))
                
                # Report statistics
                high_conf = sum(1 for m in mappings if m.confidence > 0.8)
                med_conf = sum(1 for m in mappings if 0.5 <= m.confidence <= 0.8)
                low_conf = sum(1 for m in mappings if m.confidence < 0.5)
                
                click.secho(f"Table {table_name} mapping statistics:", fg='blue')
                click.echo(f"  Total components: {len(mappings)}")
                click.echo(f"  High confidence: {high_conf}")
                click.echo(f"  Medium confidence: {med_conf}")
                click.echo(f"  Low confidence: {low_conf}")
        
        if dry_run:
            click.secho("Dry run completed. No files were created.", fg='yellow')
            return 0
        
        # Generate KiCAD database
        click.secho("Generating KiCAD database library...", fg='blue')
        generator = KiCADDbLibGenerator(config['output_directory'], config_manager)
        result = generator.generate(all_mappings)
        
        click.secho("Migration completed successfully!", fg='green')
        click.echo(f"Database: {result['database_path']}")
        click.echo(f"Library file: {result['dblib_path']}")
        click.echo(f"Output directory: {result['output_directory']}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        click.secho(f"Migration failed: {e}", fg='red')
        return 1


@cli.command('validate')
@click.argument('dblib_file', type=click.Path(exists=True))
@common_options
def validate(dblib_file, config, verbose, log_level, log_file):
    """Validate Altium database files and connections.
    
    DBLIB_FILE is the path to the Altium .DbLib file to validate.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else log_level
    logger = setup_logging(
        log_level=log_level,
        log_file=log_file
    )
    
    try:
        click.secho(f"Validating Altium database: {dblib_file}", fg='blue')
        
        # Load configuration
        config_manager = ConfigManager(config)
        config_manager.set('altium_dblib_path', dblib_file)
        
        # Parse DbLib file
        parser = AltiumDbLibParser(config_manager)
        altium_config = parser.parse_dblib_file(dblib_file)
        
        # Check database connection
        click.secho("Testing database connection...", fg='blue')
        try:
            conn = parser.connect_to_database()
            click.secho("Database connection successful!", fg='green')
            
            # Validate tables
            click.secho("Validating database tables...", fg='blue')
            tables_valid = True
            
            for table_name, table_config in altium_config.get('tables', {}).items():
                if table_exists(conn, table_name):
                    click.echo(f"Table '{table_name}' exists")
                    
                    # Check required fields
                    required_fields = table_config.get('required_fields', [])
                    if required_fields:
                        query = f"SELECT * FROM {table_name} LIMIT 1"
                        result = execute_query(conn, query)
                        
                        if result:
                            columns = result[0].keys()
                            missing_fields = [field for field in required_fields if field not in columns]
                            
                            if missing_fields:
                                click.secho(f"  Warning: Missing required fields in '{table_name}': {', '.join(missing_fields)}", fg='yellow')
                                tables_valid = False
                            else:
                                click.echo(f"  All required fields present in '{table_name}'")
                        else:
                            click.secho(f"  Warning: Table '{table_name}' is empty", fg='yellow')
                else:
                    click.secho(f"Table '{table_name}' does not exist", fg='red')
                    tables_valid = False
            
            conn.close()
            
            if tables_valid:
                click.secho("All database tables are valid!", fg='green')
            else:
                click.secho("Some database tables have issues. See warnings above.", fg='yellow')
                
        except Exception as e:
            click.secho(f"Database connection failed: {e}", fg='red')
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        click.secho(f"Validation failed: {e}", fg='red')
        return 1


@cli.command('batch')
@click.argument('input_dir', type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(), default='output', help='Output directory for KiCAD database files')
@click.option('--pattern', default='*.DbLib', help='File pattern to match Altium .DbLib files')
@click.option('--parallel/--no-parallel', default=True, help='Enable/disable parallel processing')
@click.option('--threads', type=int, default=4, help='Number of worker threads for parallel processing')
@common_options
def batch(input_dir, output_dir, pattern, parallel, threads, config, verbose, log_level, log_file):
    """Batch process multiple Altium database files.
    
    INPUT_DIR is the directory containing Altium .DbLib files to process.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else log_level
    logger = setup_logging(
        log_level=log_level,
        log_file=log_file
    )
    
    try:
        # Find all DbLib files
        input_path = Path(input_dir)
        dblib_files = list(input_path.glob(pattern))
        
        if not dblib_files:
            click.secho(f"No files matching pattern '{pattern}' found in {input_dir}", fg='red')
            return 1
        
        click.secho(f"Found {len(dblib_files)} Altium database files to process", fg='green')
        
        # Load configuration
        config_manager = ConfigManager(config)
        
        # Process each file
        results = []
        
        if parallel and len(dblib_files) > 1:
            click.secho(f"Processing files in parallel with {threads} workers...", fg='blue')
            
            def process_file(dblib_file):
                try:
                    # Create output subdirectory based on filename
                    file_output_dir = Path(output_dir) / dblib_file.stem
                    file_output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Update config for this file
                    file_config = config_manager.config.copy()
                    file_config['altium_dblib_path'] = str(dblib_file)
                    file_config['output_directory'] = str(file_output_dir)
                    
                    # Process file
                    click.echo(f"Processing {dblib_file.name}...")
                    
                    # Parse Altium database
                    parser = AltiumDbLibParser()
                    parser.config = file_config
                    altium_config = parser.parse_dblib_file(str(dblib_file))
                    
                    # Extract data
                    altium_data = parser.extract_all_data(altium_config)
                    
                    # Map components
                    mapper = ComponentMappingEngine()
                    mapper.config = file_config
                    
                    all_mappings = {}
                    for table_name, table_data in altium_data.items():
                        if 'data' in table_data and table_data['data']:
                            mappings = mapper.map_table_data(table_name, table_data)
                            all_mappings[table_name] = mappings
                    
                    # Generate KiCAD database
                    generator = KiCADDbLibGenerator(str(file_output_dir))
                    generator.config = file_config
                    result = generator.generate(all_mappings)
                    
                    return {
                        'file': dblib_file.name,
                        'success': True,
                        'output': str(file_output_dir),
                        'components': sum(len(mappings) for mappings in all_mappings.values())
                    }
                except Exception as e:
                    return {
                        'file': dblib_file.name,
                        'success': False,
                        'error': str(e)
                    }
            
            # Process files in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                results = list(executor.map(process_file, dblib_files))
        
        else:
            # Process files sequentially
            with create_progress_bar(len(dblib_files), "Processing files") as bar:
                for dblib_file in dblib_files:
                    try:
                        # Create output subdirectory based on filename
                        file_output_dir = Path(output_dir) / dblib_file.stem
                        file_output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Update config for this file
                        file_config = config_manager.config.copy()
                        file_config['altium_dblib_path'] = str(dblib_file)
                        file_config['output_directory'] = str(file_output_dir)
                        
                        # Process file
                        click.echo(f"Processing {dblib_file.name}...")
                        
                        # Parse Altium database
                        parser = AltiumDbLibParser()
                        parser.config = file_config
                        altium_config = parser.parse_dblib_file(str(dblib_file))
                        
                        # Extract data
                        altium_data = parser.extract_all_data(altium_config)
                        
                        # Map components
                        mapper = ComponentMappingEngine()
                        mapper.config = file_config
                        
                        all_mappings = {}
                        for table_name, table_data in altium_data.items():
                            if 'data' in table_data and table_data['data']:
                                mappings = mapper.map_table_data(table_name, table_data)
                                all_mappings[table_name] = mappings
                        
                        # Generate KiCAD database
                        generator = KiCADDbLibGenerator(str(file_output_dir))
                        generator.config = file_config
                        result = generator.generate(all_mappings)
                        
                        results.append({
                            'file': dblib_file.name,
                            'success': True,
                            'output': str(file_output_dir),
                            'components': sum(len(mappings) for mappings in all_mappings.values())
                        })
                        
                    except Exception as e:
                        results.append({
                            'file': dblib_file.name,
                            'success': False,
                            'error': str(e)
                        })
                    
                    bar.update(1)
        
        # Display results
        click.secho("\nBatch processing results:", fg='blue')
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        click.echo(f"Total files processed: {len(results)}")
        click.echo(f"Successful: {successful}")
        click.echo(f"Failed: {failed}")
        
        if failed > 0:
            click.secho("\nFailed files:", fg='yellow')
            for result in results:
                if not result['success']:
                    click.echo(f"  {result['file']}: {result['error']}")
        
        # Save batch report
        report_path = Path(output_dir) / "batch_report.json"
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_files': len(results),
                'successful': successful,
                'failed': failed,
                'results': results
            }, f, indent=2)
        
        click.echo(f"\nBatch report saved to: {report_path}")
        
        return 0 if failed == 0 else 1
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        click.secho(f"Batch processing failed: {e}", fg='red')
        return 1


@cli.group('config')
def config_group():
    """Configuration management commands."""
    pass


@config_group.command('generate')
@click.argument('output_file', type=click.Path())
def config_generate(output_file):
    """Generate default configuration file.
    
    OUTPUT_FILE is the path where the configuration file will be saved.
    """
    try:
        config_manager = ConfigManager()
        success = config_manager.generate_default_config(output_file)
        
        if success:
            click.secho(f"Default configuration generated at: {output_file}", fg='green')
            return 0
        else:
            click.secho(f"Failed to generate configuration file", fg='red')
            return 1
            
    except Exception as e:
        click.secho(f"Error generating configuration: {e}", fg='red')
        return 1


@config_group.command('show')
@click.argument('config_file', type=click.Path(exists=True))
def config_show(config_file):
    """Show configuration file contents.
    
    CONFIG_FILE is the path to the configuration file to display.
    """
    try:
        config_manager = ConfigManager(config_file)
        
        click.secho(f"Configuration from: {config_file}", fg='blue')
        
        # Format and display config
        for section, items in {
            'Input Settings': ['altium_dblib_path', 'connection_timeout'],
            'Output Settings': ['output_directory', 'database_name', 'dblib_name'],
            'KiCAD Libraries': ['kicad_symbol_libraries', 'kicad_footprint_libraries'],
            'Mapping Settings': ['enable_fuzzy_matching', 'fuzzy_threshold', 'enable_ml_matching'],
            'Performance Settings': ['enable_parallel_processing', 'max_worker_threads', 'batch_size', 'enable_caching'],
            'Database Settings': ['create_indexes', 'create_views', 'vacuum_database'],
            'Logging Settings': ['log_level', 'log_file']
        }.items():
            click.secho(f"\n{section}:", fg='green')
            for key in items:
                value = config_manager.get(key)
                click.echo(f"  {key}: {value}")
        
        # Validate configuration
        issues = config_manager.validate()
        if issues:
            click.secho("\nConfiguration Issues:", fg='red')
            for key, issue in issues.items():
                click.echo(f"  {key}: {issue}")
        
        return 0
            
    except Exception as e:
        click.secho(f"Error reading configuration: {e}", fg='red')
        return 1


@config_group.command('validate')
@click.argument('config_file', type=click.Path(exists=True))
def config_validate(config_file):
    """Validate configuration file.
    
    CONFIG_FILE is the path to the configuration file to validate.
    """
    try:
        config_manager = ConfigManager(config_file)
        issues = config_manager.validate()
        
        if not issues:
            click.secho(f"Configuration is valid: {config_file}", fg='green')
            return 0
        else:
            click.secho(f"Configuration has issues: {config_file}", fg='red')
            for key, issue in issues.items():
                click.echo(f"  {key}: {issue}")
            return 1
            
    except Exception as e:
        click.secho(f"Error validating configuration: {e}", fg='red')
        return 1


@cli.command('test-connection')
@click.argument('dblib_file', type=click.Path(exists=True))
@common_options
def test_connection(dblib_file, config, verbose, log_level, log_file):
    """Test database connectivity.
    
    DBLIB_FILE is the path to the Altium .DbLib file to test.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else log_level
    logger = setup_logging(
        log_level=log_level,
        log_file=log_file
    )
    
    try:
        click.secho(f"Testing connection to database in: {dblib_file}", fg='blue')
        
        # Load configuration
        config_manager = ConfigManager(config)
        config_manager.set('altium_dblib_path', dblib_file)
        
        # Parse DbLib file
        parser = AltiumDbLibParser(config_manager)
        altium_config = parser.parse_dblib_file(dblib_file)
        
        # Get database type
        db_type = parser._detect_database_type()
        click.echo(f"Database type: {db_type}")
        
        # Test connection
        click.echo("Attempting to connect...")
        conn = parser.connect_to_database()
        
        # Get database info
        tables = []
        if db_type == 'sqlite':
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables = [row['name'] for row in execute_query(conn, query)]
        else:
            # For other database types, try to get table list
            try:
                cursor = conn.cursor()
                tables = [table.table_name for table in cursor.tables()]
                cursor.close()
            except:
                click.secho("Could not retrieve table list", fg='yellow')
        
        conn.close()
        
        click.secho("Connection successful!", fg='green')
        
        if tables:
            click.echo(f"Found {len(tables)} tables:")
            for table in tables:
                click.echo(f"  - {table}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}", exc_info=True)
        click.secho(f"Connection test failed: {e}", fg='red')
        return 1


@cli.command('generate-mapping')
@click.option('--output-dir', '-o', type=click.Path(), default='.', help='Output directory for mapping rule templates')
@click.option('--type', '-t', type=click.Choice(['symbol', 'footprint', 'category']), default='symbol', help='Type of mapping rules to generate')
@common_options
def generate_mapping(output_dir, type, config, verbose, log_level, log_file):
    """Generate mapping rule templates.
    
    This command creates template files for custom mapping rules.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else log_level
    logger = setup_logging(
        log_level=log_level,
        log_file=log_file
    )
    
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if type == 'symbol':
            filename = output_path / "symbol_mapping_rules.yaml"
            template = """# Symbol Mapping Rules
# Format: altium_symbol: kicad_symbol

# Resistors
"RES": "Device:R"
"RESISTOR": "Device:R"
"RES SMD": "Device:R_SMD"

# Capacitors
"CAP": "Device:C"
"CAPACITOR": "Device:C"
"CAP SMD": "Device:C_SMD"

# Add your custom symbol mappings below:
# "ALTIUM_SYMBOL": "KICAD_SYMBOL"

"""
        elif type == 'footprint':
            filename = output_path / "footprint_mapping_rules.yaml"
            template = """# Footprint Mapping Rules
# Format: altium_footprint: kicad_footprint

# Resistors
"AXIAL-0.3": "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal"
"AXIAL-0.4": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
"0603": "Resistor_SMD:R_0603_1608Metric"
"0805": "Resistor_SMD:R_0805_2012Metric"

# Capacitors
"RADIAL-0.1": "Capacitor_THT:C_Radial_D4.0mm_H5.0mm_P1.5mm"
"RADIAL-0.2": "Capacitor_THT:C_Radial_D5.0mm_H5.0mm_P2.0mm"
"0603-CAP": "Capacitor_SMD:C_0603_1608Metric"
"0805-CAP": "Capacitor_SMD:C_0805_2012Metric"

# Add your custom footprint mappings below:
# "ALTIUM_FOOTPRINT": "KICAD_FOOTPRINT"

"""
        elif type == 'category':
            filename = output_path / "category_mapping_rules.yaml"
            template = """# Category Mapping Rules
# Format: 
#   altium_category:
#     category: kicad_category
#     subcategory: kicad_subcategory
#     keywords: [keyword1, keyword2, ...]

# Resistors
"Resistors":
  category: "Passive Components"
  subcategory: "Resistors"
  keywords: ["resistor", "res"]

# Capacitors
"Capacitors":
  category: "Passive Components"
  subcategory: "Capacitors"
  keywords: ["capacitor", "cap"]

# Integrated Circuits
"ICs":
  category: "Active Components"
  subcategory: "Integrated Circuits"
  keywords: ["ic", "chip", "integrated circuit"]

# Add your custom category mappings below:
# "ALTIUM_CATEGORY":
#   category: "KICAD_CATEGORY"
#   subcategory: "KICAD_SUBCATEGORY"
#   keywords: ["keyword1", "keyword2"]

"""
        
        with open(filename, 'w') as f:
            f.write(template)
        
        click.secho(f"Mapping rule template generated: {filename}", fg='green')
        click.echo("Edit this file to customize component mappings.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate mapping template: {e}", exc_info=True)
        click.secho(f"Failed to generate mapping template: {e}", fg='red')
        return 1


@cli.command('show-stats')
@click.argument('output_dir', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
def show_stats(output_dir, format):
    """Display migration statistics and reports.
    
    OUTPUT_DIR is the directory containing migration results.
    """
    try:
        output_path = Path(output_dir)
        report_path = output_path / "migration_report.json"
        
        if not report_path.exists():
            click.secho(f"No migration report found in {output_dir}", fg='red')
            return 1
        
        # Load report
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        if format == 'json':
            # Output as JSON
            click.echo(json.dumps(report, indent=2))
        else:
            # Output as formatted text
            click.secho("Migration Statistics Report", fg='blue', bold=True)
            click.echo("=" * 40)
            
            # Summary
            click.secho("\nSummary:", fg='green')
            for key, value in report['migration_summary'].items():
                click.echo(f"  {key.replace('_', ' ').title()}: {value}")
            
            # Table details
            click.secho("\nTable Details:", fg='green')
            for table_name, details in report['table_details'].items():
                click.echo(f"\n  {table_name}:")
                for key, value in details.items():
                    click.echo(f"    {key.replace('_', ' ').title()}: {value}")
            
            # Confidence breakdown
            if 'confidence_breakdown' in report:
                click.secho("\nConfidence Breakdown:", fg='green')
                for level, count in report['confidence_breakdown'].items():
                    click.echo(f"  {level}: {count}")
        
        return 0
        
    except Exception as e:
        click.secho(f"Failed to display statistics: {e}", fg='red')
        return 1


def main():
    """Main entry point for the CLI."""
    return cli()


if __name__ == "__main__":
    sys.exit(main())