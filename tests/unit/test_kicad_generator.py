"""
Unit tests for the KiCAD Database Library Generator module.
"""

import os
import pytest
import sqlite3
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.core.mapping_engine import ComponentMapping


class TestKiCADDbLibGenerator:
    """Test cases for the KiCADDbLibGenerator class."""

    def test_initialization(self, temp_dir):
        """Test initialization of the generator."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        assert generator.output_dir == Path(temp_dir)
        assert generator.db_path == Path(temp_dir) / "components.db"
        assert generator.dblib_path == Path(temp_dir) / "components.kicad_dbl"
    
    def test_create_database_schema(self, temp_dir):
        """Test creating the database schema."""
        generator = KiCADDbLibGenerator(temp_dir)
        generator.create_database_schema()
        
        # Check that the database file was created
        assert os.path.exists(generator.db_path)
        
        # Check that the tables were created
        conn = sqlite3.connect(generator.db_path)
        cursor = conn.cursor()
        
        # Check components table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='components'")
        assert cursor.fetchone() is not None
        
        # Check categories table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        assert cursor.fetchone() is not None
        
        # Check views
        views = ['resistors', 'capacitors', 'inductors', 'integrated_circuits', 'diodes', 'transistors']
        for view in views:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view}'")
            assert cursor.fetchone() is not None
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='components'")
        indexes = cursor.fetchall()
        assert len(indexes) > 0
        
        conn.close()
    
    def test_create_component_views(self, temp_dir):
        """Test creating component views."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Create database and tables
        conn = sqlite3.connect(generator.db_path)
        cursor = conn.cursor()
        
        # Create components table
        cursor.execute("""
            CREATE TABLE components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                footprint TEXT NOT NULL,
                description TEXT,
                keywords TEXT
            )
        """)
        
        # Call the method to create views
        generator._create_component_views(cursor)
        
        # Check that views were created
        views = ['resistors', 'capacitors', 'inductors', 'integrated_circuits', 'diodes', 'transistors']
        for view in views:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view}'")
            assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_populate_categories(self, temp_dir):
        """Test populating categories table."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Create database and tables
        generator.create_database_schema()
        
        # Populate categories
        component_mappings = {'Resistors': [], 'Capacitors': []}
        category_ids = generator.populate_categories(component_mappings)
        
        # Check that categories were created
        assert len(category_ids) > 0
        assert 'Resistors' in category_ids
        assert 'Capacitors' in category_ids
        assert 'Integrated Circuits' in category_ids
        
        # Check database content
        conn = sqlite3.connect(generator.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        assert count > 0
        
        cursor.execute("SELECT name, description FROM categories WHERE name='Resistors'")
        resistors = cursor.fetchone()
        assert resistors is not None
        assert resistors[0] == 'Resistors'
        assert 'Resistive components' in resistors[1]
        
        conn.close()
    
    def test_categorize_component(self, temp_dir):
        """Test categorizing a component."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Create database and tables
        generator.create_database_schema()
        
        # Populate categories
        component_mappings = {'Resistors': [], 'Capacitors': []}
        category_ids = generator.populate_categories(component_mappings)
        
        # Test resistor categorization
        resistor_mapping = ComponentMapping(
            altium_symbol='Resistor',
            altium_footprint='0603',
            kicad_symbol='Device:R',
            kicad_footprint='Resistor_SMD:R_0603_1608Metric',
            confidence=0.9,
            field_mappings={'Description': 'A 10k resistor'}
        )
        
        category_id = generator._categorize_component(resistor_mapping, category_ids)
        assert category_id == category_ids['Resistors']
        
        # Test capacitor categorization
        capacitor_mapping = ComponentMapping(
            altium_symbol='Capacitor',
            altium_footprint='0805',
            kicad_symbol='Device:C',
            kicad_footprint='Capacitor_SMD:C_0805_2012Metric',
            confidence=0.9,
            field_mappings={'Description': 'A 100nF capacitor'}
        )
        
        category_id = generator._categorize_component(capacitor_mapping, category_ids)
        assert category_id == category_ids['Capacitors']
        
        # Test diode categorization
        diode_mapping = ComponentMapping(
            altium_symbol='Diode',
            altium_footprint='SOD-123',
            kicad_symbol='Device:D',
            kicad_footprint='Diode_SMD:D_SOD-123',
            confidence=0.9,
            field_mappings={'Description': 'A diode'}
        )
        
        category_id = generator._categorize_component(diode_mapping, category_ids)
        assert category_id == category_ids['Diodes']
        
        # Test unknown component categorization
        unknown_mapping = ComponentMapping(
            altium_symbol='Unknown',
            altium_footprint='Unknown',
            kicad_symbol='Device:R',
            kicad_footprint='Resistor_SMD:R_0603_1608Metric',
            confidence=0.5,
            field_mappings={'Description': 'Unknown component'}
        )
        
        category_id = generator._categorize_component(unknown_mapping, category_ids)
        assert category_id == category_ids['Uncategorized']
    
    def test_populate_components(self, temp_dir):
        """Test populating components table."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Create database and tables
        generator.create_database_schema()
        
        # Populate categories
        component_mappings = {
            'Resistors': [
                ComponentMapping(
                    altium_symbol='Resistor',
                    altium_footprint='0603',
                    kicad_symbol='Device:R',
                    kicad_footprint='Resistor_SMD:R_0603_1608Metric',
                    confidence=0.9,
                    field_mappings={
                        'Reference': 'R',
                        'Value': '10k',
                        'Description': 'A 10k resistor',
                        'Manufacturer': 'Generic',
                        'MPN': 'R-10K-0603',
                        'Package': '0603',
                        'Tolerance': '1%',
                        'Power': '0.1W'
                    }
                ),
                ComponentMapping(
                    altium_symbol='Resistor',
                    altium_footprint='0805',
                    kicad_symbol='Device:R',
                    kicad_footprint='Resistor_SMD:R_0805_2012Metric',
                    confidence=0.9,
                    field_mappings={
                        'Reference': 'R',
                        'Value': '1k',
                        'Description': 'A 1k resistor',
                        'Manufacturer': 'Generic',
                        'MPN': 'R-1K-0805',
                        'Package': '0805',
                        'Tolerance': '5%',
                        'Power': '0.125W'
                    }
                )
            ],
            'Capacitors': [
                ComponentMapping(
                    altium_symbol='Capacitor',
                    altium_footprint='0603',
                    kicad_symbol='Device:C',
                    kicad_footprint='Capacitor_SMD:C_0603_1608Metric',
                    confidence=0.9,
                    field_mappings={
                        'Reference': 'C',
                        'Value': '100nF',
                        'Description': 'A 100nF capacitor',
                        'Manufacturer': 'Generic',
                        'MPN': 'C-100N-0603',
                        'Package': '0603',
                        'Voltage': '50V',
                        'Tolerance': '10%'
                    }
                )
            ]
        }
        
        category_ids = generator.populate_categories(component_mappings)
        
        # Populate components
        generator.populate_components(component_mappings, category_ids)
        
        # Check database content
        conn = sqlite3.connect(generator.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM components")
        count = cursor.fetchone()[0]
        assert count == 3
        
        # Check resistor data
        cursor.execute("""
            SELECT symbol, footprint, value, description, manufacturer, mpn, package, tolerance, power
            FROM components
            WHERE symbol = 'Device:R' AND value = '10k'
        """)
        resistor = cursor.fetchone()
        assert resistor is not None
        assert resistor[0] == 'Device:R'
        assert resistor[1] == 'Resistor_SMD:R_0603_1608Metric'
        assert resistor[2] == '10k'
        assert resistor[3] == 'A 10k resistor'
        assert resistor[4] == 'Generic'
        assert resistor[5] == 'R-10K-0603'
        assert resistor[6] == '0603'
        assert resistor[7] == '1%'
        assert resistor[8] == '0.1W'
        
        # Check capacitor data
        cursor.execute("""
            SELECT symbol, footprint, value, description, manufacturer, mpn, package, voltage, tolerance
            FROM components
            WHERE symbol = 'Device:C' AND value = '100nF'
        """)
        capacitor = cursor.fetchone()
        assert capacitor is not None
        assert capacitor[0] == 'Device:C'
        assert capacitor[1] == 'Capacitor_SMD:C_0603_1608Metric'
        assert capacitor[2] == '100nF'
        assert capacitor[3] == 'A 100nF capacitor'
        assert capacitor[4] == 'Generic'
        assert capacitor[5] == 'C-100N-0603'
        assert capacitor[6] == '0603'
        assert capacitor[7] == '50V'
        assert capacitor[8] == '10%'
        
        conn.close()
    
    def test_generate_keywords(self, temp_dir):
        """Test generating keywords for components."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Test with resistor
        resistor_mapping = ComponentMapping(
            altium_symbol='Resistor',
            altium_footprint='0603',
            kicad_symbol='Device:R',
            kicad_footprint='Resistor_SMD:R_0603_1608Metric',
            confidence=0.9,
            field_mappings={
                'Description': 'A 10k Ohm 1% Resistor',
                'Manufacturer': 'Generic',
                'Package': '0603'
            }
        )
        
        keywords = generator._generate_keywords(resistor_mapping)
        assert 'resistor' in keywords.lower()
        assert 'ohm' in keywords.lower()
        assert 'generic' in keywords.lower()
        assert '0603' in keywords.lower()
        
        # Test with capacitor
        capacitor_mapping = ComponentMapping(
            altium_symbol='Capacitor',
            altium_footprint='0805',
            kicad_symbol='Device:C',
            kicad_footprint='Capacitor_SMD:C_0805_2012Metric',
            confidence=0.9,
            field_mappings={
                'Description': 'A 100nF 50V Ceramic Capacitor',
                'Manufacturer': 'Generic',
                'Package': '0805'
            }
        )
        
        keywords = generator._generate_keywords(capacitor_mapping)
        assert 'capacitor' in keywords.lower()
        assert 'ceramic' in keywords.lower()
        assert 'generic' in keywords.lower()
        assert '0805' in keywords.lower()
    
    def test_generate_kicad_dblib_file(self, temp_dir):
        """Test generating KiCAD .kicad_dbl configuration file."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Create database and tables
        generator.create_database_schema()
        
        # Generate KiCAD dblib file
        component_mappings = {'Resistors': [], 'Capacitors': []}
        generator.generate_kicad_dblib_file(component_mappings)
        
        # Check that the file was created
        assert os.path.exists(generator.dblib_path)
        
        # Check file content
        with open(generator.dblib_path, 'r') as f:
            config = json.load(f)
        
        assert 'meta' in config
        assert 'name' in config
        assert 'description' in config
        assert 'source' in config
        assert 'libraries' in config
        
        # Check source configuration
        assert config['source']['type'] == 'odbc'
        assert 'Driver=SQLite3;Database=' in config['source']['connection_string']
        
        # Check library definitions
        assert len(config['libraries']) > 0
        
        # Check All Components library
        all_components = next((lib for lib in config['libraries'] if lib['name'] == 'All Components'), None)
        assert all_components is not None
        assert all_components['table'] == 'components'
        assert all_components['key'] == 'id'
        assert all_components['symbols'] == 'symbol'
        assert all_components['footprints'] == 'footprint'
        assert 'fields' in all_components
        
        # Check Resistors library
        resistors = next((lib for lib in config['libraries'] if lib['name'] == 'Resistors'), None)
        assert resistors is not None
        assert resistors['table'] == 'resistors'
        assert 'fields' in resistors
    
    def test_get_standard_field_definitions(self, temp_dir):
        """Test getting standard field definitions."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        fields = generator._get_standard_field_definitions()
        
        # Check that common fields are defined
        field_names = [field['name'] for field in fields]
        assert 'Reference' in field_names
        assert 'Value' in field_names
        assert 'Description' in field_names
        assert 'Manufacturer' in field_names
        assert 'MPN' in field_names
        assert 'Package' in field_names
        assert 'Datasheet' in field_names
        
        # Check field properties
        reference_field = next((field for field in fields if field['name'] == 'Reference'), None)
        assert reference_field is not None
        assert reference_field['column'] == 'reference'
        assert reference_field['visible_on_add'] is True
        assert reference_field['visible_in_chooser'] is True
        assert reference_field['show_name'] is False
    
    def test_get_component_specific_field_definitions(self, temp_dir):
        """Test getting component-specific field definitions."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Test resistor fields
        resistor_fields = generator._get_resistor_field_definitions()
        
        # Check that standard fields are included
        standard_field_names = [field['name'] for field in generator._get_standard_field_definitions()]
        resistor_field_names = [field['name'] for field in resistor_fields]
        
        for name in standard_field_names:
            assert name in resistor_field_names
        
        # Check that resistor-specific fields are included
        assert 'Tolerance' in resistor_field_names
        assert 'Power' in resistor_field_names
        assert 'Temperature' in resistor_field_names
        
        # Test capacitor fields
        capacitor_fields = generator._get_capacitor_field_definitions()
        capacitor_field_names = [field['name'] for field in capacitor_fields]
        
        # Check that capacitor-specific fields are included
        assert 'Voltage' in capacitor_field_names
        assert 'Tolerance' in capacitor_field_names
        assert 'Temperature' in capacitor_field_names
    
    def test_generate_migration_report(self, temp_dir):
        """Test generating migration report."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Create component mappings with different confidence levels
        component_mappings = {
            'Resistors': [
                ComponentMapping(
                    altium_symbol='Resistor',
                    altium_footprint='0603',
                    kicad_symbol='Device:R',
                    kicad_footprint='Resistor_SMD:R_0603_1608Metric',
                    confidence=0.9,
                    field_mappings={'Description': 'A 10k resistor'}
                ),
                ComponentMapping(
                    altium_symbol='Resistor',
                    altium_footprint='0805',
                    kicad_symbol='Device:R',
                    kicad_footprint='Resistor_SMD:R_0805_2012Metric',
                    confidence=0.7,
                    field_mappings={'Description': 'A 1k resistor'}
                ),
                ComponentMapping(
                    altium_symbol='Resistor',
                    altium_footprint='Unknown',
                    kicad_symbol='Device:R',
                    kicad_footprint='Resistor_SMD:R_*',
                    confidence=0.4,
                    field_mappings={'Description': 'An unknown resistor'}
                )
            ],
            'Capacitors': [
                ComponentMapping(
                    altium_symbol='Capacitor',
                    altium_footprint='0603',
                    kicad_symbol='Device:C',
                    kicad_footprint='Capacitor_SMD:C_0603_1608Metric',
                    confidence=0.9,
                    field_mappings={'Description': 'A 100nF capacitor'}
                ),
                ComponentMapping(
                    altium_symbol='Unknown',
                    altium_footprint='0805',
                    kicad_symbol='Device:C',
                    kicad_footprint='Capacitor_SMD:C_0805_2012Metric',
                    confidence=0.6,
                    field_mappings={'Description': 'A 1uF capacitor'}
                )
            ]
        }
        
        # Generate report
        generator.generate_migration_report(component_mappings)
        
        # Check that the report file was created
        report_path = generator.output_dir / "migration_report.json"
        assert os.path.exists(report_path)
        
        # Check report content
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert 'migration_summary' in report
        assert 'table_details' in report
        assert 'issues' in report
        assert 'recommendations' in report
        
        # Check summary statistics
        summary = report['migration_summary']
        assert summary['total_tables'] == 2
        assert summary['total_components'] == 5
        assert summary['high_confidence'] == 2
        assert summary['medium_confidence'] == 2
        assert summary['low_confidence'] == 1
        
        # Check table details
        assert 'Resistors' in report['table_details']
        assert 'Capacitors' in report['table_details']
        
        resistors = report['table_details']['Resistors']
        assert resistors['component_count'] == 3
        assert resistors['high_confidence'] == 1
        assert resistors['medium_confidence'] == 1
        assert resistors['low_confidence'] == 1
        assert len(resistors['missing_footprints']) == 1
        
        # Check recommendations
        assert len(report['recommendations']) > 0
        assert any('low-confidence' in rec.lower() for rec in report['recommendations'])
        assert any('footprints' in rec.lower() for rec in report['recommendations'])
    
    def test_generate(self, temp_dir):
        """Test the complete generation process."""
        generator = KiCADDbLibGenerator(temp_dir)
        
        # Create component mappings
        component_mappings = {
            'Resistors': [
                ComponentMapping(
                    altium_symbol='Resistor',
                    altium_footprint='0603',
                    kicad_symbol='Device:R',
                    kicad_footprint='Resistor_SMD:R_0603_1608Metric',
                    confidence=0.9,
                    field_mappings={
                        'Reference': 'R',
                        'Value': '10k',
                        'Description': 'A 10k resistor',
                        'Manufacturer': 'Generic',
                        'MPN': 'R-10K-0603',
                        'Package': '0603',
                        'Tolerance': '1%',
                        'Power': '0.1W'
                    }
                )
            ],
            'Capacitors': [
                ComponentMapping(
                    altium_symbol='Capacitor',
                    altium_footprint='0603',
                    kicad_symbol='Device:C',
                    kicad_footprint='Capacitor_SMD:C_0603_1608Metric',
                    confidence=0.9,
                    field_mappings={
                        'Reference': 'C',
                        'Value': '100nF',
                        'Description': 'A 100nF capacitor',
                        'Manufacturer': 'Generic',
                        'MPN': 'C-100N-0603',
                        'Package': '0603',
                        'Voltage': '50V',
                        'Tolerance': '10%'
                    }
                )
            ]
        }
        
        # Run the generation process
        result = generator.generate(component_mappings)
        
        # Check the result
        assert 'database_path' in result
        assert 'dblib_path' in result
        assert 'output_directory' in result
        
        assert os.path.exists(result['database_path'])
        assert os.path.exists(result['dblib_path'])
        
        # Check that the report was generated
        report_path = generator.output_dir / "migration_report.json"
        assert os.path.exists(report_path)
        
        # Check database content
        conn = sqlite3.connect(result['database_path'])
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM components")
        count = cursor.fetchone()[0]
        assert count == 2
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        assert count > 0
        
        conn.close()