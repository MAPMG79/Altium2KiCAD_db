"""
Unit tests for the Database Utilities module.
"""

import os
import pytest
import sqlite3
import pyodbc
from unittest.mock import patch, MagicMock, call

from migration_tool.utils.database_utils import (
    create_connection,
    execute_query,
    execute_script,
    table_exists,
    get_table_columns,
    optimize_database,
    create_indexes
)


class TestDatabaseUtils:
    """Test cases for the database utility functions."""

    def test_create_connection_sqlite(self, temp_dir):
        """Test creating a SQLite connection."""
        db_path = os.path.join(temp_dir, 'test.db')
        
        # Create a connection
        connection = create_connection(db_path, 'sqlite')
        
        # Check that a valid connection was returned
        assert isinstance(connection, sqlite3.Connection)
        
        # Clean up
        connection.close()
    
    @patch('pyodbc.connect')
    def test_create_connection_odbc(self, mock_connect):
        """Test creating an ODBC connection."""
        # Set up mock
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Test different database types
        db_types = ['access', 'sqlserver', 'mysql', 'postgresql']
        connection_string = 'Driver={SQL Server};Server=localhost;Database=test;'
        
        for db_type in db_types:
            # Create a connection
            connection = create_connection(connection_string, db_type)
            
            # Check that pyodbc.connect was called
            mock_connect.assert_called_with(connection_string)
            
            # Check that the mock connection was returned
            assert connection == mock_connection
    
    def test_create_connection_unsupported(self):
        """Test creating a connection with an unsupported database type."""
        with pytest.raises(ValueError) as excinfo:
            create_connection('test.db', 'unsupported')
        
        # Check the error message
        assert 'Unsupported database type' in str(excinfo.value)
    
    def test_execute_query_with_results(self):
        """Test executing a query that returns results."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
        
        # Create a test table and insert data
        cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
        cursor.execute('INSERT INTO test VALUES (1, "Alice")')
        cursor.execute('INSERT INTO test VALUES (2, "Bob")')
        connection.commit()
        
        # Execute the query
        results = execute_query(connection, 'SELECT * FROM test')
        
        # Check the results
        assert len(results) == 2
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'Alice'
        assert results[1]['id'] == 2
        assert results[1]['name'] == 'Bob'
        
        # Clean up
        connection.close()
    
    def test_execute_query_with_params(self):
        """Test executing a query with parameters."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
        
        # Create a test table and insert data
        cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
        cursor.execute('INSERT INTO test VALUES (1, "Alice")')
        cursor.execute('INSERT INTO test VALUES (2, "Bob")')
        connection.commit()
        
        # Execute the query with parameters
        results = execute_query(connection, 'SELECT * FROM test WHERE id = ?', (1,))
        
        # Check the results
        assert len(results) == 1
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'Alice'
        
        # Clean up
        connection.close()
    
    def test_execute_query_no_results(self):
        """Test executing a query that returns no results."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
        
        # Create a test table
        cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
        connection.commit()
        
        # Execute a query that returns no results
        results = execute_query(connection, 'SELECT * FROM test')
        
        # Check that an empty list is returned
        assert results == []
        
        # Clean up
        connection.close()
    
    def test_execute_query_non_select(self):
        """Test executing a non-SELECT query."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
        
        # Create a test table
        cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
        connection.commit()
        
        # Execute an INSERT query
        results = execute_query(connection, 'INSERT INTO test VALUES (1, "Alice")')
        
        # Check that an empty list is returned
        assert results == []
        
        # Verify that the data was inserted
        cursor.execute('SELECT * FROM test')
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1
        assert rows[0][1] == 'Alice'
        
        # Clean up
        connection.close()
    
    def test_execute_script(self):
        """Test executing a SQL script with multiple statements."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        
        # Create a script with multiple statements
        script = """
        CREATE TABLE test1 (id INTEGER, name TEXT);
        CREATE TABLE test2 (id INTEGER, value REAL);
        INSERT INTO test1 VALUES (1, 'Alice');
        INSERT INTO test2 VALUES (1, 3.14);
        """
        
        # Execute the script
        execute_script(connection, script)
        
        # Verify that the tables were created and data was inserted
        cursor = connection.cursor()
        
        cursor.execute('SELECT * FROM test1')
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1
        assert rows[0][1] == 'Alice'
        
        cursor.execute('SELECT * FROM test2')
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1
        assert rows[0][1] == 3.14
        
        # Clean up
        connection.close()
    
    def test_execute_script_odbc(self):
        """Test executing a script with an ODBC connection."""
        # Create a mock ODBC connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Create a script
        script = """
        CREATE TABLE test (id INTEGER, name TEXT);
        INSERT INTO test VALUES (1, 'Alice');
        """
        
        # Execute the script
        execute_script(mock_connection, script)
        
        # Check that execute was called with the script
        mock_cursor.execute.assert_called_with(script)
        
        # Check that commit was called
        mock_connection.commit.assert_called_once()
    
    def test_table_exists_sqlite_true(self):
        """Test checking if a table exists in SQLite (true case)."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
        
        # Create a test table
        cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
        connection.commit()
        
        # Check if the table exists
        result = table_exists(connection, 'test')
        
        # Check the result
        assert result is True
        
        # Clean up
        connection.close()
    
    def test_table_exists_sqlite_false(self):
        """Test checking if a table exists in SQLite (false case)."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        
        # Check if a nonexistent table exists
        result = table_exists(connection, 'nonexistent')
        
        # Check the result
        assert result is False
        
        # Clean up
        connection.close()
    
    def test_table_exists_odbc_true(self):
        """Test checking if a table exists with ODBC (true case)."""
        # Create a mock ODBC connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Set up the mock to return a non-empty result
        mock_cursor.fetchall.return_value = [('test',)]
        
        # Check if the table exists
        result = table_exists(mock_connection, 'test')
        
        # Check the result
        assert result is True
    
    def test_table_exists_odbc_false_tables_method(self):
        """Test checking if a table exists with ODBC (false case, tables method)."""
        # Create a mock ODBC connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Set up the mock to return an empty result
        mock_cursor.fetchall.return_value = []
        
        # Check if the table exists
        result = table_exists(mock_connection, 'nonexistent')
        
        # Check the result
        assert result is False
    
    def test_table_exists_odbc_false_fallback(self):
        """Test checking if a table exists with ODBC (false case, fallback method)."""
        # Create a mock ODBC connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Set up the mock to raise an exception for tables method
        mock_cursor.tables.side_effect = Exception("Method not supported")
        
        # Set up the mock to raise an exception for the fallback query
        mock_cursor.execute.side_effect = Exception("Table not found")
        
        # Check if the table exists
        result = table_exists(mock_connection, 'nonexistent')
        
        # Check the result
        assert result is False
    
    def test_get_table_columns_sqlite(self):
        """Test getting table columns in SQLite."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
        
        # Create a test table
        cursor.execute('CREATE TABLE test (id INTEGER, name TEXT, value REAL)')
        connection.commit()
        
        # Get the table columns
        columns = get_table_columns(connection, 'test')
        
        # Check the result
        assert columns == ['id', 'name', 'value']
        
        # Clean up
        connection.close()
    
    def test_get_table_columns_odbc(self):
        """Test getting table columns with ODBC."""
        # Create a mock ODBC connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Set up the mock cursor description
        mock_cursor.description = [('id', None, None, None, None, None, None),
                                  ('name', None, None, None, None, None, None),
                                  ('value', None, None, None, None, None, None)]
        
        # Get the table columns
        columns = get_table_columns(mock_connection, 'test')
        
        # Check the result
        assert columns == ['id', 'name', 'value']
    
    def test_get_table_columns_error(self):
        """Test getting table columns when an error occurs."""
        # Create a mock connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Set up the mock to raise an exception
        mock_cursor.execute.side_effect = Exception("Table not found")
        
        # Get the table columns
        columns = get_table_columns(mock_connection, 'nonexistent')
        
        # Check that an empty list is returned
        assert columns == []
    
    @patch('sqlite3.connect')
    def test_optimize_database(self, mock_connect):
        """Test optimizing a SQLite database."""
        # Set up mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # Call the function
        optimize_database('test.db')
        
        # Check that the connection was created
        mock_connect.assert_called_with('test.db')
        
        # Check that the cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Check that the optimization commands were executed
        expected_calls = [
            call('ANALYZE'),
            call('VACUUM'),
            call('PRAGMA journal_mode=WAL'),
            call('PRAGMA synchronous=NORMAL'),
            call('PRAGMA cache_size=10000'),
            call('PRAGMA temp_store=MEMORY')
        ]
        mock_cursor.execute.assert_has_calls(expected_calls, any_order=False)
        
        # Check that commit was called
        mock_connection.commit.assert_called_once()
        
        # Check that the connection was closed
        mock_connection.close.assert_called_once()
    
    def test_create_indexes(self):
        """Test creating indexes on specified columns."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
        
        # Create a test table
        cursor.execute('CREATE TABLE test (id INTEGER, name TEXT, value REAL)')
        connection.commit()
        
        # Create indexes
        columns = ['id', 'name']
        create_indexes(connection, 'test', columns)
        
        # Check that the indexes were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='test'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        assert 'idx_test_id' in indexes
        assert 'idx_test_name' in indexes
        
        # Clean up
        connection.close()
    
    def test_create_indexes_empty_columns(self):
        """Test creating indexes with an empty list of columns."""
        # Create a test database in memory
        connection = sqlite3.connect(':memory:')
        
        # Create indexes with an empty list
        create_indexes(connection, 'test', [])
        
        # Check that no errors occurred
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='test'")
        indexes = cursor.fetchall()
        
        assert len(indexes) == 0
        
        # Clean up
        connection.close()