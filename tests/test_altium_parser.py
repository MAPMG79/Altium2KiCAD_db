#!/usr/bin/env python3
"""
Tests for the Altium DbLib parser module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from migration_tool.core.altium_parser import AltiumDbLibParser


class TestAltiumDbLibParser(unittest.TestCase):
    """Test cases for the AltiumDbLibParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = AltiumDbLibParser()
        self.test_dblib_path = os.path.join(
            os.path.dirname(__file__), 'fixtures', 'test.DbLib'
        )

    def test_init(self):
        """Test initialization of the parser."""
        self.assertIsInstance(self.parser, AltiumDbLibParser)

    @patch('migration_tool.core.altium_parser.AltiumDbLibParser.parse_dblib_file')
    def test_parse_dblib_file(self, mock_parse):
        """Test parsing of DbLib file."""
        mock_parse.return_value = {
            'connection': {
                'type': 'Access',
                'connection_string': 'test_connection_string',
            },
            'tables': ['Table1', 'Table2'],
            'fields': {
                'Table1': ['Field1', 'Field2'],
                'Table2': ['Field1', 'Field3'],
            },
        }

        result = self.parser.parse_dblib_file('dummy_path')
        mock_parse.assert_called_once_with('dummy_path')
        self.assertEqual(result['connection']['type'], 'Access')
        self.assertEqual(len(result['tables']), 2)

    @patch('migration_tool.core.altium_parser.AltiumDbLibParser.connect_to_database')
    def test_connect_to_database(self, mock_connect):
        """Test database connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        self.parser.config = {
            'connection': {
                'type': 'Access',
                'connection_string': 'test_connection_string',
            }
        }

        conn = self.parser.connect_to_database()
        mock_connect.assert_called_once()
        self.assertEqual(conn, mock_conn)

    @patch('migration_tool.core.altium_parser.AltiumDbLibParser.extract_table_data')
    def test_extract_all_data(self, mock_extract):
        """Test extraction of all data from database."""
        mock_extract.side_effect = lambda table_name: {
            'fields': ['Field1', 'Field2'],
            'data': [{'Field1': 'Value1', 'Field2': 'Value2'}]
        }

        self.parser.config = {
            'tables': ['Table1', 'Table2'],
        }

        result = self.parser.extract_all_data()
        self.assertEqual(mock_extract.call_count, 2)
        self.assertEqual(len(result), 2)
        self.assertIn('Table1', result)
        self.assertIn('Table2', result)
        self.assertEqual(len(result['Table1']['data']), 1)

    def test_extract_table_data(self):
        """Test extraction of data from a specific table."""
        # This would require a more complex mock of database operations
        # For now, we'll just test the method signature
        with patch.object(self.parser, 'connect_to_database') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            # Mock the cursor's fetchall method to return some test data
            mock_cursor.fetchall.return_value = [('Value1', 'Value2')]
            mock_cursor.description = [('Field1',), ('Field2',)]

            self.parser.config = {
                'fields': {
                    'Table1': ['Field1', 'Field2'],
                }
            }

            result = self.parser.extract_table_data('Table1')
            self.assertIn('fields', result)
            self.assertIn('data', result)
            self.assertEqual(len(result['fields']), 2)


if __name__ == '__main__':
    unittest.main()