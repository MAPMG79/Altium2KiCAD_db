"""
Integration tests for database operations.

These tests verify that database operations work correctly across
different components of the system.
"""

import os
import pytest
import sqlite3
import tempfile
from pathlib import Path

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.database_utils import (
    create_connection,
    execute_query,
    execute_script,
    table_exists,
    get_table_columns,
    optimize_database,
    create_indexes
)


class TestDatabaseOperations:
    """Integration tests for database operations."""

    def test_altium_database_connection(self, migration_test_framework, temp_dir):
        """Test connecting to an Altium database."""
        # Create a sample Altium database
        db_path = migration_test_framework.create_sample_database(temp_dir)
        
        # Create a DbLib file pointing to the database
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir, db_path=db_path)
        
        # Parse the DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(str(dblib_file))
        
        # Verify that the connection string was extracted
        assert 'connection_string' in altium_config
        
        # Connect to the database
        connection = parser.connect_to_database(altium_config['connection_string'])
        
        # Verify that the connection is valid
        assert connection is not None
        
        # Check that tables exist
        for table_name in altium_config['tables']:
            assert table_exists(connection, table_name)
        
        # Clean up
        connection.close()
    
    def test_altium_data_extraction(self, migration_test_framework, temp_dir):
        """Test extracting data from an Altium database."""
        # Create a sample Altium database
        db_path = migration_test_framework.create_sample_database(temp_dir)
        
        # Create a DbLib file pointing to the database
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir, db_path=db_path)
        
        # Parse the DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(str(dblib_file))
        
        # Extract data from all tables
        altium_data = parser.extract_all_data(altium_config)
        
        # Verify that data was extracted
        assert altium_data is not None
        assert len(altium_data) > 0
        
        # Check that each table has data
        for table_name, table_data in altium_data.items():
            assert 'columns' in table_data
            assert 'data' in table_data
            assert len(table_data['data']) > 0
            
            # Check that column names match the database
            connection = parser.connect_to_database(altium_config['connection_string'])
            db_columns = get_table_columns(connection, table_name)
            assert set(table_data['columns']) == set(db_columns)
            connection.close()
    
    def test_kicad_database_creation(self, migration_test_framework, temp_dir):
        """Test creating a KiCAD database."""
        # Set up output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a KiCAD database generator
        generator = KiCADDbLibGenerator(output_dir)
        
        # Create the database schema
        generator.create_database_schema()
        
        # Verify that the database file was created
        db_path = os.path.join(output_dir, "components.db")
        assert os.path.exists(db_path)
        
        # Connect to the database
        connection = sqlite3.connect(db_path)
        
        # Verify that tables were created
        assert table_exists(connection, "components")
        assert table_exists(connection, "categories")
        
        # Verify that views were created
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        assert len(views) > 0
        
        # Clean up
        connection.close()
    
    def test_kicad_database_population(self, migration_test_framework, temp_dir):
        """Test populating a KiCAD database."""
        # Set up output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a KiCAD database generator
        generator = KiCADDbLibGenerator(output_dir)
        
        # Create the database schema
        generator.create_database_schema()
        
        # Create sample component mappings
        component_mappings = migration_test_framework.create_sample_component_mappings()
        
        # Populate categories
        category_ids = generator.populate_categories(component_mappings)
        
        # Verify that categories were created
        assert len(category_ids) > 0
        
        # Populate components
        generator.populate_components(component_mappings, category_ids)
        
        # Connect to the database
        db_path = os.path.join(output_dir, "components.db")
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Verify that components were inserted
        cursor.execute("SELECT COUNT(*) FROM components")
        component_count = cursor.fetchone()[0]
        assert component_count > 0
        
        # Verify that categories were inserted
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        assert category_count > 0
        
        # Clean up
        connection.close()
    
    def test_database_optimization(self, migration_test_framework, temp_dir):
        """Test optimizing a database."""
        # Create a sample database
        db_path = os.path.join(temp_dir, "test.db")
        connection = sqlite3.connect(db_path)
        
        # Create a test table and insert data
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        
        # Insert some data
        for i in range(1000):
            cursor.execute("INSERT INTO test VALUES (?, ?)", (i, f"Name {i}"))
        
        connection.commit()
        connection.close()
        
        # Get the initial file size
        initial_size = os.path.getsize(db_path)
        
        # Optimize the database
        optimize_database(db_path)
        
        # Verify that the database still exists
        assert os.path.exists(db_path)
        
        # Connect to the optimized database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Verify that the data is still intact
        cursor.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        assert count == 1000
        
        # Check that pragma settings were applied
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode == "wal"
        
        cursor.execute("PRAGMA synchronous")
        synchronous = cursor.fetchone()[0]
        assert synchronous == 1  # NORMAL
        
        # Clean up
        connection.close()
    
    def test_database_indexes(self, migration_test_framework, temp_dir):
        """Test creating indexes on a database."""
        # Create a sample database
        db_path = os.path.join(temp_dir, "test.db")
        connection = sqlite3.connect(db_path)
        
        # Create a test table
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER, name TEXT, value REAL)")
        
        # Insert some data
        for i in range(100):
            cursor.execute("INSERT INTO test VALUES (?, ?, ?)", (i, f"Name {i}", i * 1.5))
        
        connection.commit()
        
        # Create indexes
        columns = ['id', 'name']
        create_indexes(connection, 'test', columns)
        
        # Verify that indexes were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='test'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        assert 'idx_test_id' in indexes
        assert 'idx_test_name' in indexes
        
        # Test query performance with indexes
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM test WHERE id = 50")
        plan = cursor.fetchall()
        plan_str = str(plan)
        
        # Verify that the index is used in the query plan
        assert "SEARCH" in plan_str or "USING INDEX" in plan_str or "USING COVERING INDEX" in plan_str
        
        # Clean up
        connection.close()
    
    def test_database_transaction_handling(self, migration_test_framework, temp_dir):
        """Test database transaction handling."""
        # Create a sample database
        db_path = os.path.join(temp_dir, "test.db")
        connection = sqlite3.connect(db_path)
        
        # Create a test table
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        connection.commit()
        
        # Start a transaction
        try:
            # Execute multiple queries in a transaction
            execute_query(connection, "INSERT INTO test VALUES (1, 'Alice')")
            execute_query(connection, "INSERT INTO test VALUES (2, 'Bob')")
            
            # Intentionally cause an error
            execute_query(connection, "INSERT INTO nonexistent_table VALUES (3, 'Charlie')")
            
            # This should not be reached
            connection.commit()
        except:
            # Rollback on error
            connection.rollback()
        
        # Verify that no data was inserted due to rollback
        results = execute_query(connection, "SELECT COUNT(*) FROM test")
        assert results[0]['COUNT(*)'] == 0
        
        # Now try a successful transaction
        try:
            # Execute multiple queries in a transaction
            execute_query(connection, "INSERT INTO test VALUES (1, 'Alice')")
            execute_query(connection, "INSERT INTO test VALUES (2, 'Bob')")
            
            # Commit the transaction
            connection.commit()
        except:
            connection.rollback()
        
        # Verify that data was inserted
        results = execute_query(connection, "SELECT COUNT(*) FROM test")
        assert results[0]['COUNT(*)'] == 2
        
        # Clean up
        connection.close()
    
    def test_database_error_handling(self, migration_test_framework, temp_dir):
        """Test database error handling."""
        # Create a sample database
        db_path = os.path.join(temp_dir, "test.db")
        connection = sqlite3.connect(db_path)
        
        # Create a test table
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.commit()
        
        # Test handling of constraint violations
        with pytest.raises(sqlite3.IntegrityError):
            execute_query(connection, "INSERT INTO test (id, name) VALUES (1, NULL)")
        
        # Test handling of syntax errors
        with pytest.raises(sqlite3.OperationalError):
            execute_query(connection, "SELECT * FROMM test")
        
        # Test handling of table not found errors
        with pytest.raises(sqlite3.OperationalError):
            execute_query(connection, "SELECT * FROM nonexistent_table")
        
        # Verify that the connection is still usable after errors
        execute_query(connection, "INSERT INTO test (id, name) VALUES (1, 'Alice')")
        results = execute_query(connection, "SELECT * FROM test")
        
        assert len(results) == 1
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'Alice'
        
        # Clean up
        connection.close()
    
    def test_database_migration_integration(self, migration_test_framework, temp_dir):
        """Test integration between Altium database reading and KiCAD database writing."""
        # Create a sample Altium database
        altium_db_path = migration_test_framework.create_sample_database(temp_dir)
        
        # Create a DbLib file pointing to the database
        dblib_file = migration_test_framework.create_sample_dblib_file(temp_dir, db_path=altium_db_path)
        
        # Set up output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Parse the DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(str(dblib_file))
        
        # Extract data from all tables
        altium_data = parser.extract_all_data(altium_config)
        
        # Create a KiCAD database generator
        generator = KiCADDbLibGenerator(output_dir)
        
        # Create sample component mappings based on the Altium data
        component_mappings = {}
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                # Create mappings for this table
                mappings = migration_test_framework.create_mappings_from_data(table_name, table_data)
                component_mappings[table_name] = mappings
        
        # Generate the KiCAD database
        result = generator.generate(component_mappings)
        
        # Verify that the database was generated
        assert os.path.exists(result['database_path'])
        assert os.path.exists(result['dblib_path'])
        
        # Connect to the KiCAD database
        kicad_connection = sqlite3.connect(result['database_path'])
        
        # Verify that components were transferred
        cursor = kicad_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM components")
        component_count = cursor.fetchone()[0]
        
        # Count the total number of components in the Altium data
        altium_component_count = sum(len(table_data.get('data', [])) 
                                   for table_data in altium_data.values())
        
        # Verify that all components were transferred
        assert component_count == altium_component_count
        
        # Clean up
        kicad_connection.close()