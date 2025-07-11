# Batch Processing Multiple Databases

This tutorial demonstrates how to use the Altium to KiCAD Database Migration Tool to process multiple Altium database libraries in batch mode. Batch processing is useful when you need to migrate several libraries at once, saving time and ensuring consistent results.

## Use Cases for Batch Processing

Batch processing is particularly useful in these scenarios:

1. **Component Library Migration**: Migrating multiple component libraries organized by category (resistors, capacitors, ICs, etc.)
2. **Enterprise Migration**: Converting all company libraries during a transition from Altium to KiCAD
3. **Vendor Library Updates**: Processing updated vendor libraries periodically
4. **CI/CD Integration**: Automating library migration as part of a continuous integration pipeline

## Prerequisites

Before starting this tutorial, ensure you have:

1. Installed the Altium to KiCAD Database Migration Tool (see [Installation Guide](../user_guide/installation.md))
2. Access to multiple Altium DbLib files or databases
3. Appropriate database drivers installed (if applicable)
4. Basic familiarity with both Altium and KiCAD

## Example Scenario

In this tutorial, we'll migrate multiple component libraries organized by category:

- `resistors.DbLib`: Resistor components
- `capacitors.DbLib`: Capacitor components
- `inductors.DbLib`: Inductor components
- `diodes.DbLib`: Diode components
- `transistors.DbLib`: Transistor components

## Method 1: Using the Command Line

### Step 1: Create a Batch Configuration File

Create a file named `batch_config.yaml` with the following content:

```yaml
# Global settings applied to all migrations
global:
  output:
    directory: output/
    format: sqlite
    create_report: true
  
  mapping:
    confidence_threshold: 0.7
    use_custom_rules: true
    custom_rules_path: mapping_rules.yaml
  
  validation:
    validate_symbols: true
    validate_footprints: true
    report_missing: true
  
  performance:
    parallel_processing: true
    max_workers: 4
    batch_size: 100
    cache_results: true
    cache_path: .cache/

# Individual library configurations
libraries:
  - input:
      path: path/to/resistors.DbLib
    output:
      library_name: Resistors
    mapping:
      # Override specific settings for this library
      confidence_threshold: 0.8
  
  - input:
      path: path/to/capacitors.DbLib
    output:
      library_name: Capacitors
  
  - input:
      path: path/to/inductors.DbLib
    output:
      library_name: Inductors
  
  - input:
      path: path/to/diodes.DbLib
    output:
      library_name: Diodes
  
  - input:
      path: path/to/transistors.DbLib
    output:
      library_name: Transistors
```

### Step 2: Create Mapping Rules

Create a file named `mapping_rules.yaml` with mapping rules for all component types:

```yaml
# Mapping rules for various component types
symbols:
  # Resistors
  - altium_pattern: "RES.*"
    kicad_symbol: "Device:R"
    confidence: 0.9
  
  # Capacitors
  - altium_pattern: "CAP.*"
    kicad_symbol: "Device:C"
    confidence: 0.9
  
  - altium_pattern: "C-POLARIZED.*"
    kicad_symbol: "Device:CP"
    confidence: 0.9
  
  # Inductors
  - altium_pattern: "IND.*"
    kicad_symbol: "Device:L"
    confidence: 0.9
  
  # Diodes
  - altium_pattern: "DIODE.*"
    kicad_symbol: "Device:D"
    confidence: 0.9
  
  - altium_pattern: "LED.*"
    kicad_symbol: "Device:LED"
    confidence: 0.9
  
  # Transistors
  - altium_pattern: "NPN.*"
    kicad_symbol: "Device:Q_NPN_BCE"
    confidence: 0.9
  
  - altium_pattern: "PNP.*"
    kicad_symbol: "Device:Q_PNP_BCE"
    confidence: 0.9

footprints:
  # Common footprints
  - altium_pattern: "SMD-.*0603.*"
    kicad_footprint: "Resistor_SMD:R_0603_1608Metric"
    confidence: 0.9
  
  - altium_pattern: "SMD-.*0805.*"
    kicad_footprint: "Resistor_SMD:R_0805_2012Metric"
    confidence: 0.9
  
  # Add more footprint mappings as needed

categories:
  - altium_pattern: "Resistors"
    kicad_category: "Passive Components/Resistors"
    confidence: 1.0
  
  - altium_pattern: "Capacitors"
    kicad_category: "Passive Components/Capacitors"
    confidence: 1.0
  
  - altium_pattern: "Inductors"
    kicad_category: "Passive Components/Inductors"
    confidence: 1.0
  
  - altium_pattern: "Diodes"
    kicad_category: "Semiconductors/Diodes"
    confidence: 1.0
  
  - altium_pattern: "Transistors"
    kicad_category: "Semiconductors/Transistors"
    confidence: 1.0
```

