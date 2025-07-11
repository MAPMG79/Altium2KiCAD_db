"""
Performance tests for parallel processing.

These tests measure the performance improvements gained by using parallel
processing for the migration tasks.
"""

import os
import time
import pytest
import sqlite3
import concurrent.futures
from pathlib import Path

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.mapping_engine import ComponentMappingEngine
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager


class TestParallelProcessing:
    """Performance tests for parallel processing."""

    @pytest.fixture
    def parallel_test_fixture(self, migration_test_framework, temp_dir):
        """Create a dataset for parallel processing testing."""
        # Create a database with multiple tables and many components
        db_path = os.path.join(temp_dir, "parallel_test.db")
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
            ]
        }
        
        # Create tables
        for table_name, columns in tables.items():
            cursor.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")
        
        # Insert data
        component_counts = {
            'Resistors': 1000,
            'Capacitors': 800,
            'Diodes': 500,
            'Transistors': 300
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
        
        connection.commit()
        
        # Create a DbLib file pointing to the database
        dblib_file = os.path.join(temp_dir, "parallel_test.DbLib")
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
        
        # Set up output directories
        output_dir_serial = os.path.join(temp_dir, "output_serial")
        output_dir_parallel = os.path.join(temp_dir, "output_parallel")
        os.makedirs(output_dir_serial, exist_ok=True)
        os.makedirs(output_dir_parallel, exist_ok=True)
        
        return {
            'dblib_file': dblib_file,
            'db_path': db_path,
            'output_dir_serial': output_dir_serial,
            'output_dir_parallel': output_dir_parallel,
            'total_components': sum(component_counts.values())
        }
    
    def test_parallel_vs_serial_data_extraction(self, parallel_test_fixture):
        """Test the performance of parallel vs. serial data extraction."""
        dblib_file = parallel_test_fixture['dblib_file']
        
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        
        # Serial extraction
        start_time_serial = time.time()
        
        altium_data_serial = parser.extract_all_data(altium_config)
        
        serial_time = time.time() - start_time_serial
        
        # Parallel extraction
        start_time_parallel = time.time()
        
        # Extract data from each table in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_table = {
                executor.submit(parser.extract_table_data, altium_config, table_name): table_name
                for table_name in altium_config['tables']
            }
            
            altium_data_parallel = {}
            for future in concurrent.futures.as_completed(future_to_table):
                table_name = future_to_table[future]
                try:
                    table_data = future.result()
                    altium_data_parallel[table_name] = table_data
                except Exception as e:
                    print(f"Error extracting data from table {table_name}: {e}")
        
        parallel_time = time.time() - start_time_parallel
        
        # Log performance metrics
        print(f"\nPerformance - Serial data extraction time: {serial_time:.2f} seconds")
        print(f"Performance - Parallel data extraction time: {parallel_time:.2f} seconds")
        print(f"Performance - Speedup factor: {serial_time / parallel_time:.2f}x")
        
        # Verify that both methods extracted the same data
        assert set(altium_data_serial.keys()) == set(altium_data_parallel.keys())
        
        for table_name in altium_data_serial.keys():
            assert len(altium_data_serial[table_name]['data']) == len(altium_data_parallel[table_name]['data'])
        
        # Assert that parallel processing is faster
        assert parallel_time < serial_time, "Parallel processing should be faster than serial processing"
    
    def test_parallel_vs_serial_component_mapping(self, parallel_test_fixture):
        """Test the performance of parallel vs. serial component mapping."""
        dblib_file = parallel_test_fixture['dblib_file']
        
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        altium_data = parser.extract_all_data(altium_config)
        
        # Serial mapping
        start_time_serial = time.time()
        
        mapper = ComponentMappingEngine()
        all_mappings_serial = {}
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings_serial[table_name] = mappings
        
        serial_time = time.time() - start_time_serial
        
        # Parallel mapping
        start_time_parallel = time.time()
        
        mapper = ComponentMappingEngine()
        all_mappings_parallel = {}
        
        # Map components from each table in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_table = {}
            
            for table_name, table_data in altium_data.items():
                if 'data' in table_data and table_data['data']:
                    future = executor.submit(mapper.map_table_data, table_name, table_data)
                    future_to_table[future] = table_name
            
            for future in concurrent.futures.as_completed(future_to_table):
                table_name = future_to_table[future]
                try:
                    mappings = future.result()
                    all_mappings_parallel[table_name] = mappings
                except Exception as e:
                    print(f"Error mapping components from table {table_name}: {e}")
        
        parallel_time = time.time() - start_time_parallel
        
        # Log performance metrics
        print(f"\nPerformance - Serial component mapping time: {serial_time:.2f} seconds")
        print(f"Performance - Parallel component mapping time: {parallel_time:.2f} seconds")
        print(f"Performance - Speedup factor: {serial_time / parallel_time:.2f}x")
        
        # Verify that both methods mapped the same number of components
        assert set(all_mappings_serial.keys()) == set(all_mappings_parallel.keys())
        
        for table_name in all_mappings_serial.keys():
            assert len(all_mappings_serial[table_name]) == len(all_mappings_parallel[table_name])
        
        # Assert that parallel processing is faster
        assert parallel_time < serial_time, "Parallel processing should be faster than serial processing"
    
    def test_parallel_vs_serial_database_generation(self, parallel_test_fixture):
        """Test the performance of parallel vs. serial database generation."""
        dblib_file = parallel_test_fixture['dblib_file']
        output_dir_serial = parallel_test_fixture['output_dir_serial']
        output_dir_parallel = parallel_test_fixture['output_dir_parallel']
        
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        altium_data = parser.extract_all_data(altium_config)
        
        mapper = ComponentMappingEngine()
        all_mappings = {}
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
        
        # Serial database generation
        start_time_serial = time.time()
        
        generator_serial = KiCADDbLibGenerator(output_dir_serial)
        result_serial = generator_serial.generate(all_mappings)
        
        serial_time = time.time() - start_time_serial
        
        # Parallel database generation
        start_time_parallel = time.time()
        
        generator_parallel = KiCADDbLibGenerator(output_dir_parallel)
        
        # Enable parallel processing
        generator_parallel.enable_parallel_processing = True
        generator_parallel.max_worker_threads = 4
        
        result_parallel = generator_parallel.generate(all_mappings)
        
        parallel_time = time.time() - start_time_parallel
        
        # Log performance metrics
        print(f"\nPerformance - Serial database generation time: {serial_time:.2f} seconds")
        print(f"Performance - Parallel database generation time: {parallel_time:.2f} seconds")
        print(f"Performance - Speedup factor: {serial_time / parallel_time:.2f}x")
        
        # Verify that both methods generated the same database
        conn_serial = sqlite3.connect(result_serial['database_path'])
        cursor_serial = conn_serial.cursor()
        
        conn_parallel = sqlite3.connect(result_parallel['database_path'])
        cursor_parallel = conn_parallel.cursor()
        
        # Check component counts
        cursor_serial.execute("SELECT COUNT(*) FROM components")
        serial_count = cursor_serial.fetchone()[0]
        
        cursor_parallel.execute("SELECT COUNT(*) FROM components")
        parallel_count = cursor_parallel.fetchone()[0]
        
        assert serial_count == parallel_count
        
        conn_serial.close()
        conn_parallel.close()
        
        # Assert that parallel processing is faster
        assert parallel_time < serial_time, "Parallel processing should be faster than serial processing"
    
    def test_parallel_vs_serial_end_to_end(self, parallel_test_fixture):
        """Test the end-to-end performance of parallel vs. serial processing."""
        dblib_file = parallel_test_fixture['dblib_file']
        output_dir_serial = parallel_test_fixture['output_dir_serial']
        output_dir_parallel = parallel_test_fixture['output_dir_parallel']
        
        # Serial processing
        start_time_serial = time.time()
        
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
        generator = KiCADDbLibGenerator(output_dir_serial)
        result_serial = generator.generate(all_mappings)
        
        serial_time = time.time() - start_time_serial
        
        # Parallel processing
        start_time_parallel = time.time()
        
        # Step 1: Parse DbLib file (same as serial)
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        
        # Step 2: Extract data in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_table = {
                executor.submit(parser.extract_table_data, altium_config, table_name): table_name
                for table_name in altium_config['tables']
            }
            
            altium_data = {}
            for future in concurrent.futures.as_completed(future_to_table):
                table_name = future_to_table[future]
                try:
                    table_data = future.result()
                    altium_data[table_name] = table_data
                except Exception as e:
                    print(f"Error extracting data from table {table_name}: {e}")
        
        # Step 3: Map components in parallel
        mapper = ComponentMappingEngine()
        all_mappings = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_table = {}
            
            for table_name, table_data in altium_data.items():
                if 'data' in table_data and table_data['data']:
                    future = executor.submit(mapper.map_table_data, table_name, table_data)
                    future_to_table[future] = table_name
            
            for future in concurrent.futures.as_completed(future_to_table):
                table_name = future_to_table[future]
                try:
                    mappings = future.result()
                    all_mappings[table_name] = mappings
                except Exception as e:
                    print(f"Error mapping components from table {table_name}: {e}")
        
        # Step 4: Generate KiCAD database with parallel processing
        generator = KiCADDbLibGenerator(output_dir_parallel)
        generator.enable_parallel_processing = True
        generator.max_worker_threads = 4
        
        result_parallel = generator.generate(all_mappings)
        
        parallel_time = time.time() - start_time_parallel
        
        # Log performance metrics
        print(f"\nPerformance - Serial end-to-end time: {serial_time:.2f} seconds")
        print(f"Performance - Parallel end-to-end time: {parallel_time:.2f} seconds")
        print(f"Performance - Speedup factor: {serial_time / parallel_time:.2f}x")
        
        # Verify that both methods produced the same results
        conn_serial = sqlite3.connect(result_serial['database_path'])
        cursor_serial = conn_serial.cursor()
        
        conn_parallel = sqlite3.connect(result_parallel['database_path'])
        cursor_parallel = conn_parallel.cursor()
        
        # Check component counts
        cursor_serial.execute("SELECT COUNT(*) FROM components")
        serial_count = cursor_serial.fetchone()[0]
        
        cursor_parallel.execute("SELECT COUNT(*) FROM components")
        parallel_count = cursor_parallel.fetchone()[0]
        
        assert serial_count == parallel_count
        
        conn_serial.close()
        conn_parallel.close()
        
        # Assert that parallel processing is faster
        assert parallel_time < serial_time, "Parallel processing should be faster than serial processing"
    
    def test_parallel_scaling_with_thread_count(self, parallel_test_fixture):
        """Test how performance scales with the number of threads."""
        dblib_file = parallel_test_fixture['dblib_file']
        output_dir = parallel_test_fixture['output_dir_parallel']
        
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        altium_data = parser.extract_all_data(altium_config)
        
        mapper = ComponentMappingEngine()
        all_mappings = {}
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
        
        # Test with different thread counts
        thread_counts = [1, 2, 4, 8]
        execution_times = []
        
        for thread_count in thread_counts:
            # Create a new output directory for each run
            thread_output_dir = os.path.join(output_dir, f"threads_{thread_count}")
            os.makedirs(thread_output_dir, exist_ok=True)
            
            # Generate database with specified thread count
            start_time = time.time()
            
            generator = KiCADDbLibGenerator(thread_output_dir)
            generator.enable_parallel_processing = True
            generator.max_worker_threads = thread_count
            
            generator.generate(all_mappings)
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            print(f"\nPerformance - {thread_count} threads: {execution_time:.2f} seconds")
        
        # Calculate speedup relative to single thread
        single_thread_time = execution_times[0]
        speedups = [single_thread_time / time for time in execution_times]
        
        print("\nThread count vs. Speedup:")
        for i, thread_count in enumerate(thread_counts):
            print(f"{thread_count} threads: {speedups[i]:.2f}x speedup")
        
        # Verify that performance improves with more threads (up to a point)
        assert speedups[1] > 1.0, "2 threads should be faster than 1 thread"
        assert speedups[2] > speedups[1], "4 threads should be faster than 2 threads"
        
        # Note: 8 threads might not be faster than 4 threads due to overhead
        # and limited parallelism in the task