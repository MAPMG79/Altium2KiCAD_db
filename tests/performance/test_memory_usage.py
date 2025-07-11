"""
Performance tests for memory usage.

These tests measure the memory consumption of the migration tool during
different operations and with different dataset sizes.
"""

import os
import gc
import time
import pytest
import sqlite3
import psutil
import tracemalloc
from pathlib import Path

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.mapping_engine import ComponentMappingEngine
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager


class TestMemoryUsage:
    """Performance tests for memory usage."""

    @pytest.fixture
    def memory_test_fixture(self, migration_test_framework, temp_dir):
        """Create datasets of different sizes for memory testing."""
        # Create databases of different sizes
        db_sizes = {
            'small': {'components_per_table': 100, 'tables': ['Resistors', 'Capacitors']},
            'medium': {'components_per_table': 500, 'tables': ['Resistors', 'Capacitors', 'Diodes']},
            'large': {'components_per_table': 1000, 'tables': ['Resistors', 'Capacitors', 'Diodes', 'Transistors']}
        }
        
        fixture_data = {}
        
        for size_name, size_config in db_sizes.items():
            # Create a database
            db_path = os.path.join(temp_dir, f"{size_name}_test.db")
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()
            
            # Create tables
            for table_name in size_config['tables']:
                if table_name == 'Resistors':
                    cursor.execute(f"""
                        CREATE TABLE {table_name} (
                            id INTEGER PRIMARY KEY,
                            LibReference TEXT,
                            Footprint TEXT,
                            Value TEXT,
                            Description TEXT,
                            Manufacturer TEXT,
                            Package TEXT,
                            Tolerance TEXT,
                            Power TEXT
                        )
                    """)
                elif table_name == 'Capacitors':
                    cursor.execute(f"""
                        CREATE TABLE {table_name} (
                            id INTEGER PRIMARY KEY,
                            LibReference TEXT,
                            Footprint TEXT,
                            Value TEXT,
                            Description TEXT,
                            Manufacturer TEXT,
                            Package TEXT,
                            Voltage TEXT,
                            Tolerance TEXT
                        )
                    """)
                elif table_name == 'Diodes':
                    cursor.execute(f"""
                        CREATE TABLE {table_name} (
                            id INTEGER PRIMARY KEY,
                            LibReference TEXT,
                            Footprint TEXT,
                            Value TEXT,
                            Description TEXT,
                            Manufacturer TEXT,
                            Package TEXT,
                            Voltage TEXT,
                            Current TEXT
                        )
                    """)
                elif table_name == 'Transistors':
                    cursor.execute(f"""
                        CREATE TABLE {table_name} (
                            id INTEGER PRIMARY KEY,
                            LibReference TEXT,
                            Footprint TEXT,
                            Value TEXT,
                            Description TEXT,
                            Manufacturer TEXT,
                            Package TEXT,
                            Type TEXT,
                            Voltage TEXT,
                            Current TEXT
                        )
                    """)
            
            # Insert data
            components_per_table = size_config['components_per_table']
            
            for table_name in size_config['tables']:
                if table_name == 'Resistors':
                    for i in range(components_per_table):
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
                    for i in range(components_per_table):
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
                    for i in range(components_per_table):
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
                    for i in range(components_per_table):
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
            connection.close()
            
            # Create a DbLib file
            dblib_file = os.path.join(temp_dir, f"{size_name}_test.DbLib")
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
                for table_name in size_config['tables']:
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
            output_dir = os.path.join(temp_dir, f"output_{size_name}")
            os.makedirs(output_dir, exist_ok=True)
            
            # Store data for this size
            fixture_data[size_name] = {
                'dblib_file': dblib_file,
                'db_path': db_path,
                'output_dir': output_dir,
                'total_components': len(size_config['tables']) * size_config['components_per_table']
            }
        
        return fixture_data
    
    def get_process_memory(self):
        """Get the memory usage of the current process in MB."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)  # Convert to MB
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure the memory usage of a function."""
        # Force garbage collection before measurement
        gc.collect()
        
        # Start memory tracing
        tracemalloc.start()
        
        # Get initial memory usage
        initial_memory = self.get_process_memory()
        
        # Execute the function
        result = func(*args, **kwargs)
        
        # Get peak memory usage
        peak_memory = self.get_process_memory()
        
        # Get memory allocated by the function
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Calculate memory usage
        memory_used = peak_memory - initial_memory
        
        return {
            'result': result,
            'initial_memory_mb': initial_memory,
            'peak_memory_mb': peak_memory,
            'memory_used_mb': memory_used,
            'tracemalloc_current_mb': current / (1024 * 1024),
            'tracemalloc_peak_mb': peak / (1024 * 1024)
        }
    
    def test_memory_usage_by_dataset_size(self, memory_test_fixture):
        """Test memory usage with different dataset sizes."""
        results = {}
        
        for size_name, fixture in memory_test_fixture.items():
            dblib_file = fixture['dblib_file']
            output_dir = fixture['output_dir']
            total_components = fixture['total_components']
            
            print(f"\nTesting memory usage for {size_name} dataset ({total_components} components)")
            
            # Step 1: Parse DbLib file
            parser = AltiumDbLibParser()
            parse_memory = self.measure_memory_usage(parser.parse_dblib_file, dblib_file)
            altium_config = parse_memory['result']
            
            # Step 2: Extract data
            extract_memory = self.measure_memory_usage(parser.extract_all_data, altium_config)
            altium_data = extract_memory['result']
            
            # Step 3: Map components
            mapper = ComponentMappingEngine()
            all_mappings = {}
            
            map_memory = {'memory_used_mb': 0, 'peak_memory_mb': 0}
            
            for table_name, table_data in altium_data.items():
                if 'data' in table_data and table_data['data']:
                    table_map_memory = self.measure_memory_usage(
                        mapper.map_table_data, table_name, table_data
                    )
                    all_mappings[table_name] = table_map_memory['result']
                    
                    # Accumulate memory usage
                    map_memory['memory_used_mb'] += table_map_memory['memory_used_mb']
                    map_memory['peak_memory_mb'] = max(
                        map_memory['peak_memory_mb'], 
                        table_map_memory['peak_memory_mb']
                    )
            
            # Step 4: Generate KiCAD database
            generator = KiCADDbLibGenerator(output_dir)
            generate_memory = self.measure_memory_usage(generator.generate, all_mappings)
            
            # Store results for this size
            results[size_name] = {
                'total_components': total_components,
                'parse_memory_mb': parse_memory['memory_used_mb'],
                'extract_memory_mb': extract_memory['memory_used_mb'],
                'map_memory_mb': map_memory['memory_used_mb'],
                'generate_memory_mb': generate_memory['memory_used_mb'],
                'peak_memory_mb': max(
                    parse_memory['peak_memory_mb'],
                    extract_memory['peak_memory_mb'],
                    map_memory['peak_memory_mb'],
                    generate_memory['peak_memory_mb']
                )
            }
            
            # Log results
            print(f"  Parse DbLib memory usage: {parse_memory['memory_used_mb']:.2f} MB")
            print(f"  Extract data memory usage: {extract_memory['memory_used_mb']:.2f} MB")
            print(f"  Map components memory usage: {map_memory['memory_used_mb']:.2f} MB")
            print(f"  Generate database memory usage: {generate_memory['memory_used_mb']:.2f} MB")
            print(f"  Peak memory usage: {results[size_name]['peak_memory_mb']:.2f} MB")
        
        # Compare memory usage across dataset sizes
        print("\nMemory usage comparison:")
        for size_name, result in results.items():
            print(f"{size_name} dataset ({result['total_components']} components):")
            print(f"  Peak memory usage: {result['peak_memory_mb']:.2f} MB")
            print(f"  Memory per component: {result['peak_memory_mb'] / result['total_components']:.4f} MB")
        
        # Verify that memory usage scales reasonably with dataset size
        # Memory usage should increase with dataset size, but not necessarily linearly
        assert results['medium']['peak_memory_mb'] > results['small']['peak_memory_mb']
        assert results['large']['peak_memory_mb'] > results['medium']['peak_memory_mb']
        
        # Check that memory per component decreases or stays relatively constant
        # (indicating better efficiency with larger datasets)
        small_memory_per_component = results['small']['peak_memory_mb'] / results['small']['total_components']
        medium_memory_per_component = results['medium']['peak_memory_mb'] / results['medium']['total_components']
        large_memory_per_component = results['large']['peak_memory_mb'] / results['large']['total_components']
        
        print(f"\nMemory efficiency:")
        print(f"  Small dataset: {small_memory_per_component:.4f} MB per component")
        print(f"  Medium dataset: {medium_memory_per_component:.4f} MB per component")
        print(f"  Large dataset: {large_memory_per_component:.4f} MB per component")
        
        # Memory per component should decrease or stay relatively constant
        # Allow for some variation due to fixed overhead
        assert medium_memory_per_component <= small_memory_per_component * 1.2
        assert large_memory_per_component <= medium_memory_per_component * 1.2
    
    def test_memory_usage_by_operation(self, memory_test_fixture):
        """Test memory usage for different operations."""
        # Use the medium dataset for this test
        fixture = memory_test_fixture['medium']
        dblib_file = fixture['dblib_file']
        output_dir = fixture['output_dir']
        
        print("\nTesting memory usage by operation")
        
        # Step 1: Parse DbLib file
        parser = AltiumDbLibParser()
        parse_memory = self.measure_memory_usage(parser.parse_dblib_file, dblib_file)
        altium_config = parse_memory['result']
        
        print(f"  Parse DbLib memory usage: {parse_memory['memory_used_mb']:.2f} MB")
        print(f"  Parse DbLib peak memory: {parse_memory['peak_memory_mb']:.2f} MB")
        
        # Step 2: Extract data
        extract_memory = self.measure_memory_usage(parser.extract_all_data, altium_config)
        altium_data = extract_memory['result']
        
        print(f"  Extract data memory usage: {extract_memory['memory_used_mb']:.2f} MB")
        print(f"  Extract data peak memory: {extract_memory['peak_memory_mb']:.2f} MB")
        
        # Step 3: Map components
        mapper = ComponentMappingEngine()
        all_mappings = {}
        
        map_memory_total = 0
        map_memory_peak = 0
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                table_map_memory = self.measure_memory_usage(
                    mapper.map_table_data, table_name, table_data
                )
                all_mappings[table_name] = table_map_memory['result']
                
                map_memory_total += table_map_memory['memory_used_mb']
                map_memory_peak = max(map_memory_peak, table_map_memory['peak_memory_mb'])
        
        print(f"  Map components memory usage: {map_memory_total:.2f} MB")
        print(f"  Map components peak memory: {map_memory_peak:.2f} MB")
        
        # Step 4: Generate KiCAD database
        generator = KiCADDbLibGenerator(output_dir)
        
        # 4.1: Create database schema
        schema_memory = self.measure_memory_usage(generator.create_database_schema)
        
        print(f"  Create schema memory usage: {schema_memory['memory_used_mb']:.2f} MB")
        print(f"  Create schema peak memory: {schema_memory['peak_memory_mb']:.2f} MB")
        
        # 4.2: Populate categories
        categories_memory = self.measure_memory_usage(generator.populate_categories, all_mappings)
        category_ids = categories_memory['result']
        
        print(f"  Populate categories memory usage: {categories_memory['memory_used_mb']:.2f} MB")
        print(f"  Populate categories peak memory: {categories_memory['peak_memory_mb']:.2f} MB")
        
        # 4.3: Populate components
        components_memory = self.measure_memory_usage(
            generator.populate_components, all_mappings, category_ids
        )
        
        print(f"  Populate components memory usage: {components_memory['memory_used_mb']:.2f} MB")
        print(f"  Populate components peak memory: {components_memory['peak_memory_mb']:.2f} MB")
        
        # 4.4: Generate KiCAD DbLib file
        dblib_memory = self.measure_memory_usage(
            generator.generate_kicad_dblib_file, all_mappings
        )
        
        print(f"  Generate DbLib file memory usage: {dblib_memory['memory_used_mb']:.2f} MB")
        print(f"  Generate DbLib file peak memory: {dblib_memory['peak_memory_mb']:.2f} MB")
        
        # 4.5: Generate migration report
        report_memory = self.measure_memory_usage(
            generator.generate_migration_report, all_mappings
        )
        
        print(f"  Generate report memory usage: {report_memory['memory_used_mb']:.2f} MB")
        print(f"  Generate report peak memory: {report_memory['peak_memory_mb']:.2f} MB")
        
        # Verify that memory usage for each operation is reasonable
        assert parse_memory['memory_used_mb'] < 50, "Parse DbLib memory usage is too high"
        assert extract_memory['memory_used_mb'] < 100, "Extract data memory usage is too high"
        assert map_memory_total < 100, "Map components memory usage is too high"
        assert schema_memory['memory_used_mb'] < 50, "Create schema memory usage is too high"
        assert categories_memory['memory_used_mb'] < 50, "Populate categories memory usage is too high"
        assert components_memory['memory_used_mb'] < 100, "Populate components memory usage is too high"
        assert dblib_memory['memory_used_mb'] < 50, "Generate DbLib file memory usage is too high"
        assert report_memory['memory_used_mb'] < 50, "Generate report memory usage is too high"
    
    def test_memory_usage_with_caching(self, memory_test_fixture):
        """Test memory usage with and without caching."""
        # Use the medium dataset for this test
        fixture = memory_test_fixture['medium']
        dblib_file = fixture['dblib_file']
        output_dir = fixture['output_dir']
        
        print("\nTesting memory usage with and without caching")
        
        # Step 1: Parse DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(dblib_file)
        
        # Step 2: Extract data
        altium_data = parser.extract_all_data(altium_config)
        
        # Step 3: Map components without caching
        mapper_no_cache = ComponentMappingEngine()
        mapper_no_cache.enable_caching = False
        
        map_no_cache_memory = self.measure_memory_usage(
            lambda: {
                table_name: mapper_no_cache.map_table_data(table_name, table_data)
                for table_name, table_data in altium_data.items()
                if 'data' in table_data and table_data['data']
            }
        )
        
        all_mappings_no_cache = map_no_cache_memory['result']
        
        print(f"  Map components without caching memory usage: {map_no_cache_memory['memory_used_mb']:.2f} MB")
        print(f"  Map components without caching peak memory: {map_no_cache_memory['peak_memory_mb']:.2f} MB")
        
        # Step 3: Map components with caching
        mapper_with_cache = ComponentMappingEngine()
        mapper_with_cache.enable_caching = True
        
        map_with_cache_memory = self.measure_memory_usage(
            lambda: {
                table_name: mapper_with_cache.map_table_data(table_name, table_data)
                for table_name, table_data in altium_data.items()
                if 'data' in table_data and table_data['data']
            }
        )
        
        all_mappings_with_cache = map_with_cache_memory['result']
        
        print(f"  Map components with caching memory usage: {map_with_cache_memory['memory_used_mb']:.2f} MB")
        print(f"  Map components with caching peak memory: {map_with_cache_memory['peak_memory_mb']:.2f} MB")
        
        # Compare memory usage
        print(f"  Memory usage difference: {map_with_cache_memory['memory_used_mb'] - map_no_cache_memory['memory_used_mb']:.2f} MB")
        
        # Verify that caching increases memory usage (due to storing cached results)
        assert map_with_cache_memory['memory_used_mb'] > map_no_cache_memory['memory_used_mb']
        
        # But the increase should be reasonable
        assert map_with_cache_memory['memory_used_mb'] < map_no_cache_memory['memory_used_mb'] * 2
        
        # Verify that both methods produced the same mappings
        assert set(all_mappings_no_cache.keys()) == set(all_mappings_with_cache.keys())
        
        for table_name in all_mappings_no_cache.keys():
            assert len(all_mappings_no_cache[table_name]) == len(all_mappings_with_cache[table_name])
    
    def test_memory_cleanup(self, memory_test_fixture):
        """Test memory cleanup after operations."""
        # Use the medium dataset for this test
        fixture = memory_test_fixture['medium']
        dblib_file = fixture['dblib_file']
        output_dir = fixture['output_dir']
        
        print("\nTesting memory cleanup after operations")
        
        # Get initial memory usage
        initial_memory = self.get_process_memory()
        print(f"  Initial memory usage: {initial_memory:.2f} MB")
        
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
        generator.generate(all_mappings)
        
        # Get memory usage after operations
        after_operations_memory = self.get_process_memory()
        print(f"  Memory usage after operations: {after_operations_memory:.2f} MB")
        print(f"  Memory increase: {after_operations_memory - initial_memory:.2f} MB")
        
        # Clear references to large objects
        del altium_config
        del altium_data
        del all_mappings
        del generator
        
        # Force garbage collection
        gc.collect()
        
        # Get memory usage after cleanup
        after_cleanup_memory = self.get_process_memory()
        print(f"  Memory usage after cleanup: {after_cleanup_memory:.2f} MB")
        print(f"  Memory decrease after cleanup: {after_operations_memory - after_cleanup_memory:.2f} MB")
        
        # Verify that memory was released
        assert after_cleanup_memory < after_operations_memory
        
        # Memory usage should be closer to initial memory after cleanup
        # Allow for some overhead that might not be released
        assert after_cleanup_memory < after_operations_memory * 0.7