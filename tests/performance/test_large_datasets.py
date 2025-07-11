"""
Performance tests for large datasets.

These tests measure the performance of the migration tool when processing
large amounts of data.
"""

import os
import time
import pytest
import sqlite3
from pathlib import Path

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.mapping_engine import ComponentMappingEngine
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager


class TestLargeDatasets:
    """Performance tests for large datasets."""

    @pytest.fixture
    def large_dataset_fixture(self, migration_test_framework, temp_dir):
        """Create a large dataset for testing."""
        # Create a large database with multiple tables and many components
        db_path = os.path.join(temp_dir, "large_test.db")
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Create tables
        tables = {
            'Resistors': [
                'id INTEGER PRIMARY KEY',
                'LibReference TEXT',
                'Footprint TEXT',
                'Value TEXT',
                'Description TEXT',
                'Manufacturer TEXT',
                'Package TEXT',
                'Tolerance TEXT',
                'Power TEXT'
            ],
            'Capacitors': [
                'id INTEGER PRIMARY KEY',
                'LibReference TEXT',
                'Footprint TEXT',
                'Value TEXT',
                'Description TEXT',
                'Manufacturer TEXT',
                'Package TEXT',
                'Voltage TEXT',
                'Tolerance TEXT'
            ],
            'Diodes': [
                'id INTEGER PRIMARY KEY',
                'LibReference TEXT',
                'Footprint TEXT',
                'Value TEXT',
                'Description TEXT',
                'Manufacturer TEXT',
                'Package TEXT',
                'Voltage TEXT',
                'Current TEXT'
            ],
            'Transistors': [
                'id INTEGER PRIMARY KEY',
                'LibReference TEXT',
                'Footprint TEXT',
                'Value TEXT',
                'Description TEXT',
                'Manufacturer TEXT',
                'Package TEXT',
                'Type TEXT',
                'Voltage TEXT',
                'Current TEXT'
            ],
            'ICs': [
                'id INTEGER PRIMARY KEY',
                'LibReference TEXT',
                'Footprint TEXT',
                'Value TEXT',
                'Description TEXT',
                'Manufacturer TEXT',
                'Package TEXT',
                'Function TEXT',
                'Pins TEXT'
            ]
        }
        
        # Create tables
        for table_name, columns in tables.items():
            cursor.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")
        
        # Insert data
        component_counts = {
            'Resistors': 5000,
            'Capacitors': 3000,
            'Diodes': 1000,
            'Transistors': 800,
            'ICs': 1200
        }
        
        for table_name, count in component_counts.items():
            # Generate insert statements
            if table_name == 'Resistors':
                for i in range(count):
                    value = f"{i % 100}k"
                    cursor.execute(
                        f"INSERT INTO {table_name} (LibReference, Footprint, Value, Description, Manufacturer, Package, Tolerance, Power) "
                        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            f"RES{i}",
                            f"RESC{i % 10 + 1}06",
                            value,
                            f"{value} Resistor",
                            f"Manufacturer {i % 10}",
                            f"{i % 10 + 1}06",
                            f"{i % 5 + 1}%",
                            f"{(i % 5 + 1) / 10}W"
                        )
                    )
            elif table_name == 'Capacitors':
                for i in range(count):
                    value = f"{i % 100}nF"
                    cursor.execute(
                        f"INSERT INTO {table_name} (LibReference, Footprint, Value, Description, Manufacturer, Package, Voltage, Tolerance) "
                        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            f"CAP{i}",
                            f"CAPC{i % 10 + 1}06",
                            value,
                            f"{value} Capacitor",
                            f"Manufacturer {i % 10}",
                            f"{i % 10 + 1}06",
                            f"{(i % 10 + 1) * 10}V",
                            f"{i % 5 + 1}%"
                        )
                    )
            elif table_name == 'Diodes':
                for i in range(count):
                    cursor.execute(
                        f"INSERT INTO {table_name} (LibReference, Footprint, Value, Description, Manufacturer, Package, Voltage, Current) "
                        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            f"D{i}",
                            f"SOD{i % 5 + 1}23",
                            f"1N{4000 + i % 1000}",
                            f"Diode 1N{4000 + i % 1000}",
                            f"Manufacturer {i % 10}",
                            f"SOD{i % 5 + 1}23",
                            f"{(i % 10 + 1) * 10}V",
                            f"{(i % 10 + 1) * 100}mA"
                        )
                    )
            elif table_name == 'Transistors':
                for i in range(count):
                    cursor.execute(
                        f"INSERT INTO {table_name} (LibReference, Footprint, Value, Description, Manufacturer, Package, Type, Voltage, Current) "
                        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            f"Q{i}",
                            f"SOT{i % 5 + 1}23",
                            f"2N{3000 + i % 1000}",
                            f"Transistor 2N{3000 + i % 1000}",
                            f"Manufacturer {i % 10}",
                            f"SOT{i % 5 + 1}23",
                            "NPN" if i % 2 == 0 else "PNP",
                            f"{(i % 10 + 1) * 10}V",
                            f"{(i % 10 + 1) * 100}mA"
                        )
                    )
            elif table_name == 'ICs':
                for i in range(count):
                    cursor.execute(
                        f"INSERT INTO {table_name} (LibReference, Footprint, Value, Description, Manufacturer, Package, Function, Pins) "
                        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            f"IC{i}",
                            f"SOIC{i % 5 + 1}",
                            f"LM{3000 + i % 1000}",
                            f"IC LM{3000 + i % 1000}",
                            f"Manufacturer {i % 10}",
                            f"SOIC{i % 5 + 1}",
                            f"Function {i % 10}",
                            f"{(i % 10 + 1) * 2}"
                        )
                    )
        
        connection.commit()
        
        # Create a DbLib file pointing to the database
        dblib_file = os.path.join(temp_dir, "large_test.DbLib")
        with open(dblib_file, 'w') as f:
            f.write("[OutputDatabaseLinkFile]\n")
            f.write(f"ConnectionString={db_path}\n")
            f.write("AddMode=3\n")
            f.write("RemoveMode=1\n")
            f.write("UpdateMode=2\n")
            f.write("ViewMode=1\n")
            f.write("LeftQuote=[\n")
            f.write("RightQuote=]\n")
            f.write("QuoteTableNames=1\n")
            f.write("UseTableSchemaName=0\n")
            f.write("DefaultColumnType=VARCHAR(255)\n")
            f.write("LibraryDatabaseType=Microsoft Access\n")
            f.write("LibraryDatabasePath=\n")
            f.write("DatabasePathRelative=0\n")
            f.write("TopPanelCollapsed=0\n")
            f.write("LibrarySearchPath=\n")
            f.write("OrcadMultiValueDelimiter=,\n")
            f.write("SearchSubDirectories=0\n")
            f.write("SchemaName=\n")
            f.write("LastFocusedTable=Resistors\n")
            
            # Add table definitions
            for table_name in tables.keys():
                f.write(f"\n[{table_name}]\n")
                f.write(f"SchemaName=\n")
                f.write(f"TableName={table_name}\n")
                f.write(f"Enabled=True\n")
                f.write(f"UserWhere=\n")
                f.write(f"UserWhereParams=\n")
                f.write(f"BrowserOrder_Sorting=\n")
                f.write(f"BrowserOrder_Grouping=\n")
                f.write(f"BrowserOrder_Visible=\n")
                f.write(f"ComponentIdColumn=id\n")
                f.write(f"LibraryRefColumn=LibReference\n")
                f.write(f"FootprintColumn=Footprint\n")
        
        # Set up output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        return {
            'dblib_file': dblib_file,
            'db_path': db_path,
            'output_dir': output_dir,
            'total_components': sum(component_counts.values())
        }
    
    def test_large_dataset_parsing_performance(self, large_dataset_fixture):
        """Test the performance of parsing a large dataset."""
        dblib_file = large_dataset_fixture['dblib_file']
        
        # Measure parsing time
        start_time = time.time()
        
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        
        parsing_time = time.time() - start_time
        
        # Log performance metrics
        print(f"\nPerformance - DbLib parsing time: {parsing_time:.2f} seconds")
        
        # Verify that the parsing was successful
        assert altium_config is not None
        assert 'connection_string' in altium_config
        assert 'tables' in altium_config
        assert len(altium_config['tables']) == 5  # 5 tables
        
        # Assert that parsing time is reasonable (adjust threshold as needed)
        assert parsing_time < 5.0, f"DbLib parsing took too long: {parsing_time:.2f} seconds"
    
    def test_large_dataset_extraction_performance(self, large_dataset_fixture):
        """Test the performance of extracting data from a large dataset."""
        dblib_file = large_dataset_fixture['dblib_file']
        total_components = large_dataset_fixture['total_components']
        
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        
        # Measure extraction time
        start_time = time.time()
        
        altium_data = parser.extract_all_data(altium_config)
        
        extraction_time = time.time() - start_time
        
        # Log performance metrics
        print(f"\nPerformance - Data extraction time: {extraction_time:.2f} seconds")
        print(f"Performance - Components per second: {total_components / extraction_time:.2f}")
        
        # Verify that the extraction was successful
        assert altium_data is not None
        assert len(altium_data) == 5  # 5 tables
        
        # Count the total number of components extracted
        extracted_components = sum(len(table_data.get('data', [])) for table_data in altium_data.values())
        assert extracted_components == total_components
        
        # Assert that extraction time is reasonable (adjust threshold as needed)
        # This is a rough estimate and should be adjusted based on actual performance
        assert extraction_time < 60.0, f"Data extraction took too long: {extraction_time:.2f} seconds"
    
    def test_large_dataset_mapping_performance(self, large_dataset_fixture):
        """Test the performance of mapping a large dataset."""
        dblib_file = large_dataset_fixture['dblib_file']
        total_components = large_dataset_fixture['total_components']
        
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        altium_data = parser.extract_all_data(altium_config)
        
        # Measure mapping time
        start_time = time.time()
        
        mapper = ComponentMappingEngine()
        all_mappings = {}
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
        
        mapping_time = time.time() - start_time
        
        # Log performance metrics
        print(f"\nPerformance - Component mapping time: {mapping_time:.2f} seconds")
        print(f"Performance - Components mapped per second: {total_components / mapping_time:.2f}")
        
        # Verify that the mapping was successful
        assert all_mappings is not None
        assert len(all_mappings) == 5  # 5 tables
        
        # Count the total number of components mapped
        mapped_components = sum(len(mappings) for mappings in all_mappings.values())
        assert mapped_components == total_components
        
        # Assert that mapping time is reasonable (adjust threshold as needed)
        # This is a rough estimate and should be adjusted based on actual performance
        assert mapping_time < 120.0, f"Component mapping took too long: {mapping_time:.2f} seconds"
    
    def test_large_dataset_database_generation_performance(self, large_dataset_fixture):
        """Test the performance of generating a database for a large dataset."""
        dblib_file = large_dataset_fixture['dblib_file']
        output_dir = large_dataset_fixture['output_dir']
        total_components = large_dataset_fixture['total_components']
        
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        altium_data = parser.extract_all_data(altium_config)
        
        mapper = ComponentMappingEngine()
        all_mappings = {}
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
        
        # Measure database generation time
        start_time = time.time()
        
        generator = KiCADDbLibGenerator(output_dir)
        result = generator.generate(all_mappings)
        
        generation_time = time.time() - start_time
        
        # Log performance metrics
        print(f"\nPerformance - Database generation time: {generation_time:.2f} seconds")
        print(f"Performance - Components processed per second: {total_components / generation_time:.2f}")
        
        # Verify that the database was generated
        assert os.path.exists(result['database_path'])
        assert os.path.exists(result['dblib_path'])
        
        # Verify database content
        conn = sqlite3.connect(result['database_path'])
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM components")
        component_count = cursor.fetchone()[0]
        assert component_count == total_components
        
        conn.close()
        
        # Assert that generation time is reasonable (adjust threshold as needed)
        # This is a rough estimate and should be adjusted based on actual performance
        assert generation_time < 180.0, f"Database generation took too long: {generation_time:.2f} seconds"
    
    def test_large_dataset_end_to_end_performance(self, large_dataset_fixture):
        """Test the end-to-end performance of processing a large dataset."""
        dblib_file = large_dataset_fixture['dblib_file']
        output_dir = large_dataset_fixture['output_dir']
        total_components = large_dataset_fixture['total_components']
        
        # Measure total processing time
        start_time = time.time()
        
        # Step 1: Parse DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        
        # Step 2: Extract data
        altium_data = parser.extract_all_data(altium_config)
        
        # Step 3: Map components
        mapper = ComponentMappingEngine()
        all_mappings = {}
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
        
        # Step 4: Generate KiCAD database
        generator = KiCADDbLibGenerator(output_dir)
        result = generator.generate(all_mappings)
        
        total_time = time.time() - start_time
        
        # Log performance metrics
        print(f"\nPerformance - Total processing time: {total_time:.2f} seconds")
        print(f"Performance - Overall components per second: {total_components / total_time:.2f}")
        
        # Verify that the process was successful
        assert os.path.exists(result['database_path'])
        assert os.path.exists(result['dblib_path'])
        
        # Assert that total processing time is reasonable (adjust threshold as needed)
        # This is a rough estimate and should be adjusted based on actual performance
        assert total_time < 360.0, f"Total processing took too long: {total_time:.2f} seconds"