import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class ComponentMapping:
    """Data class for component mapping information"""
    altium_symbol: str
    altium_footprint: str
    kicad_symbol: str
    kicad_footprint: str
    confidence: float
    field_mappings: Dict[str, str]

class ComponentMappingEngine:
    """Engine for mapping Altium components to KiCAD equivalents"""
    
    def __init__(self, kicad_library_path: str = None):
        self.kicad_library_path = kicad_library_path or self._find_kicad_libraries()
        self.symbol_mappings = {}
        self.footprint_mappings = {}
        self.field_mappings = self._default_field_mappings()
        self.component_type_mappings = self._load_component_type_mappings()
        
    def _find_kicad_libraries(self) -> str:
        """Attempt to find KiCAD library installation"""
        possible_paths = [
            "/usr/share/kicad/symbols",
            "/usr/local/share/kicad/symbols", 
            "C:/Program Files/KiCad/*/share/kicad/symbols",
            "C:/KiCad/*/share/kicad/symbols"
        ]
        
        for path_pattern in possible_paths:
            if '*' in path_pattern:
                # Handle wildcard paths
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    return str(Path(matches[0]).parent)
            else:
                if Path(path_pattern).exists():
                    return str(Path(path_pattern).parent)
        
        return ""  # Return empty if not found
    
    def _default_field_mappings(self) -> Dict[str, str]:
        """Default field name mappings from Altium to KiCAD"""
        return {
            # Altium field -> KiCAD field
            'Part Number': 'MPN',
            'Manufacturer': 'Manufacturer',
            'Manufacturer Part Number': 'MPN',
            'Description': 'Description',
            'Value': 'Value',
            'Footprint': 'Footprint',
            'Datasheet': 'Datasheet',
            'Supplier': 'Supplier',
            'Supplier Part Number': 'SPN',
            'Package': 'Package',
            'Voltage': 'Voltage',
            'Current': 'Current',
            'Power': 'Power',
            'Tolerance': 'Tolerance',
            'Temperature': 'Temperature'
        }
    
    def _load_component_type_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load component type specific mappings"""
        return {
            'resistors': {
                'altium_library': 'Resistors',
                'kicad_symbol': 'Device:R',
                'symbol_patterns': [r'.*resistor.*', r'.*res.*'],
                'common_footprints': {
                    '0201': 'Resistor_SMD:R_0201_0603Metric',
                    '0402': 'Resistor_SMD:R_0402_1005Metric', 
                    '0603': 'Resistor_SMD:R_0603_1608Metric',
                    '0805': 'Resistor_SMD:R_0805_2012Metric',
                    '1206': 'Resistor_SMD:R_1206_3216Metric'
                }
            },
            'capacitors': {
                'altium_library': 'Capacitors',
                'kicad_symbol': 'Device:C',
                'symbol_patterns': [r'.*capacitor.*', r'.*cap.*'],
                'common_footprints': {
                    '0201': 'Capacitor_SMD:C_0201_0603Metric',
                    '0402': 'Capacitor_SMD:C_0402_1005Metric',
                    '0603': 'Capacitor_SMD:C_0603_1608Metric', 
                    '0805': 'Capacitor_SMD:C_0805_2012Metric',
                    '1206': 'Capacitor_SMD:C_1206_3216Metric'
                }
            }
        }
    
    def map_component(self, altium_data: Dict[str, Any], table_config: Dict[str, Any]) -> ComponentMapping:
        """Map a single Altium component to KiCAD format"""
        # Extract symbol and footprint references
        symbol_field = table_config.get('symbol_field', 'Symbol')
        footprint_field = table_config.get('footprint_field', 'Footprint')
        
        altium_symbol = altium_data.get(symbol_field, '')
        altium_footprint = altium_data.get(footprint_field, '')
        
        # Map to KiCAD equivalents
        kicad_symbol = self.map_symbol(altium_symbol, altium_data)
        kicad_footprint = self.map_footprint(altium_footprint, altium_data)
        
        # Map fields
        mapped_fields = self.map_fields(altium_data)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(
            altium_symbol, kicad_symbol, 
            altium_footprint, kicad_footprint,
            altium_data
        )
        
        return ComponentMapping(
            altium_symbol=altium_symbol,
            altium_footprint=altium_footprint,
            kicad_symbol=kicad_symbol,
            kicad_footprint=kicad_footprint,
            confidence=confidence,
            field_mappings=mapped_fields
        )
    
    def map_symbol(self, altium_symbol: str, component_data: Dict[str, Any]) -> str:
        """Map Altium symbol to KiCAD symbol"""
        # Direct mapping check
        if altium_symbol in self.symbol_mappings:
            return self.symbol_mappings[altium_symbol]
        
        # Component type-based mapping
        description = component_data.get('Description', '').lower()
        value = component_data.get('Value', '').lower()
        
        for comp_type, mapping in self.component_type_mappings.items():
            for pattern in mapping.get('symbol_patterns', []):
                if re.search(pattern, description) or re.search(pattern, value):
                    kicad_symbol = mapping['kicad_symbol']
                    # Cache the mapping
                    self.symbol_mappings[altium_symbol] = kicad_symbol
                    return kicad_symbol
        
        # Fallback: try to find similar KiCAD symbol
        return self._find_similar_symbol(altium_symbol, component_data)
    
    def _find_similar_symbol(self, altium_symbol: str, component_data: Dict[str, Any]) -> str:
        """Find similar KiCAD symbol using fuzzy matching"""
        # This would require scanning KiCAD symbol libraries
        # For now, return a generic symbol based on description
        description = component_data.get('Description', '').lower()
        
        if any(word in description for word in ['resistor', 'res']):
            return 'Device:R'
        elif any(word in description for word in ['capacitor', 'cap']):
            return 'Device:C'
        elif any(word in description for word in ['inductor', 'ind']):
            return 'Device:L'
        elif any(word in description for word in ['diode']):
            return 'Device:D'
        elif any(word in description for word in ['transistor', 'fet', 'mosfet']):
            return 'Device:Q_NMOS_GSD'
        else:
            return 'Device:R'  # Default fallback