"""
Pytest configuration and fixtures for the Altium to KiCAD migration tool tests.
"""

import os
import sys
import pytest
import tempfile
import sqlite3
import configparser
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.mapping_engine import ComponentMappingEngine
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager
from migration_tool.utils.database_utils import DatabaseUtils
from migration_tool.utils.logging_utils import setup_logging


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_dblib_file(temp_dir):
    """Create a sample Altium DbLib file for testing."""
    dblib_path = os.path.join(temp_dir, "test.DbLib")
    
    # Create a simple DbLib file
    config = configparser.ConfigParser()
    
    config['DatabaseLinks'] = {
        'ConnectionString': f'Driver=SQLite3;Database={os.path.join(temp_dir, "test.db")};',
        'AddMode': '3',
        'RemoveMode': '1',
        'UpdateMode': '2'
    }
    
    config['Table1'] = {
        'SchemaName': '',
        'TableName': 'Resistors',
        'Enabled': 'True',
        'Key': 'Part Number',
        'Symbols': 'Symbol',
        'Footprints': 'Footprint',
        'Description': 'Description'
    }
    
    config['Table2'] = {
        'SchemaName': '',
        'TableName': 'Capacitors',
        'Enabled': 'True',
        'Key': 'Part Number',
        'Symbols': 'Symbol',
        'Footprints': 'Footprint',
        'Description': 'Description'
    }
    
    with open(dblib_path, 'w') as f:
        config.write(f)
    
    # Create the SQLite database
    _create_test_database(os.path.join(temp_dir, "test.db"))
    
    return dblib_path