### Step 3: Run the Batch Migration

Execute the batch migration using the command line:

```bash
altium2kicad --batch-config batch_config.yaml
```

You should see output showing the progress of each library migration:

```
Altium to KiCAD Database Migration Tool v1.0.0
==============================================

Loading batch configuration from batch_config.yaml
Found 5 libraries to process

Processing library 1/5: Resistors
--------------------------------
Connecting to Altium database: path/to/resistors.DbLib
Successfully connected to database
Extracting components...
Found 150 components
Mapping components...
[====================] 100% (150/150)
Mapping complete: 150 components mapped
Generating KiCAD library...
Creating SQLite database: output/Resistors.sqlite
Library generation complete
Generating report...
Report saved to: output/Resistors_report.html

Processing library 2/5: Capacitors
---------------------------------
Connecting to Altium database: path/to/capacitors.DbLib
...

[Processing continues for all libraries]

Batch Migration Summary:
- Libraries Processed: 5
- Total Components: 750
- Successfully Mapped: 745 (99.3%)
- High Confidence Mappings: 730 (97.3%)
- Low Confidence Mappings: 15 (2.0%)
- Failed Mappings: 5 (0.7%)
- Warnings: 3
- Errors: 0

Batch migration completed successfully in 25.7 seconds
```

## Method 2: Using the Python API

For more control and customization, you can use the Python API to implement batch processing:

```python
import os
import yaml
from migration_tool import MigrationAPI
from datetime import datetime

def process_libraries(batch_config_path):
    """Process multiple libraries based on a batch configuration file."""
    # Load batch configuration
    with open(batch_config_path, 'r') as f:
        batch_config = yaml.safe_load(f)
    
    # Initialize API
    api = MigrationAPI()
    
    # Get global settings
    global_settings = batch_config.get('global', {})
    
    # Prepare results
    results = {
        'libraries_processed': 0,
        'total_components': 0,
        'success_count': 0,
        'high_confidence_count': 0,
        'low_confidence_count': 0,
        'failed_count': 0,
        'warnings': 0,
        'errors': 0,
        'libraries': []
    }
    
    # Process each library
    libraries = batch_config.get('libraries', [])
    for i, library_config in enumerate(libraries):
        # Merge global and library-specific settings
        config = {}
        for section in ['input', 'output', 'mapping', 'validation', 'performance']:
            if section in global_settings:
                config[section] = global_settings[section].copy()
            if section in library_config:
                if section not in config:
                    config[section] = {}
                config[section].update(library_config[section])
        
        # Get library name for logging
        library_name = config.get('output', {}).get('library_name', f'Library_{i+1}')
        print(f"\nProcessing library {i+1}/{len(libraries)}: {library_name}")
        print("-" * (len(library_name) + 24))
        
        # Run migration for this library
        try:
            result = api.run_migration(config)
            
            # Update overall results
            results['libraries_processed'] += 1
            results['total_components'] += result.get('component_count', 0)
            results['success_count'] += result.get('success_count', 0)
            results['high_confidence_count'] += result.get('high_confidence_count', 0)
            results['low_confidence_count'] += result.get('low_confidence_count', 0)
            results['failed_count'] += result.get('component_count', 0) - result.get('success_count', 0)
            results['warnings'] += result.get('warning_count', 0)
            results['errors'] += result.get('error_count', 0)
            
            # Store library result
            results['libraries'].append({
                'name': library_name,
                'success': result.get('success', False),
                'component_count': result.get('component_count', 0),
                'success_count': result.get('success_count', 0),
                'output_path': result.get('output_path', ''),
                'report_path': result.get('report_path', ''),
                'duration': result.get('duration', 0)
            })
            
        except Exception as e:
            print(f"Error processing library {library_name}: {str(e)}")
            results['errors'] += 1
            results['libraries'].append({
                'name': library_name,
                'success': False,
                'error': str(e)
            })
    
    # Generate batch summary report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(global_settings.get('output', {}).get('directory', 'output'), 
                              f'batch_report_{timestamp}.html')
    
    # Generate HTML report
    generate_batch_report(results, report_path)
    
    # Print summary
    print("\nBatch Migration Summary:")
    print(f"- Libraries Processed: {results['libraries_processed']}")
    print(f"- Total Components: {results['total_components']}")
    
    if results['total_components'] > 0:
        success_percent = (results['success_count'] / results['total_components']) * 100
        high_conf_percent = (results['high_confidence_count'] / results['total_components']) * 100
        low_conf_percent = (results['low_confidence_count'] / results['total_components']) * 100
        failed_percent = (results['failed_count'] / results['total_components']) * 100
        
        print(f"- Successfully Mapped: {results['success_count']} ({success_percent:.1f}%)")
        print(f"- High Confidence Mappings: {results['high_confidence_count']} ({high_conf_percent:.1f}%)")
        print(f"- Low Confidence Mappings: {results['low_confidence_count']} ({low_conf_percent:.1f}%)")
        print(f"- Failed Mappings: {results['failed_count']} ({failed_percent:.1f}%)")
    
    print(f"- Warnings: {results['warnings']}")
    print(f"- Errors: {results['errors']}")
    print(f"\nBatch report saved to: {report_path}")
    
    return results

def generate_batch_report(results, report_path):
    """Generate an HTML report for the batch migration."""
    # Implementation of report generation
    # This would create an HTML file with tables and charts
    # showing the results of the batch migration
    pass

if __name__ == "__main__":
    process_libraries("batch_config.yaml")
```

