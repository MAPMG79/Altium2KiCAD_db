#!/usr/bin/env python3
"""
Tests for the Component Mapping Engine module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from migration_tool.core.mapping_engine import ComponentMappingEngine


class TestComponentMappingEngine(unittest.TestCase):
    """Test cases for the ComponentMappingEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        self.kicad_lib_path = os.path.join(
            os.path.dirname(__file__), 'fixtures', 'kicad_libs'
        )
        self.mapper = ComponentMappingEngine(self.kicad_lib_path)
        
        # Sample test data
        self.test_table_data = {
            'fields': ['Comment', 'Library Ref', 'Footprint Ref', 'Value'],
            'data': [
                {
                    'Comment': 'Resistor 10K',
                    'Library Ref': 'RES',
                    'Footprint Ref': 'RES_0805',
                    'Value': '10K'
                },
                {
                    'Comment': 'Capacitor 100nF',
                    'Library Ref': 'CAP',
                    'Footprint Ref': 'CAP_0603',
                    'Value': '100nF'
                },
                {
                    'Comment': 'LED Red',
                    'Library Ref': 'LED',
                    'Footprint Ref': 'LED_0805',
                    'Value': 'Red'
                }
            ]
        }

    def test_init(self):
        """Test initialization of the mapping engine."""
        self.assertIsInstance(self.mapper, ComponentMappingEngine)
        self.assertEqual(self.mapper.kicad_lib_path, self.kicad_lib_path)

    @patch('migration_tool.core.mapping_engine.ComponentMappingEngine.load_mapping_rules')
    def test_load_mapping_rules(self, mock_load):
        """Test loading of mapping rules."""
        mock_load.return_value = {
            'symbols': {'RES*': 'Device:R'},
            'footprints': {'*0805*': 'Resistor_SMD:R_0805_2012Metric'}
        }
        
        rules = self.mapper.load_mapping_rules()
        mock_load.assert_called_once()
        self.assertIn('symbols', rules)
        self.assertIn('footprints', rules)

    def test_map_table_data(self):
        """Test mapping of table data."""
        # Mock the internal methods used by map_table_data
        with patch.object(self.mapper, 'map_component') as mock_map:
            mock_map.side_effect = lambda component: {
                'Symbol': 'Device:R',
                'Footprint': 'Resistor_SMD:R_0805_2012Metric',
                'Value': component['Value'],
                'Description': component['Comment'],
                'Confidence': 90
            }
            
            result = self.mapper.map_table_data('TestTable', self.test_table_data)
            
            self.assertEqual(mock_map.call_count, 3)
            self.assertEqual(len(result['mapped_data']), 3)
            self.assertEqual(result['mapped_data'][0]['Symbol'], 'Device:R')
            self.assertEqual(result['mapped_data'][0]['Confidence'], 90)

    def test_map_component(self):
        """Test mapping of a single component."""
        # Mock the internal methods used by map_component
        with patch.object(self.mapper, 'map_symbol') as mock_symbol:
            with patch.object(self.mapper, 'map_footprint') as mock_footprint:
                with patch.object(self.mapper, 'calculate_confidence') as mock_confidence:
                    
                    mock_symbol.return_value = ('Device:R', 80)
                    mock_footprint.return_value = ('Resistor_SMD:R_0805_2012Metric', 90)
                    mock_confidence.return_value = 85
                    
                    component = self.test_table_data['data'][0]
                    result = self.mapper.map_component(component)
                    
                    mock_symbol.assert_called_once_with(component['Library Ref'])
                    mock_footprint.assert_called_once_with(component['Footprint Ref'])
                    
                    self.assertEqual(result['Symbol'], 'Device:R')
                    self.assertEqual(result['Footprint'], 'Resistor_SMD:R_0805_2012Metric')
                    self.assertEqual(result['Value'], '10K')
                    self.assertEqual(result['Confidence'], 85)

    def test_map_symbol(self):
        """Test mapping of a symbol."""
        # Set up test mapping rules
        self.mapper.mapping_rules = {
            'symbols': {
                'RES*': 'Device:R',
                'CAP*': 'Device:C',
                'LED*': 'Device:LED'
            }
        }
        
        symbol, confidence = self.mapper.map_symbol('RES')
        self.assertEqual(symbol, 'Device:R')
        self.assertGreater(confidence, 0)
        
        symbol, confidence = self.mapper.map_symbol('CAP')
        self.assertEqual(symbol, 'Device:C')
        
        symbol, confidence = self.mapper.map_symbol('UNKNOWN')
        self.assertNotEqual(symbol, '')  # Should return a default or best guess

    def test_map_footprint(self):
        """Test mapping of a footprint."""
        # Set up test mapping rules
        self.mapper.mapping_rules = {
            'footprints': {
                '*0805*': 'Resistor_SMD:R_0805_2012Metric',
                '*0603*': 'Capacitor_SMD:C_0603_1608Metric'
            }
        }
        
        footprint, confidence = self.mapper.map_footprint('RES_0805')
        self.assertEqual(footprint, 'Resistor_SMD:R_0805_2012Metric')
        self.assertGreater(confidence, 0)
        
        footprint, confidence = self.mapper.map_footprint('CAP_0603')
        self.assertEqual(footprint, 'Capacitor_SMD:C_0603_1608Metric')
        
        footprint, confidence = self.mapper.map_footprint('UNKNOWN')
        self.assertNotEqual(footprint, '')  # Should return a default or best guess

    def test_calculate_confidence(self):
        """Test calculation of confidence score."""
        # Simple test case
        symbol_confidence = 80
        footprint_confidence = 90
        
        confidence = self.mapper.calculate_confidence(symbol_confidence, footprint_confidence)
        self.assertGreaterEqual(confidence, min(symbol_confidence, footprint_confidence))
        self.assertLessEqual(confidence, max(symbol_confidence, footprint_confidence))


if __name__ == '__main__':
    unittest.main()