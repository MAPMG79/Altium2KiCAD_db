"""
Integration tests for file operations.

These tests verify that file operations work correctly across
different components of the system.
"""

import os
import json
import yaml
import pytest
from pathlib import Path

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager


class TestFileOperations:
    """Integration tests for file operations."""

    def test_altium_dblib_file_parsing(self, migration_test_framework, temp_dir):
        """Test parsing an Altium DbLib file."""
        # Create a sample DbLib file
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir)
        
        # Parse the DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(str(dblib_file))
        
        # Verify that the file was parsed correctly
        assert altium_config is not None
        assert 'connection_string' in altium_config
        assert 'tables' in altium_config
        assert len(altium_config['tables']) > 0
        
        # Verify that the connection string was extracted correctly
        with open(dblib_file, 'r') as f:
            dblib_content = f.read()
            assert altium_config['connection_string'] in dblib_content
        
        # Verify that all tables were extracted
        for table_name in altium_config['tables']:
            assert table_name in dblib_content
    
    def test_altium_dblib_file_with_multiple_tables(self, migration_test_framework, temp_dir):
        """Test parsing an Altium DbLib file with multiple tables."""
        # Create a sample DbLib file with multiple tables
        table_names = ['Resistors', 'Capacitors', 'Diodes', 'Transistors', 'ICs']
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir, table_names=table_names)
        
        # Parse the DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(str(dblib_file))
        
        # Verify that all tables were extracted
        assert set(altium_config['tables']) == set(table_names)
    
    def test_altium_dblib_file_with_invalid_format(self, temp_dir):
        """Test parsing an Altium DbLib file with invalid format."""
        # Create an invalid DbLib file
        dblib_file = os.path.join(temp_dir, "invalid.DbLib")
        with open(dblib_file, 'w') as f:
            f.write("This is not a valid DbLib file")
        
        # Parse the DbLib file
        parser = AltiumDbLibParser()
        
        # Verify that an exception is raised
        with pytest.raises(Exception) as excinfo:
            parser.parse_dblib_file(dblib_file)
        
        # Check the error message
        assert "Invalid DbLib file" in str(excinfo.value) or "Error parsing DbLib file" in str(excinfo.value)
    
    def test_kicad_dblib_file_generation(self, migration_test_framework, temp_dir):
        """Test generating a KiCAD DbLib file."""
        # Set up output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a KiCAD database generator
        generator = KiCADDbLibGenerator(output_dir)
        
        # Create sample component mappings
        component_mappings = migration_test_framework.create_sample_component_mappings()
        
        # Generate the KiCAD DbLib file
        generator.generate_kicad_dblib_file(component_mappings)
        
        # Verify that the file was created
        dblib_path = os.path.join(output_dir, "components.kicad_dbl")
        assert os.path.exists(dblib_path)
        
        # Verify the file content
        with open(dblib_path, 'r') as f:
            dblib_config = json.load(f)
        
        # Check that the file has the required sections
        assert 'meta' in dblib_config
        assert 'name' in dblib_config
        assert 'description' in dblib_config
        assert 'source' in dblib_config
        assert 'libraries' in dblib_config
        
        # Check that the source configuration is correct
        assert dblib_config['source']['type'] == 'odbc'
        assert 'Driver=SQLite3;Database=' in dblib_config['source']['connection_string']
        
        # Check that libraries are defined
        assert len(dblib_config['libraries']) > 0
        
        # Check that the All Components library is defined
        all_components = next((lib for lib in dblib_config['libraries'] if lib['name'] == 'All Components'), None)
        assert all_components is not None
        assert all_components['table'] == 'components'
        assert all_components['key'] == 'id'
        assert all_components['symbols'] == 'symbol'
        assert all_components['footprints'] == 'footprint'
        assert 'fields' in all_components
    
    def test_kicad_dblib_file_with_custom_name(self, migration_test_framework, temp_dir):
        """Test generating a KiCAD DbLib file with a custom name."""
        # Set up output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a KiCAD database generator with a custom DbLib name
        custom_name = "custom_components.kicad_dbl"
        generator = KiCADDbLibGenerator(output_dir, dblib_name=custom_name)
        
        # Create sample component mappings
        component_mappings = migration_test_framework.create_sample_component_mappings()
        
        # Generate the KiCAD DbLib file
        generator.generate_kicad_dblib_file(component_mappings)
        
        # Verify that the file was created with the custom name
        dblib_path = os.path.join(output_dir, custom_name)
        assert os.path.exists(dblib_path)
    
    def test_migration_report_generation(self, migration_test_framework, temp_dir):
        """Test generating a migration report file."""
        # Set up output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a KiCAD database generator
        generator = KiCADDbLibGenerator(output_dir)
        
        # Create sample component mappings with different confidence levels
        component_mappings = {
            'Resistors': [
                migration_test_framework.create_component_mapping(confidence=0.9),
                migration_test_framework.create_component_mapping(confidence=0.7),
                migration_test_framework.create_component_mapping(confidence=0.4)
            ],
            'Capacitors': [
                migration_test_framework.create_component_mapping(confidence=0.9),
                migration_test_framework.create_component_mapping(confidence=0.6)
            ]
        }
        
        # Generate the migration report
        generator.generate_migration_report(component_mappings)
        
        # Verify that the report file was created
        report_path = os.path.join(output_dir, "migration_report.json")
        assert os.path.exists(report_path)
        
        # Verify the report content
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Check that the report has the required sections
        assert 'migration_summary' in report
        assert 'table_details' in report
        assert 'issues' in report
        assert 'recommendations' in report
        
        # Check that the summary statistics are correct
        summary = report['migration_summary']
        assert summary['total_tables'] == 2
        assert summary['total_components'] == 5
        assert summary['high_confidence'] == 2
        assert summary['medium_confidence'] == 2
        assert summary['low_confidence'] == 1
    
    def test_config_file_loading_yaml(self, temp_dir):
        """Test loading a YAML configuration file."""
        # Create a YAML configuration file
        config_path = os.path.join(temp_dir, "config.yaml")
        test_config = {
            'altium_dblib_path': 'test.DbLib',
            'output_directory': 'output',
            'fuzzy_threshold': 0.8,
            'enable_ml_mapping': True
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Load the configuration
        config_manager = ConfigManager(config_path)
        
        # Verify that the configuration was loaded correctly
        assert config_manager.get('altium_dblib_path') == 'test.DbLib'
        assert config_manager.get('output_directory') == 'output'
        assert config_manager.get('fuzzy_threshold') == 0.8
        assert config_manager.get('enable_ml_mapping') is True
    
    def test_config_file_loading_json(self, temp_dir):
        """Test loading a JSON configuration file."""
        # Create a JSON configuration file
        config_path = os.path.join(temp_dir, "config.json")
        test_config = {
            'altium_dblib_path': 'test.DbLib',
            'output_directory': 'output',
            'fuzzy_threshold': 0.8,
            'enable_ml_mapping': True
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Load the configuration
        config_manager = ConfigManager(config_path)
        
        # Verify that the configuration was loaded correctly
        assert config_manager.get('altium_dblib_path') == 'test.DbLib'
        assert config_manager.get('output_directory') == 'output'
        assert config_manager.get('fuzzy_threshold') == 0.8
        assert config_manager.get('enable_ml_mapping') is True
    
    def test_config_file_saving_yaml(self, temp_dir):
        """Test saving a configuration to a YAML file."""
        # Create a configuration
        config_path = os.path.join(temp_dir, "config.yaml")
        config_manager = ConfigManager()
        
        # Set some configuration values
        config_manager.set('altium_dblib_path', 'test.DbLib')
        config_manager.set('output_directory', 'output')
        config_manager.set('fuzzy_threshold', 0.8)
        config_manager.set('enable_ml_mapping', True)
        
        # Save the configuration
        config_manager.save_config(config_path)
        
        # Verify that the file was created
        assert os.path.exists(config_path)
        
        # Load the configuration again
        new_config_manager = ConfigManager(config_path)
        
        # Verify that the values were saved correctly
        assert new_config_manager.get('altium_dblib_path') == 'test.DbLib'
        assert new_config_manager.get('output_directory') == 'output'
        assert new_config_manager.get('fuzzy_threshold') == 0.8
        assert new_config_manager.get('enable_ml_mapping') is True
    
    def test_config_file_saving_json(self, temp_dir):
        """Test saving a configuration to a JSON file."""
        # Create a configuration
        config_path = os.path.join(temp_dir, "config.json")
        config_manager = ConfigManager()
        
        # Set some configuration values
        config_manager.set('altium_dblib_path', 'test.DbLib')
        config_manager.set('output_directory', 'output')
        config_manager.set('fuzzy_threshold', 0.8)
        config_manager.set('enable_ml_mapping', True)
        
        # Save the configuration
        config_manager.save_config(config_path)
        
        # Verify that the file was created
        assert os.path.exists(config_path)
        
        # Load the configuration again
        new_config_manager = ConfigManager(config_path)
        
        # Verify that the values were saved correctly
        assert new_config_manager.get('altium_dblib_path') == 'test.DbLib'
        assert new_config_manager.get('output_directory') == 'output'
        assert new_config_manager.get('fuzzy_threshold') == 0.8
        assert new_config_manager.get('enable_ml_mapping') is True
    
    def test_file_path_handling(self, migration_test_framework, temp_dir):
        """Test handling of file paths across components."""
        # Create a sample DbLib file
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir)
        
        # Set up output directory with a nested structure
        output_dir = os.path.join(temp_dir, "output", "nested", "dir")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a configuration
        config_path = os.path.join(temp_dir, "config", "test_config.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        config_manager = ConfigManager()
        config_manager.set('altium_dblib_path', str(dblib_file))
        config_manager.set('output_directory', output_dir)
        config_manager.save_config(config_path)
        
        # Load the configuration
        loaded_config_manager = ConfigManager(config_path)
        config = loaded_config_manager.config
        
        # Parse the DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(config['altium_dblib_path'])
        
        # Extract data
        altium_data = parser.extract_all_data(altium_config)
        
        # Create sample component mappings
        component_mappings = migration_test_framework.create_sample_component_mappings()
        
        # Generate the KiCAD database
        generator = KiCADDbLibGenerator(config['output_directory'])
        result = generator.generate(component_mappings)
        
        # Verify that the output files were created in the correct location
        assert os.path.exists(result['database_path'])
        assert os.path.exists(result['dblib_path'])
        assert os.path.dirname(result['database_path']) == output_dir
        assert os.path.dirname(result['dblib_path']) == output_dir
    
    def test_file_error_handling(self, temp_dir):
        """Test handling of file errors."""
        # Test loading a nonexistent configuration file
        nonexistent_config = os.path.join(temp_dir, "nonexistent.yaml")
        config_manager = ConfigManager(nonexistent_config)
        
        # Verify that default values are used
        assert config_manager.get('output_directory') == 'output'
        
        # Test saving to a directory without write permissions
        if os.name == 'posix':  # Skip on Windows
            # Create a directory without write permissions
            no_write_dir = os.path.join(temp_dir, "no_write")
            os.makedirs(no_write_dir)
            os.chmod(no_write_dir, 0o555)  # Read and execute only
            
            # Try to save a configuration file
            no_write_config = os.path.join(no_write_dir, "config.yaml")
            result = config_manager.save_config(no_write_config)
            
            # Verify that the save operation failed
            assert result is False
            
            # Restore permissions for cleanup
            os.chmod(no_write_dir, 0o755)
        
        # Test parsing a nonexistent DbLib file
        parser = AltiumDbLibParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_dblib_file(os.path.join(temp_dir, "nonexistent.DbLib"))