Save this script as `batch_migration.py` and run it:

```bash
python batch_migration.py
```

## Method 3: Using Directory Scanning

You can also automatically discover and process all DbLib files in a directory:

```python
import os
import glob
from migration_tool import MigrationAPI

def process_directory(directory_path, output_directory, mapping_rules_path=None):
    """Process all DbLib files in a directory."""
    # Find all DbLib files
    dblib_files = glob.glob(os.path.join(directory_path, "*.DbLib"))
    
    if not dblib_files:
        print(f"No DbLib files found in {directory_path}")
        return
    
    print(f"Found {len(dblib_files)} DbLib files to process")
    
    # Initialize API
    api = MigrationAPI()
    
    # Process each file
    for i, dblib_file in enumerate(dblib_files):
        # Get library name from filename
        library_name = os.path.splitext(os.path.basename(dblib_file))[0]
        print(f"\nProcessing {i+1}/{len(dblib_files)}: {library_name}")
        
        # Create configuration
        config = {
            'input': {
                'path': dblib_file
            },
            'output': {
                'directory': output_directory,
                'library_name': library_name,
                'format': 'sqlite',
                'create_report': True
            },
            'mapping': {
                'confidence_threshold': 0.7
            },
            'validation': {
                'validate_symbols': True,
                'validate_footprints': True
            },
            'performance': {
                'parallel_processing': True,
                'max_workers': 4
            }
        }
        
        # Add custom mapping rules if provided
        if mapping_rules_path:
            config['mapping']['use_custom_rules'] = True
            config['mapping']['custom_rules_path'] = mapping_rules_path
        
        # Run migration
        try:
            result = api.run_migration(config)
            print(f"Completed: {result['success_count']}/{result['component_count']} components migrated")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    process_directory("path/to/libraries", "output", "mapping_rules.yaml")
```

Save this script as `directory_migration.py` and run it:

```bash
python directory_migration.py
```

## Advanced Batch Processing Features

### Parallel Library Processing

For even faster processing, you can process multiple libraries in parallel:

```python
import concurrent.futures
from migration_tool import MigrationAPI

def process_library(config):
    """Process a single library."""
    api = MigrationAPI()
    try:
        result = api.run_migration(config)
        return {
            'success': True,
            'library_name': config.get('output', {}).get('library_name', 'Unknown'),
            'result': result
        }
    except Exception as e:
        return {
            'success': False,
            'library_name': config.get('output', {}).get('library_name', 'Unknown'),
            'error': str(e)
        }

def parallel_batch_process(batch_config_path, max_workers=2):
    """Process libraries in parallel."""
    # Load batch configuration
    with open(batch_config_path, 'r') as f:
        batch_config = yaml.safe_load(f)
    
    # Get global settings
    global_settings = batch_config.get('global', {})
    
    # Prepare configurations for each library
    configs = []
    for library_config in batch_config.get('libraries', []):
        # Merge global and library-specific settings
        config = {}
        for section in ['input', 'output', 'mapping', 'validation', 'performance']:
            if section in global_settings:
                config[section] = global_settings[section].copy()
            if section in library_config:
                if section not in config:
                    config[section] = {}
                config[section].update(library_config[section])
        configs.append(config)
    
    # Process libraries in parallel
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_config = {executor.submit(process_library, config): config for config in configs}
        for future in concurrent.futures.as_completed(future_to_config):
            config = future_to_config[future]
            try:
                result = future.result()
                results.append(result)
                print(f"Completed: {result['library_name']}")
            except Exception as e:
                library_name = config.get('output', {}).get('library_name', 'Unknown')
                print(f"Error processing {library_name}: {str(e)}")
                results.append({
                    'success': False,
                    'library_name': library_name,
                    'error': str(e)
                })
    
    return results
```

### Incremental Processing

For large libraries that are updated regularly, you can implement incremental processing:

```python
def incremental_process(previous_result_path, current_config):
    """Process only components that have changed since the last run."""
    import json
    
    # Load previous results
    with open(previous_result_path, 'r') as f:
        previous_result = json.load(f)
    
    # Get previously processed components
    processed_components = {}
    for component in previous_result.get('components', []):
        processed_components[component['libref']] = component
    
    # Initialize API
    api = MigrationAPI()
    
    # Extract current components
    components = api.parse_altium_database(current_config['input']['path'])
    
    # Identify new or modified components
    components_to_process = []
    for component in components:
        libref = component.get('LibRef')
        if libref not in processed_components:
            # New component
            components_to_process.append(component)
        else:
            # Check if component has changed
            previous = processed_components[libref]
            if component.get('ModifiedDate') != previous.get('ModifiedDate'):
                components_to_process.append(component)
    
    print(f"Found {len(components_to_process)} new or modified components out of {len(components)}")
    
    if not components_to_process:
        print("No changes detected, skipping migration")
        return previous_result
    
    # Process only the changed components
    # [Implementation details...]
```

## Best Practices for Batch Processing

1. **Use a Common Mapping Rules File**: Maintain a single mapping rules file for all libraries to ensure consistency.

2. **Organize Output by Category**: Structure your output directory to match your library organization.
   ```yaml
   output:
     directory: output/passive_components/
   ```

3. **Adjust Confidence Thresholds by Library Type**: Different component types may need different confidence thresholds.
   ```yaml
   # For standard components
   mapping:
     confidence_threshold: 0.7
   
   # For specialized components
   mapping:
     confidence_threshold: 0.6
   ```

4. **Use Caching**: Enable caching to speed up repeated migrations.
   ```yaml
   performance:
     cache_results: true
     cache_path: .cache/
   ```

5. **Generate Comprehensive Reports**: Enable detailed reporting for easier troubleshooting.
   ```yaml
   output:
     create_report: true
     report_format: html
     report_detail_level: high
   ```

6. **Monitor Resource Usage**: For very large libraries, monitor memory usage and adjust batch size accordingly.
   ```yaml
   performance:
     batch_size: 100  # Reduce for memory-constrained environments
     memory_limit: 2048  # MB
   ```

## Conclusion

Batch processing is a powerful feature of the Altium to KiCAD Database Migration Tool that allows you to efficiently migrate multiple libraries while maintaining consistency and quality. By using the techniques described in this tutorial, you can automate the migration process and integrate it into your workflow.

For more advanced scenarios, check out the [Enterprise Setup Guide](enterprise_setup.md) and the [API Reference](../developer_guide/api_reference.md).