"""
Unit tests for the Altium DbLib parser module.
"""

import os
import pytest
import sqlite3
from unittest.mock import patch, MagicMock

from migration_tool.core.altium_parser import AltiumDbLibParser


class TestAltiumDbLibParser:
    """Test cases for the AltiumDbLibParser class."""

    def test_parse_dblib_file(self, sample_dblib_file):
        """Test parsing an Altium DbLib file."""
        parser = AltiumDbLibParser()
        config = parser.parse_dblib_file(sample_dblib_file)
        
        # Check that the connection string was extracted
        assert 'connection_string' in config
        assert 'Driver=SQLite3;Database=' in config['connection_string']
        
        # Check that tables were parsed
        assert 'tables' in config
        assert 'Resistors' in config['tables']
        assert 'Capacitors' in config['tables']
        
        # Check table configuration
        resistors_config = config['tables']['Resistors']
        assert resistors_config['enabled'] is True
        assert resistors_config['key_field'] == 'Part Number'
        assert resistors_config['symbol_field'] == 'Symbol'
        assert resistors_config['footprint_field'] == 'Footprint'
        assert resistors_config['description_field'] == 'Description'
    
    def test_detect_database_type(self):
        """Test database type detection from connection string."""
        parser = AltiumDbLibParser()
        
        # Test Access database detection
        parser.connection_string = 'Provider=Microsoft.ACE.OLEDB.12.0;Data Source=test.mdb;'
        assert parser._detect_database_type() == 'access'
        
        # Test SQL Server detection
        parser.connection_string = 'Driver={SQL Server};Server=myServer;Database=myDB;'
        assert parser._detect_database_type() == 'sqlserver'
        
        # Test SQLite detection
        parser.connection_string = 'Driver=SQLite3;Database=test.db;'
        assert parser._detect_database_type() == 'sqlite'
        
        # Test MySQL detection
        parser.connection_string = 'Driver={MySQL ODBC 8.0 Driver};Server=localhost;Database=myDB;'
        assert parser._detect_database_type() == 'mysql'
        
        # Test PostgreSQL detection
        parser.connection_string = 'Driver={PostgreSQL};Server=localhost;Database=myDB;'
        assert parser._detect_database_type() == 'postgresql'
        
        # Test unknown database type
        parser.connection_string = 'Driver={Unknown};Server=localhost;Database=myDB;'
        assert parser._detect_database_type() == 'unknown'
    
    def test_extract_sqlite_path(self):
        """Test extracting SQLite database path from connection string."""
        parser = AltiumDbLibParser()
        
        # Test standard format
        parser.connection_string = 'Driver=SQLite3;Database=C:/path/to/test.db;'
        assert parser._extract_sqlite_path() == 'C:/path/to/test.db'
        
        # Test alternative format
        parser.connection_string = 'Driver=SQLite3;Database=C:\\path\\to\\test.db'
        assert parser._extract_sqlite_path() == 'C:\\path\\to\\test.db'
        
        # Test with additional parameters
        parser.connection_string = 'Driver=SQLite3;Database=test.db;Mode=ReadOnly;'
        assert parser._extract_sqlite_path() == 'test.db'
        
        # Test with invalid format
        parser.connection_string = 'Driver=SQLite3;InvalidParam=test.db;'
        with pytest.raises(ValueError):
            parser._extract_sqlite_path()
    
    @patch('migration_tool.core.altium_parser.pyodbc')
    def test_connect_to_database_access(self, mock_pyodbc):
        """Test connecting to an Access database."""
        parser = AltiumDbLibParser()
        parser.connection_string = 'Provider=Microsoft.ACE.OLEDB.12.0;Data Source=test.mdb;'
        
        mock_connection = MagicMock()
        mock_pyodbc.connect.return_value = mock_connection
        
        connection = parser.connect_to_database()
        
        # Check that pyodbc.connect was called with the correct connection string
        mock_pyodbc.connect.assert_called_once_with(parser.connection_string)
        assert connection == mock_connection
    
    @patch('migration_tool.core.altium_parser.sqlite3')
    def test_connect_to_database_sqlite(self, mock_sqlite3):
        """Test connecting to a SQLite database."""
        parser = AltiumDbLibParser()
        parser.connection_string = 'Driver=SQLite3;Database=test.db;'
        
        mock_connection = MagicMock()
        mock_sqlite3.connect.return_value = mock_connection
        
        # Mock the _extract_sqlite_path method
        parser._extract_sqlite_path = MagicMock(return_value='test.db')
        
        connection = parser.connect_to_database()
        
        # Check that sqlite3.connect was called with the correct database path
        mock_sqlite3.connect.assert_called_once_with('test.db')
        assert connection == mock_connection
    
    def test_connect_to_database_unsupported(self):
        """Test connecting to an unsupported database type."""
        parser = AltiumDbLibParser()
        parser.connection_string = 'Driver={Unknown};Server=localhost;Database=myDB;'
        
        with pytest.raises(ValueError, match="Unsupported database type"):
            parser.connect_to_database()
    
    def test_extract_table_data(self, sample_dblib_file):
        """Test extracting data from a table."""
        parser = AltiumDbLibParser()
        config = parser.parse_dblib_file(sample_dblib_file)
        
        # Extract data from the Resistors table
        table_config = config['tables']['Resistors']
        table_data = parser.extract_table_data('Resistors', table_config)
        
        # Check that data was extracted
        assert len(table_data) == 3
        
        # Check the structure of the extracted data
        assert 'Part Number' in table_data[0]
        assert 'Symbol' in table_data[0]
        assert 'Footprint' in table_data[0]
        assert 'Description' in table_data[0]
        assert 'Value' in table_data[0]
        
        # Check specific values
        assert table_data[0]['Part Number'] == 'R-0603-10K'
        assert table_data[0]['Symbol'] == 'Resistor'
        assert table_data[0]['Footprint'] == '0603'
        assert table_data[0]['Description'] == '10k Ohm Resistor'
        assert table_data[0]['Value'] == '10k'
    
    def test_extract_all_data(self, sample_dblib_file):
        """Test extracting data from all tables."""
        parser = AltiumDbLibParser()
        config = parser.parse_dblib_file(sample_dblib_file)
        
        all_data = parser.extract_all_data(config)
        
        # Check that data was extracted from both tables
        assert 'Resistors' in all_data
        assert 'Capacitors' in all_data
        
        # Check the structure of the extracted data
        assert 'config' in all_data['Resistors']
        assert 'data' in all_data['Resistors']
        assert 'config' in all_data['Capacitors']
        assert 'data' in all_data['Capacitors']
        
        # Check the number of components extracted
        assert len(all_data['Resistors']['data']) == 3
        assert len(all_data['Capacitors']['data']) == 3
    
    def test_extract_table_data_with_error(self, sample_dblib_file):
        """Test error handling when extracting table data."""
        parser = AltiumDbLibParser()
        config = parser.parse_dblib_file(sample_dblib_file)
        
        # Try to extract data from a non-existent table
        table_config = config['tables']['Resistors']
        with pytest.raises(Exception):
            parser.extract_table_data('NonExistentTable', table_config)
    
    def test_extract_all_data_with_error(self, sample_dblib_file):
        """Test error handling when extracting all data."""
        parser = AltiumDbLibParser()
        config = parser.parse_dblib_file(sample_dblib_file)
        
        # Modify the config to include a non-existent table
        config['tables']['NonExistentTable'] = config['tables']['Resistors'].copy()
        
        all_data = parser.extract_all_data(config)
        
        # Check that data was extracted from valid tables
        assert 'Resistors' in all_data
        assert 'Capacitors' in all_data
        
        # Check that the error was handled for the non-existent table
        assert 'NonExistentTable' in all_data
        assert 'error' in all_data['NonExistentTable']
    
    def test_parse_table_config(self):
        """Test parsing table configuration."""
        parser = AltiumDbLibParser()
        
        table_info = {
            'Enabled': 'True',
            'Key': 'ID',
            'Symbols': 'Symbol',
            'Footprints': 'Footprint',
            'Description': 'Description',
            'UserWhereText': 'Value > 0',
            'Field1Name': 'Value',
            'Field2Name': 'Manufacturer'
        }
        
        table_config = parser._parse_table_config(table_info)
        
        # Check the parsed configuration
        assert table_config['enabled'] is True
        assert table_config['key_field'] == 'ID'
        assert table_config['symbol_field'] == 'Symbol'
        assert table_config['footprint_field'] == 'Footprint'
        assert table_config['description_field'] == 'Description'
        assert table_config['user_where'] == 'Value > 0'
        assert 'Value' in table_config['custom_fields']
        assert 'Manufacturer' in table_config['custom_fields']
    
    def test_extract_custom_fields(self):
        """Test extracting custom fields from table configuration."""
        parser = AltiumDbLibParser()
        
        table_info = {
            'Field1Name': 'Value',
            'Field2Name': 'Manufacturer',
            'Field3Name': 'Package',
            'OtherParam': 'SomeValue'
        }
        
        custom_fields = parser._extract_custom_fields(table_info)
        
        # Check the extracted custom fields
        assert 'Value' in custom_fields
        assert 'Manufacturer' in custom_fields
        assert 'Package' in custom_fields
        assert 'SomeValue' not in custom_fields
        assert len(custom_fields) == 3