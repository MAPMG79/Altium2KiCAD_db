"""
Unit tests for the Component Mapping Engine module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from migration_tool.core.mapping_engine import ComponentMappingEngine, ComponentMapping


class TestComponentMappingEngine:
    """Test cases for the ComponentMappingEngine class."""

    def test_initialization(self):
        """Test initialization of the mapping engine."""
        # Test with default parameters
        mapper = ComponentMappingEngine()
        assert mapper.kicad_library_path is not None
        assert isinstance(mapper.symbol_mappings, dict)
        assert isinstance(mapper.footprint_mappings, dict)
        assert isinstance(mapper.field_mappings, dict)
        assert isinstance(mapper.component_type_mappings, dict)
        
        # Test with custom library path
        custom_path = "/custom/path"
        mapper = ComponentMappingEngine(custom_path)
        assert mapper.kicad_library_path == custom_path
    
    def test_find_kicad_libraries(self):
        """Test finding KiCAD libraries."""
        with patch('os.path.exists', return_value=True):
            mapper = ComponentMappingEngine()
            path = mapper._find_kicad_libraries()
            assert path != ""
    
    def test_default_field_mappings(self):
        """Test default field mappings."""
        mapper = ComponentMappingEngine()
        field_mappings = mapper._default_field_mappings()
        
        # Check that common fields are mapped
        assert 'Part Number' in field_mappings
        assert 'Manufacturer' in field_mappings
        assert 'Description' in field_mappings
        assert 'Value' in field_mappings
        assert 'Footprint' in field_mappings
        
        # Check specific mappings
        assert field_mappings['Part Number'] == 'MPN'
        assert field_mappings['Manufacturer'] == 'Manufacturer'
        assert field_mappings['Description'] == 'Description'
        assert field_mappings['Value'] == 'Value'
    
    def test_load_component_type_mappings(self):
        """Test loading component type mappings."""
        mapper = ComponentMappingEngine()
        type_mappings = mapper._load_component_type_mappings()
        
        # Check that common component types are mapped
        assert 'resistors' in type_mappings
        assert 'capacitors' in type_mappings
        assert 'inductors' in type_mappings
        assert 'diodes' in type_mappings
        
        # Check resistor mappings
        resistors = type_mappings['resistors']
        assert resistors['kicad_symbol'] == 'Device:R'
        assert 'common_footprints' in resistors
        assert '0603' in resistors['common_footprints']
        assert resistors['common_footprints']['0603'] == 'Resistor_SMD:R_0603_1608Metric'
    
    def test_map_symbol_direct_mapping(self):
        """Test mapping a symbol with direct mapping."""
        mapper = ComponentMappingEngine()
        
        # Add a direct mapping
        mapper.symbol_mappings['TestSymbol'] = 'Test:Symbol'
        
        # Test the mapping
        component_data = {'Description': 'Test component'}
        result = mapper.map_symbol('TestSymbol', component_data)
        
        assert result == 'Test:Symbol'
    
    def test_map_symbol_component_type(self):
        """Test mapping a symbol based on component type."""
        mapper = ComponentMappingEngine()
        
        # Test with a resistor description
        component_data = {'Description': 'A 10k resistor', 'Value': '10k'}
        result = mapper.map_symbol('Unknown', component_data)
        
        assert result == 'Device:R'
        
        # Test with a capacitor description
        component_data = {'Description': 'A 100nF capacitor', 'Value': '100nF'}
        result = mapper.map_symbol('Unknown', component_data)
        
        assert result == 'Device:C'
    
    def test_map_symbol_fallback(self):
        """Test symbol mapping fallback."""
        mapper = ComponentMappingEngine()
        
        # Test with an unknown component
        component_data = {'Description': 'Unknown component'}
        result = mapper.map_symbol('Unknown', component_data)
        
        # Should fall back to a generic symbol
        assert result is not None
        assert result.startswith('Device:')
    
    def test_map_footprint_direct_mapping(self):
        """Test mapping a footprint with direct mapping."""
        mapper = ComponentMappingEngine()
        
        # Add a direct mapping
        mapper.footprint_mappings['TestFootprint'] = 'Test:Footprint'
        
        # Test the mapping
        component_data = {'Description': 'Test component'}
        result = mapper.map_footprint('TestFootprint', component_data)
        
        assert result == 'Test:Footprint'
    
    def test_map_footprint_package_extraction(self):
        """Test footprint mapping with package extraction."""
        mapper = ComponentMappingEngine()
        
        # Test with a resistor with package information
        component_data = {
            'Description': 'A 10k resistor',
            'Value': '10k',
            'Package': '0603'
        }
        result = mapper.map_footprint('Unknown', component_data)
        
        assert 'Resistor_SMD:R_0603' in result
        
        # Test with a capacitor with package information
        component_data = {
            'Description': 'A 100nF capacitor',
            'Value': '100nF',
            'Package': '0805'
        }
        result = mapper.map_footprint('Unknown', component_data)
        
        assert 'Capacitor_SMD:C_0805' in result
    
    def test_extract_package_size(self):
        """Test extracting package size from component data."""
        mapper = ComponentMappingEngine()
        
        # Test with package in footprint
        footprint = '0603'
        component_data = {'Description': 'Test component'}
        result = mapper._extract_package_size(footprint, component_data)
        
        assert result == '0603'
        
        # Test with package in component data
        footprint = 'Unknown'
        component_data = {'Package': '0805'}
        result = mapper._extract_package_size(footprint, component_data)
        
        assert result == '0805'
        
        # Test with package in description
        footprint = 'Unknown'
        component_data = {'Description': 'A component in SOT-23 package'}
        result = mapper._extract_package_size(footprint, component_data)
        
        assert result == 'SOT-23'
    
    def test_find_similar_symbol(self):
        """Test finding similar symbols."""
        mapper = ComponentMappingEngine()
        
        # Test with resistor description
        component_data = {'Description': 'A 10k resistor'}
        result = mapper._find_similar_symbol('Unknown', component_data)
        
        assert result == 'Device:R'
        
        # Test with capacitor description
        component_data = {'Description': 'A 100nF capacitor'}
        result = mapper._find_similar_symbol('Unknown', component_data)
        
        assert result == 'Device:C'
        
        # Test with inductor description
        component_data = {'Description': 'A 10uH inductor'}
        result = mapper._find_similar_symbol('Unknown', component_data)
        
        assert result == 'Device:L'
        
        # Test with diode description
        component_data = {'Description': 'A diode'}
        result = mapper._find_similar_symbol('Unknown', component_data)
        
        assert result == 'Device:D'
        
        # Test with transistor description
        component_data = {'Description': 'A transistor'}
        result = mapper._find_similar_symbol('Unknown', component_data)
        
        assert result == 'Device:Q_NMOS_GSD'
    
    def test_find_similar_footprint(self):
        """Test finding similar footprints."""
        mapper = ComponentMappingEngine()
        
        # Test with resistor description and package
        component_data = {
            'Description': 'A 10k resistor',
            'Package': '0603'
        }
        result = mapper._find_similar_footprint('Unknown', component_data)
        
        assert 'Resistor_SMD:R_0603' in result
        
        # Test with capacitor description and package
        component_data = {
            'Description': 'A 100nF capacitor',
            'Package': '0805'
        }
        result = mapper._find_similar_footprint('Unknown', component_data)
        
        assert 'Capacitor_SMD:C_0805' in result
        
        # Test with unknown component
        component_data = {'Description': 'Unknown component'}
        result = mapper._find_similar_footprint('Unknown', component_data)
        
        # Should fall back to a generic footprint
        assert result is not None
        assert 'Package_TO_SOT_SMD:SOT-23' in result
    
    def test_map_fields(self):
        """Test mapping component fields."""
        mapper = ComponentMappingEngine()
        
        # Test with various fields
        altium_data = {
            'Part Number': 'R-0603-10K',
            'Manufacturer': 'Generic',
            'Description': 'A 10k resistor',
            'Value': '10k',
            'Tolerance': '1%',
            'Power': '0.1W',
            'Datasheet': 'http://example.com/datasheet.pdf'
        }
        
        result = mapper.map_fields(altium_data)
        
        # Check that fields were mapped correctly
        assert 'MPN' in result
        assert 'Manufacturer' in result
        assert 'Description' in result
        assert 'Value' in result
        assert 'Tolerance' in result
        assert 'Power' in result
        assert 'Datasheet' in result
        
        # Check specific values
        assert result['MPN'] == 'R-0603-10K'
        assert result['Manufacturer'] == 'Generic'
        assert result['Description'] == 'A 10k resistor'
        assert result['Value'] == '10k'
    
    def test_handle_special_field_mappings(self):
        """Test handling special field mappings."""
        mapper = ComponentMappingEngine()
        
        # Test combining manufacturer and MPN
        mapped_fields = {
            'Manufacturer': 'Generic',
            'MPN': 'R-0603-10K'
        }
        
        result = mapper._handle_special_field_mappings({}, mapped_fields)
        
        assert 'Manufacturer_MPN' in result
        assert result['Manufacturer_MPN'] == 'Generic R-0603-10K'
        
        # Test creating reference from description
        mapped_fields = {
            'Description': 'A 10k resistor'
        }
        
        result = mapper._handle_special_field_mappings({}, mapped_fields)
        
        assert 'Reference' in result
        assert result['Reference'] == 'R'
        
        # Test with capacitor description
        mapped_fields = {
            'Description': 'A 100nF capacitor'
        }
        
        result = mapper._handle_special_field_mappings({}, mapped_fields)
        
        assert 'Reference' in result
        assert result['Reference'] == 'C'
    
    def test_map_component(self):
        """Test mapping a complete component."""
        mapper = ComponentMappingEngine()
        
        # Test with a resistor
        altium_data = {
            'Part Number': 'R-0603-10K',
            'Symbol': 'Resistor',
            'Footprint': '0603',
            'Description': 'A 10k resistor',
            'Value': '10k',
            'Manufacturer': 'Generic',
            'Tolerance': '1%',
            'Power': '0.1W'
        }
        
        table_config = {
            'symbol_field': 'Symbol',
            'footprint_field': 'Footprint'
        }
        
        result = mapper.map_component(altium_data, table_config)
        
        # Check the mapping result
        assert isinstance(result, ComponentMapping)
        assert result.altium_symbol == 'Resistor'
        assert result.altium_footprint == '0603'
        assert result.kicad_symbol == 'Device:R'
        assert 'Resistor_SMD:R_0603' in result.kicad_footprint
        assert result.confidence > 0
        assert 'Description' in result.field_mappings
        assert 'Value' in result.field_mappings
        assert 'Manufacturer' in result.field_mappings
        assert 'Tolerance' in result.field_mappings
        assert 'Power' in result.field_mappings
    
    def test_calculate_confidence(self):
        """Test calculating confidence score for mapping."""
        mapper = ComponentMappingEngine()
        
        # Test with direct symbol and footprint mappings
        mapper.symbol_mappings['Resistor'] = 'Device:R'
        mapper.footprint_mappings['0603'] = 'Resistor_SMD:R_0603_1608Metric'
        
        component_data = {
            'Description': 'A 10k resistor',
            'Value': '10k',
            'Package': '0603'
        }
        
        confidence = mapper._calculate_confidence(
            'Resistor', 'Device:R',
            '0603', 'Resistor_SMD:R_0603_1608Metric',
            component_data
        )
        
        # Should have high confidence with direct mappings
        assert confidence > 0.8
        
        # Test with fuzzy matching
        confidence = mapper._calculate_confidence(
            'Unknown', 'Device:R',
            'Unknown', 'Resistor_SMD:R_0603_1608Metric',
            component_data
        )
        
        # Should have lower confidence with fuzzy matching
        assert confidence < 0.8
    
    def test_map_table_data(self):
        """Test mapping all components in a table."""
        mapper = ComponentMappingEngine()
        
        # Create sample table data
        table_data = {
            'config': {
                'symbol_field': 'Symbol',
                'footprint_field': 'Footprint'
            },
            'data': [
                {
                    'Part Number': 'R-0603-10K',
                    'Symbol': 'Resistor',
                    'Footprint': '0603',
                    'Description': 'A 10k resistor',
                    'Value': '10k'
                },
                {
                    'Part Number': 'C-0805-100N',
                    'Symbol': 'Capacitor',
                    'Footprint': '0805',
                    'Description': 'A 100nF capacitor',
                    'Value': '100nF'
                }
            ]
        }
        
        result = mapper.map_table_data('TestTable', table_data)
        
        # Check the mapping results
        assert len(result) == 2
        assert isinstance(result[0], ComponentMapping)
        assert isinstance(result[1], ComponentMapping)
        
        # Check resistor mapping
        resistor = result[0]
        assert resistor.altium_symbol == 'Resistor'
        assert resistor.altium_footprint == '0603'
        assert resistor.kicad_symbol == 'Device:R'
        assert 'Resistor_SMD:R_0603' in resistor.kicad_footprint
        
        # Check capacitor mapping
        capacitor = result[1]
        assert capacitor.altium_symbol == 'Capacitor'
        assert capacitor.altium_footprint == '0805'
        assert capacitor.kicad_symbol == 'Device:C'
        assert 'Capacitor_SMD:C_0805' in capacitor.kicad_footprint
    
    def test_map_table_data_with_error(self):
        """Test error handling when mapping table data."""
        mapper = ComponentMappingEngine()
        
        # Create sample table data with a problematic component
        table_data = {
            'config': {
                'symbol_field': 'Symbol',
                'footprint_field': 'Footprint'
            },
            'data': [
                {
                    'Part Number': 'R-0603-10K',
                    'Symbol': 'Resistor',
                    'Footprint': '0603',
                    'Description': 'A 10k resistor',
                    'Value': '10k'
                },
                {
                    # Missing required fields
                    'Part Number': 'PROBLEM-COMPONENT'
                }
            ]
        }
        
        # Mock the map_component method to raise an exception for the problematic component
        original_map_component = mapper.map_component
        
        def mock_map_component(component_data, table_config):
            if component_data.get('Part Number') == 'PROBLEM-COMPONENT':
                raise ValueError("Missing required fields")
            return original_map_component(component_data, table_config)
        
        mapper.map_component = mock_map_component
        
        result = mapper.map_table_data('TestTable', table_data)
        
        # Check that both components were processed
        assert len(result) == 2
        
        # Check that the first component was mapped correctly
        assert result[0].altium_symbol == 'Resistor'
        assert result[0].kicad_symbol == 'Device:R'
        
        # Check that the second component has fallback values
        assert result[1].confidence == 0.0
        assert result[1].kicad_symbol == 'Device:R'  # Fallback symbol