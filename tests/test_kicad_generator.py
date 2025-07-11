#!/usr/bin/env python3
"""
Tests for the KiCAD Database Library Generator module.
"""

import os
import unittest
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

from migration_tool.core.kicad_generator import KiCADDbLibGenerator


class TestKiCADDbLibGenerator(unittest.TestCase):
    """Test cases for the KiCADDbLibGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
        
        self.generator = KiCADDbLibGenerator(self.output_dir)
        
        # Sample test data
        self.test_mapping_data = {
            'Table1': {
                'table_name': 'Table1',
                'fields': ['Symbol', 'Footprint', 'Value', 'Description', 'Datasheet'],
                'mapped_data': [
                    {
                        'Symbol': 'Device:R',
                        'Footprint': 'Resistor_SMD:R_0805_2012Metric',
                        'Value': '10K',
                        'Description': 'Resistor 10K',
                        'Datasheet': 'http://example.com/datasheet.pdf',
                        'Confidence': 90
                    },
                    {
                        'Symbol': 'Device:C',
                        'Footprint': 'Capacitor_SMD:C_0603_1608Metric',
                        'Value': '100nF',
                        'Description': 'Capacitor 100nF',
                        'Datasheet': 'http://example.com/datasheet2.pdf',
                        'Confidence': 85
                    }
                ]
            },
            'Table2': {
                'table_name': 'Table2',
                'fields': ['Symbol', 'Footprint', 'Value', 'Description'],
                'mapped_data': [
                    {
                        'Symbol': 'Device:LED',
                        'Footprint': 'LED_SMD:LED_0805_2012Metric',
                        'Value': 'Red',
                        'Description': 'LED Red',
                        'Confidence': 95
                    }
                ]
            }
        }

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of the generator."""
        self.assertIsInstance(self.generator, KiCADDbLibGenerator)
        self.assertEqual(self.generator.output_dir, self.output_dir)

    @patch('migration_tool.core.kicad_generator.KiCADDbLibGenerator.create_database')
    def test_generate(self, mock_create_db):
        """Test generation of KiCAD database library."""
        mock_create_db.return_value = os.path.join(self.output_dir, 'library.db')
        
        with patch.object(self.generator, 'create_dblib_file') as mock_create_dblib:
            mock_create_dblib.return_value = os.path.join(self.output_dir, 'library.kicad_dbl')
            
            with patch.object(self.generator, 'generate_report') as mock_report:
                mock_report.return_value = os.path.join(self.output_dir, 'migration_report.json')
                
                result = self.generator.generate(self.test_mapping_data)
                
                mock_create_db.assert_called_once_with(self.test_mapping_data)
                mock_create_dblib.assert_called_once()
                mock_report.assert_called_once()
                
                self.assertIn('database_path', result)
                self.assertIn('dblib_path', result)
                self.assertIn('report_path', result)

    def test_create_database(self):
        """Test creation of SQLite database."""
        # This test will actually create a temporary database
        db_path = self.generator.create_database(self.test_mapping_data)
        
        self.assertTrue(os.path.exists(db_path))
        
        # Verify database structure and content
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        # Should have a components table and possibly category views
        self.assertIn('components', table_names)
        
        # Check if components were inserted
        cursor.execute("SELECT COUNT(*) FROM components")
        count = cursor.fetchone()[0]
        
        # We had 3 components in our test data
        self.assertEqual(count, 3)
        
        conn.close()

    def test_create_dblib_file(self):
        """Test creation of KiCAD database library file."""
        # Mock the database path
        db_path = os.path.join(self.output_dir, 'library.db')
        
        # Create an empty file to simulate the database
        with open(db_path, 'w') as f:
            f.write('')
        
        dblib_path = self.generator.create_dblib_file(db_path)
        
        self.assertTrue(os.path.exists(dblib_path))
        
        # Check file extension
        self.assertTrue(dblib_path.endswith('.kicad_dbl'))
        
        # Read file content to verify structure
        with open(dblib_path, 'r') as f:
            content = f.read()
            
            # Basic checks for expected content
            self.assertIn('kicad_dbl', content.lower())
            self.assertIn('sqlite', content.lower())

    def test_generate_report(self):
        """Test generation of migration report."""
        report_path = self.generator.generate_report(self.test_mapping_data)
        
        self.assertTrue(os.path.exists(report_path))
        
        # Check file extension
        self.assertTrue(report_path.endswith('.json'))
        
        # Read file content to verify structure
        import json
        with open(report_path, 'r') as f:
            report = json.load(f)
            
            # Basic checks for expected content
            self.assertIn('migration_summary', report)
            self.assertIn('table_details', report)
            
            # Check component counts
            self.assertEqual(report['migration_summary']['total_components'], 3)


if __name__ == '__main__':
    unittest.main()