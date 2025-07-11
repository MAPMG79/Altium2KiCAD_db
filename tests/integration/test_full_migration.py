"""
Integration tests for the full migration process.

These tests verify that all components of the system work together correctly
to migrate an Altium database to a KiCAD database.
"""

import os
import pytest
import sqlite3
import json
from pathlib import Path

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.mapping_engine import ComponentMappingEngine
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager


class TestFullMigration:
    """Integration tests for the full migration process."""

    def test_end_to_end_migration(self, migration_test_framework, temp_dir):
        """Test the complete end-to-end migration process."""
        # Set up test data
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir)
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a configuration
        config = {
            'altium_dblib_path': str(dblib_file),
            'output_directory': output_dir,
            'enable_fuzzy_matching': True,
            'fuzzy_threshold': 0.7,
            'enable_ml_mapping': False,
            'enable_parallel_processing': False,
            'create_views': True,
            'vacuum_database': True
        }
        
        # Step 1: Parse Altium DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(config['altium_dblib_path'])
        
        # Verify that the DbLib file was parsed correctly
        assert altium_config is not None
        assert 'connection_string' in altium_config
        assert 'tables' in altium_config
        assert len(altium_config['tables']) > 0
        
        # Step 2: Extract component data
        altium_data = parser.extract_all_data(altium_config)
        
        # Verify that data was extracted
        assert altium_data is not None
        assert len(altium_data) > 0
        
        # Check that each table has data
        for table_name, table_data in altium_data.items():
            assert 'columns' in table_data
            assert 'data' in table_data
            assert len(table_data['data']) > 0
        
        # Step 3: Map components
        mapper = ComponentMappingEngine()
        
        all_mappings = {}
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                # Map components
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
                
                # Verify that mappings were created
                assert len(mappings) > 0
                
                # Check mapping quality
                high_conf = sum(1 for m in mappings if m.confidence > 0.8)
                med_conf = sum(1 for m in mappings if 0.5 <= m.confidence <= 0.8)
                low_conf = sum(1 for m in mappings if m.confidence < 0.5)
                
                # Verify that at least some mappings have high confidence
                assert high_conf > 0
        
        # Step 4: Generate KiCAD database
        generator = KiCADDbLibGenerator(config['output_directory'])
        result = generator.generate(all_mappings)
        
        # Verify that the database was generated
        assert 'database_path' in result
        assert 'dblib_path' in result
        assert 'output_directory' in result
        
        assert os.path.exists(result['database_path'])
        assert os.path.exists(result['dblib_path'])
        
        # Verify database content
        conn = sqlite3.connect(result['database_path'])
        cursor = conn.cursor()
        
        # Check that components table exists and has data
        cursor.execute("SELECT COUNT(*) FROM components")
        component_count = cursor.fetchone()[0]
        assert component_count > 0
        
        # Check that categories table exists and has data
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        assert category_count > 0
        
        # Check that views were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        assert len(views) > 0
        
        # Verify KiCAD DbLib file content
        with open(result['dblib_path'], 'r') as f:
            dblib_config = json.load(f)
        
        assert 'meta' in dblib_config
        assert 'name' in dblib_config
        assert 'description' in dblib_config
        assert 'source' in dblib_config
        assert 'libraries' in dblib_config
        assert len(dblib_config['libraries']) > 0
        
        conn.close()
    
    def test_migration_with_custom_config(self, migration_test_framework, temp_dir):
        """Test migration with a custom configuration."""
        # Set up test data
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir)
        output_dir = os.path.join(temp_dir, "output_custom")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a custom configuration file
        config_path = os.path.join(temp_dir, "custom_config.yaml")
        config_manager = ConfigManager()
        config_manager.set('altium_dblib_path', str(dblib_file))
        config_manager.set('output_directory', output_dir)
        config_manager.set('fuzzy_threshold', 0.8)  # Higher threshold
        config_manager.set('create_views', False)  # Disable views
        config_manager.save_config(config_path)
        
        # Load the configuration
        config_manager = ConfigManager(config_path)
        config = config_manager.config
        
        # Step 1: Parse Altium DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(config['altium_dblib_path'])
        
        # Step 2: Extract component data
        altium_data = parser.extract_all_data(altium_config)
        
        # Step 3: Map components
        mapper = ComponentMappingEngine()
        
        all_mappings = {}
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
        
        # Step 4: Generate KiCAD database
        generator = KiCADDbLibGenerator(config['output_directory'])
        result = generator.generate(all_mappings)
        
        # Verify that the database was generated
        assert os.path.exists(result['database_path'])
        assert os.path.exists(result['dblib_path'])
        
        # Verify database content
        conn = sqlite3.connect(result['database_path'])
        cursor = conn.cursor()
        
        # Check that components table exists and has data
        cursor.execute("SELECT COUNT(*) FROM components")
        component_count = cursor.fetchone()[0]
        assert component_count > 0
        
        # Check that views were not created (as per config)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        assert len(views) == 0
        
        conn.close()
    
    def test_migration_with_error_handling(self, migration_test_framework, temp_dir):
        """Test migration with error handling for invalid inputs."""
        # Set up test data with invalid DbLib file
        invalid_dblib_file = os.path.join(temp_dir, "invalid.DbLib")
        with open(invalid_dblib_file, 'w') as f:
            f.write("This is not a valid DbLib file")
        
        output_dir = os.path.join(temp_dir, "output_error")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a configuration
        config = {
            'altium_dblib_path': invalid_dblib_file,
            'output_directory': output_dir
        }
        
        # Step 1: Parse Altium DbLib file (should raise an exception)
        parser = AltiumDbLibParser()
        
        with pytest.raises(Exception) as excinfo:
            altium_config = parser.parse_dblib_file(config['altium_dblib_path'])
        
        # Verify that an appropriate error was raised
        assert "Invalid DbLib file" in str(excinfo.value) or "Error parsing DbLib file" in str(excinfo.value)
    
    def test_migration_with_empty_tables(self, migration_test_framework, temp_dir):
        """Test migration with empty tables."""
        # Set up test data with empty tables
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir, empty_tables=True)
        output_dir = os.path.join(temp_dir, "output_empty")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a configuration
        config = {
            'altium_dblib_path': str(dblib_file),
            'output_directory': output_dir
        }
        
        # Step 1: Parse Altium DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(config['altium_dblib_path'])
        
        # Step 2: Extract component data
        altium_data = parser.extract_all_data(altium_config)
        
        # Verify that data structure is correct but tables are empty
        assert altium_data is not None
        assert len(altium_data) > 0
        
        for table_name, table_data in altium_data.items():
            assert 'columns' in table_data
            assert 'data' in table_data
            assert len(table_data['data']) == 0
        
        # Step 3: Map components (should result in empty mappings)
        mapper = ComponentMappingEngine()
        
        all_mappings = {}
        for table_name, table_data in altium_data.items():
            mappings = mapper.map_table_data(table_name, table_data)
            all_mappings[table_name] = mappings
            
            # Verify that mappings are empty
            assert len(mappings) == 0
        
        # Step 4: Generate KiCAD database
        generator = KiCADDbLibGenerator(config['output_directory'])
        result = generator.generate(all_mappings)
        
        # Verify that the database was generated
        assert os.path.exists(result['database_path'])
        assert os.path.exists(result['dblib_path'])
        
        # Verify database content
        conn = sqlite3.connect(result['database_path'])
        cursor = conn.cursor()
        
        # Check that components table exists but is empty
        cursor.execute("SELECT COUNT(*) FROM components")
        component_count = cursor.fetchone()[0]
        assert component_count == 0
        
        conn.close()