def _create_test_database(db_path: str):
    """Create a test SQLite database with sample data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Resistors table
    cursor.execute("""
        CREATE TABLE Resistors (
            [Part Number] TEXT PRIMARY KEY,
            Symbol TEXT,
            Footprint TEXT,
            Description TEXT,
            Value TEXT,
            Manufacturer TEXT,
            [Manufacturer Part Number] TEXT,
            Package TEXT,
            Tolerance TEXT,
            Power TEXT,
            Datasheet TEXT
        )
    """)
    
    # Insert test resistors
    resistors_data = [
        ('R-0603-10K', 'Resistor', '0603', '10k Ohm Resistor', '10k', 'Generic', 'R-10K-0603', '0603', '1%', '0.1W', 'http://example.com/resistor.pdf'),
        ('R-0805-1K', 'Resistor', '0805', '1k Ohm Resistor', '1k', 'Generic', 'R-1K-0805', '0805', '5%', '0.125W', 'http://example.com/resistor.pdf'),
        ('R-1206-100R', 'Resistor', '1206', '100 Ohm Resistor', '100R', 'Generic', 'R-100R-1206', '1206', '1%', '0.25W', 'http://example.com/resistor.pdf')
    ]
    
    cursor.executemany("""
        INSERT INTO Resistors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, resistors_data)
    
    # Create Capacitors table
    cursor.execute("""
        CREATE TABLE Capacitors (
            [Part Number] TEXT PRIMARY KEY,
            Symbol TEXT,
            Footprint TEXT,
            Description TEXT,
            Value TEXT,
            Manufacturer TEXT,
            [Manufacturer Part Number] TEXT,
            Package TEXT,
            Voltage TEXT,
            Tolerance TEXT,
            Datasheet TEXT
        )
    """)
    
    # Insert test capacitors
    capacitors_data = [
        ('C-0603-100N', 'Capacitor', '0603', '100nF Ceramic Capacitor', '100nF', 'Generic', 'C-100N-0603', '0603', '50V', '10%', 'http://example.com/capacitor.pdf'),
        ('C-0805-1U', 'Capacitor', '0805', '1uF Ceramic Capacitor', '1uF', 'Generic', 'C-1U-0805', '0805', '25V', '20%', 'http://example.com/capacitor.pdf'),
        ('C-1206-10U', 'Capacitor', '1206', '10uF Ceramic Capacitor', '10uF', 'Generic', 'C-10U-1206', '1206', '16V', '20%', 'http://example.com/capacitor.pdf')
    ]
    
    cursor.executemany("""
        INSERT INTO Capacitors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, capacitors_data)
    
    conn.commit()
    conn.close()


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration for testing."""
    config = {
        'altium_dblib_path': os.path.join(temp_dir, "test.DbLib"),
        'output_directory': os.path.join(temp_dir, "output"),
        'database_name': "components.db",
        'dblib_name': "components.kicad_dbl",
        'enable_parallel_processing': False,
        'max_worker_threads': 1,
        'batch_size': 100,
        'enable_caching': False,
        'fuzzy_threshold': 0.7,
        'confidence_threshold': 0.5,
        'validate_symbols': False,
        'validate_footprints': False,
        'create_views': True,
        'vacuum_database': True,
        'log_level': "INFO"
    }
    
    # Create the output directory
    os.makedirs(os.path.join(temp_dir, "output"), exist_ok=True)
    
    return config


@pytest.fixture
def altium_parser(sample_dblib_file):
    """Create an AltiumDbLibParser instance for testing."""
    parser = AltiumDbLibParser()
    return parser


@pytest.fixture
def mapping_engine():
    """Create a ComponentMappingEngine instance for testing."""
    mapper = ComponentMappingEngine()
    return mapper


@pytest.fixture
def kicad_generator(temp_dir):
    """Create a KiCADDbLibGenerator instance for testing."""
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    generator = KiCADDbLibGenerator(output_dir)
    return generator


@pytest.fixture
def sample_component_data():
    """Create sample component data for testing."""
    return {
        'Part Number': 'R-0603-10K',
        'Symbol': 'Resistor',
        'Footprint': '0603',
        'Description': '10k Ohm Resistor',
        'Value': '10k',
        'Manufacturer': 'Generic',
        'Manufacturer Part Number': 'R-10K-0603',
        'Package': '0603',
        'Tolerance': '1%',
        'Power': '0.1W',
        'Datasheet': 'http://example.com/resistor.pdf'
    }


@pytest.fixture
def sample_table_config():
    """Create sample table configuration for testing."""
    return {
        'enabled': True,
        'key_field': 'Part Number',
        'symbol_field': 'Symbol',
        'footprint_field': 'Footprint',
        'description_field': 'Description',
        'user_where': '',
        'custom_fields': ['Value', 'Manufacturer', 'Manufacturer Part Number', 'Package', 'Tolerance', 'Power', 'Datasheet']
    }


@pytest.fixture
def sample_altium_data():
    """Create sample Altium data for testing."""
    return {
        'Resistors': {
            'config': {
                'enabled': True,
                'key_field': 'Part Number',
                'symbol_field': 'Symbol',
                'footprint_field': 'Footprint',
                'description_field': 'Description',
                'user_where': '',
                'custom_fields': ['Value', 'Manufacturer', 'Manufacturer Part Number', 'Package', 'Tolerance', 'Power', 'Datasheet']
            },
            'data': [
                {
                    'Part Number': 'R-0603-10K',
                    'Symbol': 'Resistor',
                    'Footprint': '0603',
                    'Description': '10k Ohm Resistor',
                    'Value': '10k',
                    'Manufacturer': 'Generic',
                    'Manufacturer Part Number': 'R-10K-0603',
                    'Package': '0603',
                    'Tolerance': '1%',
                    'Power': '0.1W',
                    'Datasheet': 'http://example.com/resistor.pdf'
                },
                {
                    'Part Number': 'R-0805-1K',
                    'Symbol': 'Resistor',
                    'Footprint': '0805',
                    'Description': '1k Ohm Resistor',
                    'Value': '1k',
                    'Manufacturer': 'Generic',
                    'Manufacturer Part Number': 'R-1K-0805',
                    'Package': '0805',
                    'Tolerance': '5%',
                    'Power': '0.125W',
                    'Datasheet': 'http://example.com/resistor.pdf'
                }
            ]
        },
        'Capacitors': {
            'config': {
                'enabled': True,
                'key_field': 'Part Number',
                'symbol_field': 'Symbol',
                'footprint_field': 'Footprint',
                'description_field': 'Description',
                'user_where': '',
                'custom_fields': ['Value', 'Manufacturer', 'Manufacturer Part Number', 'Package', 'Voltage', 'Tolerance', 'Datasheet']
            },
            'data': [
                {
                    'Part Number': 'C-0603-100N',
                    'Symbol': 'Capacitor',
                    'Footprint': '0603',
                    'Description': '100nF Ceramic Capacitor',
                    'Value': '100nF',
                    'Manufacturer': 'Generic',
                    'Manufacturer Part Number': 'C-100N-0603',
                    'Package': '0603',
                    'Voltage': '50V',
                    'Tolerance': '10%',
                    'Datasheet': 'http://example.com/capacitor.pdf'
                },
                {
                    'Part Number': 'C-0805-1U',
                    'Symbol': 'Capacitor',
                    'Footprint': '0805',
                    'Description': '1uF Ceramic Capacitor',
                    'Value': '1uF',
                    'Manufacturer': 'Generic',
                    'Manufacturer Part Number': 'C-1U-0805',
                    'Package': '0805',
                    'Voltage': '25V',
                    'Tolerance': '20%',
                    'Datasheet': 'http://example.com/capacitor.pdf'
                }
            ]
        }
    }


class MigrationTestFramework:
    """Framework for testing and validating migrations."""
    
    def __init__(self, test_output_dir: str = None):
        self.test_output_dir = test_output_dir or tempfile.mkdtemp()
        self.test_results = {}
        
    def create_test_altium_dblib(self) -> str:
        """Create a test Altium .DbLib file for testing."""
        test_dblib_path = os.path.join(self.test_output_dir, "test.DbLib")
        
        # Create test SQLite database
        test_db_path = os.path.join(self.test_output_dir, "test.db")
        self._create_test_database(test_db_path)
        
        # Create DbLib configuration
        config = configparser.ConfigParser()
        
        config['DatabaseLinks'] = {
            'ConnectionString': f'Driver=SQLite3;Database={test_db_path};',
            'AddMode': '3',
            'RemoveMode': '1',
            'UpdateMode': '2'
        }
        
        config['Table1'] = {
            'SchemaName': '',
            'TableName': 'Resistors',
            'Enabled': 'True',
            'Key': 'Part Number',
            'Symbols': 'Symbol',
            'Footprints': 'Footprint',
            'Description': 'Description'
        }
        
        config['Table2'] = {
            'SchemaName': '',
            'TableName': 'Capacitors',
            'Enabled': 'True',
            'Key': 'Part Number',
            'Symbols': 'Symbol', 
            'Footprints': 'Footprint',
            'Description': 'Description'
        }
        
        with open(test_dblib_path, 'w') as f:
            config.write(f)
        
        return test_dblib_path
    
    def _create_test_database(self, db_path: str):
        """Create test SQLite database with sample data."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create resistors table
        cursor.execute("""
            CREATE TABLE Resistors (
                [Part Number] TEXT PRIMARY KEY,
                Symbol TEXT,
                Footprint TEXT,
                Description TEXT,
                Value TEXT,
                Manufacturer TEXT,
                [Manufacturer Part Number] TEXT,
                Package TEXT,
                Tolerance TEXT,
                Power TEXT,
                Datasheet TEXT
            )
        """)
        
        # Insert test resistors
        resistors_data = [
            ('R-0603-10K', 'Resistor', '0603', '10k Ohm Resistor', '10k', 'Generic', 'R-10K-0603', '0603', '1%', '0.1W', 'http://example.com/resistor.pdf'),
            ('R-0805-1K', 'Resistor', '0805', '1k Ohm Resistor', '1k', 'Generic', 'R-1K-0805', '0805', '5%', '0.125W', 'http://example.com/resistor.pdf'),
            ('R-1206-100R', 'Resistor', '1206', '100 Ohm Resistor', '100R', 'Generic', 'R-100R-1206', '1206', '1%', '0.25W', 'http://example.com/resistor.pdf')
        ]
        
        cursor.executemany("""
            INSERT INTO Resistors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, resistors_data)
        
        # Create capacitors table
        cursor.execute("""
            CREATE TABLE Capacitors (
                [Part Number] TEXT PRIMARY KEY,
                Symbol TEXT,
                Footprint TEXT,
                Description TEXT,
                Value TEXT,
                Manufacturer TEXT,
                [Manufacturer Part Number] TEXT,
                Package TEXT,
                Voltage TEXT,
                Tolerance TEXT,
                Datasheet TEXT
            )
        """)
        
        # Insert test capacitors
        capacitors_data = [
            ('C-0603-100N', 'Capacitor', '0603', '100nF Ceramic Capacitor', '100nF', 'Generic', 'C-100N-0603', '0603', '50V', '10%', 'http://example.com/capacitor.pdf'),
            ('C-0805-1U', 'Capacitor', '0805', '1uF Ceramic Capacitor', '1uF', 'Generic', 'C-1U-0805', '0805', '25V', '20%', 'http://example.com/capacitor.pdf'),
            ('C-1206-10U', 'Capacitor', '1206', '10uF Ceramic Capacitor', '10uF', 'Generic', 'C-10U-1206', '1206', '16V', '20%', 'http://example.com/capacitor.pdf')
        ]
        
        cursor.executemany("""
            INSERT INTO Capacitors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, capacitors_data)
        
        conn.commit()
        conn.close()
    
    def run_migration_test(self, altium_dblib_path: str, output_dir: str) -> Dict[str, Any]:
        """Run a migration test and return results."""
        from migration_tool.core.altium_parser import AltiumDbLibParser
        from migration_tool.core.mapping_engine import ComponentMappingEngine
        from migration_tool.core.kicad_generator import KiCADDbLibGenerator
        
        # Parse Altium DbLib
        parser = AltiumDbLibParser()
        config = parser.parse_dblib_file(altium_dblib_path)
        
        # Extract data
        altium_data = parser.extract_all_data(config)
        
        # Map components
        mapper = ComponentMappingEngine()
        all_mappings = {}
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
        
        # Generate KiCAD database
        generator = KiCADDbLibGenerator(output_dir)
        result = generator.generate(all_mappings)
        
        # Validate results
        validation_result = self.validate_migration(result['database_path'], altium_data)
        
        return {
            'migration_result': result,
            'validation_result': validation_result
        }
    
    def validate_migration(self, kicad_db_path: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate migration results."""
        conn = sqlite3.connect(kicad_db_path)
        cursor = conn.cursor()
        
        # Count components
        cursor.execute("SELECT COUNT(*) FROM components")
        migrated_count = cursor.fetchone()[0]
        
        # Count original components
        original_count = 0
        for table_name, table_data in original_data.items():
            if 'data' in table_data:
                original_count += len(table_data['data'])
        
        # Check for missing components
        missing_components = []
        
        for table_name, table_data in original_data.items():
            if 'data' not in table_data:
                continue
                
            for component in table_data['data']:
                part_number = component.get('Part Number', '')
                
                cursor.execute(
                    "SELECT COUNT(*) FROM components WHERE mpn = ?",
                    (component.get('Manufacturer Part Number', ''),)
                )
                
                if cursor.fetchone()[0] == 0:
                    missing_components.append({
                        'table': table_name,
                        'part_number': part_number
                    })
        
        # Check for data integrity
        data_integrity = {
            'original_count': original_count,
            'migrated_count': migrated_count,
            'missing_count': len(missing_components),
            'integrity_score': (original_count - len(missing_components)) / original_count if original_count > 0 else 0
        }
        
        conn.close()
        
        return {
            'data_integrity': data_integrity,
            'missing_components': missing_components
        }
    
    def generate_test_report(self, test_results: Dict[str, Any]) -> str:
        """Generate a test report."""
        report_path = os.path.join(self.test_output_dir, "test_report.json")
        
        with open(report_path, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        return report_path


@pytest.fixture
def migration_test_framework(temp_dir):
    """Create a MigrationTestFramework instance for testing."""
    return MigrationTestFramework(temp_dir)