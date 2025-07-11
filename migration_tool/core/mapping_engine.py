"""
Component mapping engine for Altium to KiCAD migration.

This module provides functionality to map Altium components to KiCAD equivalents
using various mapping strategies.
"""

import re
import json
import os
import yaml
import glob
import fnmatch
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from difflib import SequenceMatcher

from migration_tool.utils.logging_utils import get_logger


class MappingError(Exception):
    """Base exception for mapping errors."""
    pass


class SymbolMappingError(MappingError):
    """Exception raised when symbol mapping fails."""
    pass


class FootprintMappingError(MappingError):
    """Exception raised when footprint mapping fails."""
    pass


class ConfigurationError(MappingError):
    """Exception raised when configuration is invalid."""
    pass


@dataclass
class ComponentMapping:
    """Data class for component mapping information."""
    altium_symbol: str
    altium_footprint: str
    kicad_symbol: str
    kicad_footprint: str
    confidence: float
    field_mappings: Dict[str, str]
    category: str = "Uncategorized"
    subcategory: str = "General"
    keywords: List[str] = None

    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.keywords is None:
            self.keywords = []


class ComponentMappingEngine:
    """Engine for mapping Altium components to KiCAD equivalents."""
    
    def __init__(self, kicad_library_path: str = None, config_manager=None):
        """
        Initialize the mapping engine.
        
        Args:
            kicad_library_path: Path to KiCAD libraries
            config_manager: Optional configuration manager instance
        """
        self.logger = get_logger("core.mapping_engine")
        self.config = config_manager
        self.kicad_library_path = kicad_library_path or self._find_kicad_libraries()
        self.symbol_mappings = {}
        self.footprint_mappings = {}
        self.field_mappings = self._default_field_mappings()
        self.component_type_mappings = self._load_component_type_mappings()
        self.category_mappings = []
        
        self.logger.info(f"Initialized ComponentMappingEngine with KiCAD library path: {self.kicad_library_path}")
        
        # Load custom mappings from configuration if available
        self._load_custom_mappings()
    
    def _find_kicad_libraries(self) -> str:
        """
        Attempt to find KiCAD library installation.
        
        Returns:
            Path to KiCAD libraries or empty string if not found
        """
        possible_paths = [
            "/usr/share/kicad/symbols",
            "/usr/local/share/kicad/symbols", 
            "C:/Program Files/KiCad/*/share/kicad/symbols",
            "C:/KiCad/*/share/kicad/symbols",
            os.path.expanduser("~/.kicad/symbols"),
            os.path.expanduser("~/Library/Application Support/kicad/symbols")
        ]
        
        # Check if config has KiCAD library paths
        if self.config and self.config.get('kicad_symbol_libraries'):
            kicad_paths = self.config.get('kicad_symbol_libraries')
            if isinstance(kicad_paths, list) and kicad_paths:
                self.logger.info(f"Using KiCAD library path from config: {kicad_paths[0]}")
                return kicad_paths[0]
        
        for path_pattern in possible_paths:
            if '*' in path_pattern:
                # Handle wildcard paths
                matches = glob.glob(path_pattern)
                if matches:
                    self.logger.info(f"Found KiCAD library at: {matches[0]}")
                    return str(Path(matches[0]).parent)
            else:
                if os.path.exists(path_pattern):
                    self.logger.info(f"Found KiCAD library at: {path_pattern}")
                    return str(Path(path_pattern).parent)
        
        self.logger.warning("KiCAD library not found, using default mappings only")
        return ""  # Return empty if not found
    
    def _load_custom_mappings(self):
        """Load custom mappings from configuration files."""
        # Load symbol mappings
        if self.config and self.config.get('symbol_mapping_file'):
            symbol_file = self.config.get('symbol_mapping_file')
            if os.path.exists(symbol_file):
                try:
                    with open(symbol_file, 'r') as f:
                        if symbol_file.endswith('.yaml') or symbol_file.endswith('.yml'):
                            custom_symbols = yaml.safe_load(f)
                        else:
                            custom_symbols = json.load(f)
                        
                        if isinstance(custom_symbols, dict):
                            self.symbol_mappings.update(custom_symbols)
                            self.logger.info(f"Loaded {len(custom_symbols)} custom symbol mappings")
                except Exception as e:
                    self.logger.error(f"Error loading custom symbol mappings: {str(e)}")
        
        # Load footprint mappings
        if self.config and self.config.get('footprint_mapping_file'):
            footprint_file = self.config.get('footprint_mapping_file')
            if os.path.exists(footprint_file):
                try:
                    with open(footprint_file, 'r') as f:
                        if footprint_file.endswith('.yaml') or footprint_file.endswith('.yml'):
                            custom_footprints = yaml.safe_load(f)
                        else:
                            custom_footprints = json.load(f)
                        
                        if isinstance(custom_footprints, dict):
                            self.footprint_mappings.update(custom_footprints)
                            self.logger.info(f"Loaded {len(custom_footprints)} custom footprint mappings")
                except Exception as e:
                    self.logger.error(f"Error loading custom footprint mappings: {str(e)}")
        
        # Load category mappings
        if self.config and self.config.get('category_mapping_file'):
            category_file = self.config.get('category_mapping_file')
            if os.path.exists(category_file):
                try:
                    with open(category_file, 'r') as f:
                        if category_file.endswith('.yaml') or category_file.endswith('.yml'):
                            self.category_mappings = yaml.safe_load(f)
                        else:
                            self.category_mappings = json.load(f)
                        
                        if isinstance(self.category_mappings, list):
                            self.logger.info(f"Loaded {len(self.category_mappings)} category mapping rules")
                except Exception as e:
                    self.logger.error(f"Error loading category mappings: {str(e)}")
    
    def _default_field_mappings(self) -> Dict[str, str]:
        """
        Default field name mappings from Altium to KiCAD.
        
        Returns:
            Dictionary mapping Altium field names to KiCAD field names
        """
        default_mappings = {
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
            'Temperature': 'Temperature',
            'Library Name': 'Library',
            'Comment': 'Comment',
            'ComponentLink1Description': 'Link1_Desc',
            'ComponentLink1URL': 'Link1_URL',
            'ComponentLink2Description': 'Link2_Desc', 
            'ComponentLink2URL': 'Link2_URL'
        }
        
        # Override with config if available
        if self.config and self.config.get('field_mappings'):
            config_mappings = self.config.get('field_mappings')
            if isinstance(config_mappings, dict):
                default_mappings.update(config_mappings)
                self.logger.info(f"Updated field mappings from config")
        
        return default_mappings
    
    def _load_component_type_mappings(self) -> Dict[str, Dict[str, Any]]:
        """
        Load component type specific mappings.
        
        Returns:
            Dictionary of component type mappings
        """
        # Try to load from config file first
        if self.config and self.config.get('component_type_mapping_file'):
            mapping_file = self.config.get('component_type_mapping_file')
            if os.path.exists(mapping_file):
                try:
                    with open(mapping_file, 'r') as f:
                        if mapping_file.endswith('.yaml') or mapping_file.endswith('.yml'):
                            mappings = yaml.safe_load(f)
                        else:
                            mappings = json.load(f)
                        
                        if isinstance(mappings, dict):
                            self.logger.info(f"Loaded component type mappings from {mapping_file}")
                            return mappings
                except Exception as e:
                    self.logger.error(f"Error loading component type mappings: {str(e)}")
        
        # Default mappings
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
                    '1206': 'Resistor_SMD:R_1206_3216Metric',
                    '1210': 'Resistor_SMD:R_1210_3225Metric',
                    '2010': 'Resistor_SMD:R_2010_5025Metric',
                    '2512': 'Resistor_SMD:R_2512_6332Metric'
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
                    '1206': 'Capacitor_SMD:C_1206_3216Metric',
                    '1210': 'Capacitor_SMD:C_1210_3225Metric',
                    '1812': 'Capacitor_SMD:C_1812_4532Metric',
                    '2220': 'Capacitor_SMD:C_2220_5650Metric'
                }
            },
            'inductors': {
                'altium_library': 'Inductors',
                'kicad_symbol': 'Device:L',
                'symbol_patterns': [r'.*inductor.*', r'.*ind.*'],
                'common_footprints': {
                    '0603': 'Inductor_SMD:L_0603_1608Metric',
                    '0805': 'Inductor_SMD:L_0805_2012Metric',
                    '1206': 'Inductor_SMD:L_1206_3216Metric',
                    '1210': 'Inductor_SMD:L_1210_3225Metric',
                    '1812': 'Inductor_SMD:L_1812_4532Metric',
                    '2220': 'Inductor_SMD:L_2220_5650Metric'
                }
            },
            'diodes': {
                'altium_library': 'Diodes',
                'kicad_symbol': 'Device:D',
                'symbol_patterns': [r'.*diode.*'],
                'common_footprints': {
                    'SOD-123': 'Diode_SMD:D_SOD-123',
                    'SOD-323': 'Diode_SMD:D_SOD-323',
                    'SOD-523': 'Diode_SMD:D_SOD-523',
                    'SMA': 'Diode_SMD:D_SMA',
                    'SMB': 'Diode_SMD:D_SMB',
                    'SMC': 'Diode_SMD:D_SMC'
                }
            },
            'transistors': {
                'altium_library': 'Transistors',
                'kicad_symbol': 'Device:Q_NPN_BCE',
                'symbol_patterns': [r'.*transistor.*', r'.*mosfet.*', r'.*fet.*', r'.*bjt.*'],
                'common_footprints': {
                    'SOT-23': 'Package_TO_SOT_SMD:SOT-23',
                    'SOT-23-3': 'Package_TO_SOT_SMD:SOT-23',
                    'SOT-23-5': 'Package_TO_SOT_SMD:SOT-23-5',
                    'SOT-23-6': 'Package_TO_SOT_SMD:SOT-23-6',
                    'SOT-223': 'Package_TO_SOT_SMD:SOT-223',
                    'TO-252': 'Package_TO_SOT_SMD:TO-252-3_TabPin2',
                    'DPAK': 'Package_TO_SOT_SMD:TO-252-3_TabPin2'
                }
            },
            'ics': {
                'altium_library': 'Integrated Circuits',
                'kicad_symbol': 'Device:U',
                'symbol_patterns': [r'.*ic.*', r'.*integrated circuit.*', r'.*microcontroller.*', r'.*processor.*'],
                'common_footprints': {
                    'SOIC-8': 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
                    'SOIC-16': 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',
                    'TSSOP-8': 'Package_SO:TSSOP-8_4.4x3mm_P0.65mm',
                    'TSSOP-16': 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
                    'QFN-20': 'Package_DFN_QFN:QFN-20-1EP_4x4mm_P0.5mm_EP2.5x2.5mm',
                    'QFN-24': 'Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm',
                    'LQFP-32': 'Package_QFP:LQFP-32_7x7mm_P0.8mm',
                    'LQFP-48': 'Package_QFP:LQFP-48_7x7mm_P0.5mm',
                    'LQFP-64': 'Package_QFP:LQFP-64_10x10mm_P0.5mm',
                    'LQFP-100': 'Package_QFP:LQFP-100_14x14mm_P0.5mm'
                }
            }
        }
    
    def map_symbol(self, altium_symbol: str, component_data: Dict[str, Any]) -> str:
        """
        Map Altium symbol to KiCAD symbol.
        
        Args:
            altium_symbol: Altium symbol name
            component_data: Component data dictionary
            
        Returns:
            KiCAD symbol name
            
        Raises:
            SymbolMappingError: If mapping fails
        """
        try:
            self.logger.debug(f"Mapping symbol: {altium_symbol}")
            
            if not altium_symbol:
                self.logger.warning("Empty Altium symbol name provided")
                return self._get_fallback_symbol(component_data)
            
            # Direct mapping check
            if altium_symbol in self.symbol_mappings:
                self.logger.debug(f"Found direct symbol mapping: {altium_symbol} -> {self.symbol_mappings[altium_symbol]}")
                return self.symbol_mappings[altium_symbol]
            
            # Pattern-based mapping from symbol_mappings
            for pattern, kicad_symbol in self.symbol_mappings.items():
                if '*' in pattern and fnmatch.fnmatch(altium_symbol, pattern):
                    self.logger.debug(f"Matched symbol pattern: {pattern} -> {kicad_symbol}")
                    # Cache the mapping for future use
                    self.symbol_mappings[altium_symbol] = kicad_symbol
                    return kicad_symbol
            
            # Component type-based mapping
            description = component_data.get('Description', '').lower()
            value = component_data.get('Value', '').lower()
            
            for comp_type, mapping in self.component_type_mappings.items():
                for pattern in mapping.get('symbol_patterns', []):
                    if re.search(pattern, description) or re.search(pattern, value):
                        kicad_symbol = mapping['kicad_symbol']
                        # Cache the mapping
                        self.symbol_mappings[altium_symbol] = kicad_symbol
                        self.logger.debug(f"Mapped symbol by pattern: {altium_symbol} -> {kicad_symbol}")
                        return kicad_symbol
            
            # Try to find similar symbol using fuzzy matching
            kicad_symbol = self._find_similar_symbol(altium_symbol, component_data)
            if kicad_symbol:
                self.logger.debug(f"Mapped symbol by similarity: {altium_symbol} -> {kicad_symbol}")
                return kicad_symbol
            
            # Fallback to generic symbol
            fallback = self._get_fallback_symbol(component_data)
            self.logger.warning(f"No mapping found for symbol: {altium_symbol}, using fallback: {fallback}")
            return fallback
            
        except Exception as e:
            self.logger.error(f"Error mapping symbol {altium_symbol}: {str(e)}")
            raise SymbolMappingError(f"Failed to map symbol {altium_symbol}: {str(e)}")
    
    def _find_similar_symbol(self, altium_symbol: str, component_data: Dict[str, Any]) -> Optional[str]:
        """
        Find similar KiCAD symbol using fuzzy matching.
        
        Args:
            altium_symbol: Altium symbol name
            component_data: Component data dictionary
            
        Returns:
            KiCAD symbol name or None if no match found
        """
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
        elif any(word in description for word in ['ic', 'integrated', 'chip']):
            return 'Device:U'
        
        return None
    
    def _get_fallback_symbol(self, component_data: Dict[str, Any]) -> str:
        """
        Get fallback symbol when no good match is found.
        
        Args:
            component_data: Component data dictionary
            
        Returns:
            KiCAD symbol name
        """
        # Use basic heuristics for fallback
        description = component_data.get('Description', '').lower()
        value = component_data.get('Value', '').lower()
        
        # Check for basic component indicators
        if any(term in f"{description} {value}" for term in ['ohm', 'k', 'm', 'resistor']):
            return 'Device:R'
        elif any(term in f"{description} {value}" for term in ['f', 'farad', 'capacitor']):
            return 'Device:C'
        elif any(term in f"{description} {value}" for term in ['h', 'henry', 'inductor']):
            return 'Device:L'
        elif any(term in f"{description} {value}" for term in ['diode', 'rectifier']):
            return 'Device:D'
        elif any(term in f"{description} {value}" for term in ['transistor', 'fet', 'mosfet']):
            return 'Device:Q_NMOS_GSD'
        else:
            return 'Device:U'  # Ultimate fallback
    
    def map_footprint(self, altium_footprint: str, component_data: Dict[str, Any]) -> str:
        """
        Map Altium footprint to KiCAD footprint.
        
        Args:
            altium_footprint: Altium footprint name
            component_data: Component data dictionary
            
        Returns:
            KiCAD footprint name
            
        Raises:
            FootprintMappingError: If mapping fails
        """
        try:
            self.logger.debug(f"Mapping footprint: {altium_footprint}")
            
            if not altium_footprint:
                self.logger.warning("Empty Altium footprint name provided")
                return self._get_fallback_footprint(component_data)
            
            # Direct mapping check
            if altium_footprint in self.footprint_mappings:
                self.logger.debug(f"Found direct footprint mapping: {altium_footprint} -> {self.footprint_mappings[altium_footprint]}")
                return self.footprint_mappings[altium_footprint]
            
            # Pattern-based mapping from footprint_mappings
            for pattern, kicad_footprint in self.footprint_mappings.items():
                if '*' in pattern and fnmatch.fnmatch(altium_footprint, pattern):
                    self.logger.debug(f"Matched footprint pattern: {pattern} -> {kicad_footprint}")
                    # Cache the mapping for future use
                    self.footprint_mappings[altium_footprint] = kicad_footprint
                    return kicad_footprint
            
            # Package size extraction and mapping
            package = self._extract_package_size(altium_footprint, component_data)
            if package:
                description = component_data.get('Description', '').lower()
                
                # Check component type mappings
                for comp_type, mapping in self.component_type_mappings.items():
                    if any(re.search(pattern, description) for pattern in mapping.get('symbol_patterns', [])):
                        footprint_mappings = mapping.get('common_footprints', {})
                        if package in footprint_mappings:
                            kicad_footprint = footprint_mappings[package]
                            # Cache the mapping
                            self.footprint_mappings[altium_footprint] = kicad_footprint
                            self.logger.debug(f"Mapped footprint by package size: {altium_footprint} ({package}) -> {kicad_footprint}")
                            return kicad_footprint
            
            # Try to find similar footprint using fuzzy matching
            kicad_footprint = self._find_similar_footprint(altium_footprint, component_data)
            if kicad_footprint:
                self.logger.debug(f"Mapped footprint by similarity: {altium_footprint} -> {kicad_footprint}")
                return kicad_footprint
            
            # Fallback to generic footprint
            fallback = self._get_fallback_footprint(component_data)
            self.logger.warning(f"No mapping found for footprint: {altium_footprint}, using fallback: {fallback}")
            return fallback
            
        except Exception as e:
            self.logger.error(f"Error mapping footprint {altium_footprint}: {str(e)}")
            raise FootprintMappingError(f"Failed to map footprint {altium_footprint}: {str(e)}")
    
    def _extract_package_size(self, footprint: str, component_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract package size from footprint name or component data.
        
        Args:
            footprint: Altium footprint name
            component_data: Component data dictionary
            
        Returns:
            Package size string or None if not found
        """
        # Common package size patterns
        package_patterns = [
            # SMD resistors/capacitors
            r'(\d{3,4})$',  # Ends with 3-4 digits (0603, 1206, etc.)
            r'(\d{3,4})[^0-9]',  # 3-4 digits followed by non-digit
            r'_(\d{3,4})_',  # 3-4 digits surrounded by underscores
            
            # SOT packages
            r'SOT-?(\d+)',  # SOT followed by numbers
            r'SOT-?(\d+-\d+)',  # SOT with complex numbering
            
            # SOIC/TSSOP/QFP packages
            r'SOIC-?(\d+)',
            r'TSSOP-?(\d+)',
            r'QFP-?(\d+)',
            r'LQFP-?(\d+)',
            r'QFN-?(\d+)',
            
            # DIP packages
            r'DIP-?(\d+)',
        ]
        
        # Try to extract from footprint name
        for pattern in package_patterns:
            match = re.search(pattern, footprint, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try to extract from package field
        package = component_data.get('Package', '')
        if package:
            for pattern in package_patterns:
                match = re.search(pattern, package, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        # Try to extract from description
        description = component_data.get('Description', '')
        for pattern in package_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _find_similar_footprint(self, altium_footprint: str, component_data: Dict[str, Any]) -> Optional[str]:
        """
        Find similar KiCAD footprint using fuzzy matching.
        
        Args:
            altium_footprint: Altium footprint name
            component_data: Component data dictionary
            
        Returns:
            KiCAD footprint name or None if no match found
        """
        # Extract common package identifiers
        footprint_lower = altium_footprint.lower()
        
        # Check for common package types
        if '0603' in footprint_lower:
            if 'res' in footprint_lower:
                return 'Resistor_SMD:R_0603_1608Metric'
            elif 'cap' in footprint_lower:
                return 'Capacitor_SMD:C_0603_1608Metric'
            else:
                return 'Resistor_SMD:R_0603_1608Metric'
                
        elif '0805' in footprint_lower:
            if 'res' in footprint_lower:
                return 'Resistor_SMD:R_0805_2012Metric'
            elif 'cap' in footprint_lower:
                return 'Capacitor_SMD:C_0805_2012Metric'
            else:
                return 'Resistor_SMD:R_0805_2012Metric'
                
        elif 'sot23' in footprint_lower or 'sot-23' in footprint_lower:
            return 'Package_TO_SOT_SMD:SOT-23'
            
        elif 'soic' in footprint_lower:
            if '8' in footprint_lower:
                return 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
            elif '16' in footprint_lower:
                return 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm'
            else:
                return 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
        
        return None
    
    def _get_fallback_footprint(self, component_data: Dict[str, Any]) -> str:
        """
        Get fallback footprint when no good match is found.
        
        Args:
            component_data: Component data dictionary
            
        Returns:
            KiCAD footprint name
        """
        # Use basic heuristics for fallback
        description = component_data.get('Description', '').lower()
        
        # Check for basic component indicators
        if any(term in description for term in ['resistor', 'res', 'ohm']):
            return 'Resistor_SMD:R_0603_1608Metric'
        elif any(term in description for term in ['capacitor', 'cap']):
            return 'Capacitor_SMD:C_0603_1608Metric'
        elif any(term in description for term in ['inductor', 'ind']):
            return 'Inductor_SMD:L_0603_1608Metric'
        elif any(term in description for term in ['diode']):
            return 'Diode_SMD:D_SOD-123'
        elif any(term in description for term in ['transistor', 'fet', 'mosfet']):
            return 'Package_TO_SOT_SMD:SOT-23'
        else:
            return 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'  # Ultimate fallback
    
    def map_fields(self, altium_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Altium fields to KiCAD fields.
        
        Args:
            altium_data: Dictionary of Altium component data
            
        Returns:
            Dictionary of mapped KiCAD fields
        """
        try:
            mapped_fields = {}
            
            for altium_field, kicad_field in self.field_mappings.items():
                if altium_field in altium_data:
                    value = altium_data[altium_field]
                    if value is not None and str(value).strip():  # Only map non-empty values
                        mapped_fields[kicad_field] = str(value).strip()
            
            # Add some derived fields if they don't exist
            if 'Value' not in mapped_fields and 'Description' in mapped_fields:
                mapped_fields['Value'] = mapped_fields['Description']
            
            # Ensure required fields exist
            if 'Reference' not in mapped_fields:
                # Try to determine a reasonable reference designator
                if any(term in str(altium_data.get('Description', '')).lower() for term in ['resistor', 'res']):
                    mapped_fields['Reference'] = 'R'
                elif any(term in str(altium_data.get('Description', '')).lower() for term in ['capacitor', 'cap']):
                    mapped_fields['Reference'] = 'C'
                elif any(term in str(altium_data.get('Description', '')).lower() for term in ['inductor', 'ind']):
                    mapped_fields['Reference'] = 'L'
                elif any(term in str(altium_data.get('Description', '')).lower() for term in ['diode']):
                    mapped_fields['Reference'] = 'D'
                elif any(term in str(altium_data.get('Description', '')).lower() for term in ['transistor', 'fet', 'mosfet']):
                    mapped_fields['Reference'] = 'Q'
                else:
                    mapped_fields['Reference'] = 'U'
            
            return mapped_fields
            
        except Exception as e:
            self.logger.error(f"Error mapping fields: {str(e)}")
            # Return minimal fields to avoid complete failure
            return {
                'Reference': 'U',
                'Value': altium_data.get('Description', 'Unknown')
            }
    
    def map_component_category(self, component_data: Dict[str, Any]) -> Tuple[str, str, List[str]]:
        """
        Map component to category, subcategory and keywords.
        
        Args:
            component_data: Dictionary of component data
            
        Returns:
            Tuple of (category, subcategory, keywords)
        """
        try:
            # Extract component name and description for matching
            name = component_data.get('Name', '')
            description = component_data.get('Description', '')
            symbol = component_data.get('Symbol', '')
            footprint = component_data.get('Footprint', '')
            
            match_text = f"{name} {description} {symbol} {footprint}".lower()
            
            # Try to match against category mapping rules
            for rule in self.category_mappings:
                pattern = rule.get('pattern', '')
                if pattern and fnmatch.fnmatch(match_text, pattern.lower()):
                    return (
                        rule.get('category', 'Uncategorized'),
                        rule.get('subcategory', 'General'),
                        rule.get('keywords', [])
                    )
            
            # Fallback to basic categorization
            if any(term in match_text for term in ['resistor', 'res', 'ohm']):
                return ('Passive Components', 'Resistors', ['resistor', 'resistance', 'ohm'])
            elif any(term in match_text for term in ['capacitor', 'cap']):
                return ('Passive Components', 'Capacitors', ['capacitor', 'capacitance', 'farad'])
            elif any(term in match_text for term in ['inductor', 'ind']):
                return ('Passive Components', 'Inductors', ['inductor', 'inductance', 'henry'])
            elif any(term in match_text for term in ['diode']):
                return ('Semiconductor', 'Diodes', ['diode', 'rectifier'])
            elif any(term in match_text for term in ['transistor', 'fet', 'mosfet']):
                return ('Semiconductor', 'Transistors', ['transistor', 'fet', 'mosfet'])
            elif any(term in match_text for term in ['ic', 'integrated', 'chip']):
                return ('Integrated Circuits', 'General', ['ic', 'chip'])
            else:
                return ('Uncategorized', 'General', ['component'])
                
        except Exception as e:
            self.logger.error(f"Error mapping component category: {str(e)}")
            return ('Uncategorized', 'General', ['component'])
    
    def map_component(self, altium_data: Dict[str, Any], table_config: Dict[str, Any]) -> ComponentMapping:
        """
        Map a single Altium component to KiCAD format.
        
        Args:
            altium_data: Dictionary of Altium component data
            table_config: Configuration for the table containing the component
            
        Returns:
            ComponentMapping object with mapped data
            
        Raises:
            MappingError: If mapping fails
        """
        try:
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
            
            # Map category
            category, subcategory, keywords = self.map_component_category(altium_data)
            
            # Calculate confidence score based on mapping method
            confidence = self._calculate_confidence(
                altium_symbol, altium_footprint,
                kicad_symbol, kicad_footprint,
                altium_data
            )
            
            return ComponentMapping(
                altium_symbol=altium_symbol,
                altium_footprint=altium_footprint,
                kicad_symbol=kicad_symbol,
                kicad_footprint=kicad_footprint,
                confidence=confidence,
                field_mappings=mapped_fields,
                category=category,
                subcategory=subcategory,
                keywords=keywords
            )
            
        except Exception as e:
            self.logger.error(f"Error mapping component: {str(e)}")
            # Create a minimal mapping for failed components
            return ComponentMapping(
                altium_symbol=altium_data.get('Symbol', ''),
                altium_footprint=altium_data.get('Footprint', ''),
                kicad_symbol='Device:U',  # Fallback
                kicad_footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',  # Fallback
                confidence=0.0,
                field_mappings=self.map_fields(altium_data)
            )
    
    def _calculate_confidence(
        self,
        altium_symbol: str,
        altium_footprint: str,
        kicad_symbol: str,
        kicad_footprint: str,
        component_data: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for a mapping.
        
        Args:
            altium_symbol: Altium symbol name
            altium_footprint: Altium footprint name
            kicad_symbol: KiCAD symbol name
            kicad_footprint: KiCAD footprint name
            component_data: Component data dictionary
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Start with base confidence
        confidence = 0.5
        
        # Direct mapping has high confidence
        if altium_symbol in self.symbol_mappings and self.symbol_mappings[altium_symbol] == kicad_symbol:
            confidence += 0.3
        
        if altium_footprint in self.footprint_mappings and self.footprint_mappings[altium_footprint] == kicad_footprint:
            confidence += 0.3
        
        # Pattern-based mapping has good confidence
        for pattern in self.symbol_mappings:
            if '*' in pattern and fnmatch.fnmatch(altium_symbol, pattern) and self.symbol_mappings[pattern] == kicad_symbol:
                confidence += 0.2
                break
        
        for pattern in self.footprint_mappings:
            if '*' in pattern and fnmatch.fnmatch(altium_footprint, pattern) and self.footprint_mappings[pattern] == kicad_footprint:
                confidence += 0.2
                break
        
        # Fallback mappings have lower confidence
        if kicad_symbol in ['Device:R', 'Device:C', 'Device:L', 'Device:D', 'Device:Q_NMOS_GSD', 'Device:U']:
            # Check if the fallback matches the component type
            description = component_data.get('Description', '').lower()
            if kicad_symbol == 'Device:R' and any(term in description for term in ['resistor', 'res']):
                confidence += 0.1
            elif kicad_symbol == 'Device:C' and any(term in description for term in ['capacitor', 'cap']):
                confidence += 0.1
            elif kicad_symbol == 'Device:L' and any(term in description for term in ['inductor', 'ind']):
                confidence += 0.1
            elif kicad_symbol == 'Device:D' and any(term in description for term in ['diode']):
                confidence += 0.1
            elif kicad_symbol == 'Device:Q_NMOS_GSD' and any(term in description for term in ['transistor', 'fet', 'mosfet']):
                confidence += 0.1
            else:
                confidence -= 0.1
        
        # Cap confidence between 0.0 and 1.0
        return max(0.0, min(1.0, confidence))
    
    def map_table_data(self, table_name: str, table_data: Dict[str, Any]) -> List[ComponentMapping]:
        """
        Map all components in a table.
        
        Args:
            table_name: Name of the table
            table_data: Dictionary containing table configuration and data
            
        Returns:
            List of ComponentMapping objects
        """
        mappings = []
        table_config = table_data.get('config', {})
        
        self.logger.info(f"Mapping {len(table_data.get('data', []))} components from table '{table_name}'")
        
        for component_data in table_data.get('data', []):
            try:
                mapping = self.map_component(component_data, table_config)
                mappings.append(mapping)
                
                # Log high and low confidence mappings
                if mapping.confidence >= 0.8:
                    self.logger.debug(f"High confidence mapping ({mapping.confidence:.2f}): {mapping.altium_symbol} -> {mapping.kicad_symbol}")
                elif mapping.confidence <= 0.3:
                    self.logger.warning(f"Low confidence mapping ({mapping.confidence:.2f}): {mapping.altium_symbol} -> {mapping.kicad_symbol}")
                
            except Exception as e:
                self.logger.error(f"Error mapping component in {table_name}: {str(e)}")
                # Create a minimal mapping for failed components
                mappings.append(ComponentMapping(
                    altium_symbol=component_data.get('Symbol', ''),
                    altium_footprint=component_data.get('Footprint', ''),
                    kicad_symbol='Device:U',  # Fallback
                    kicad_footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',  # Fallback
                    confidence=0.0,
                    field_mappings=self.map_fields(component_data)
                ))
        
        self.logger.info(f"Successfully mapped {len(mappings)} components from table '{table_name}'")
        return mappings
    
    def map_database_data(self, database_data: Dict[str, Dict[str, Any]]) -> Dict[str, List[ComponentMapping]]:
        """
        Map all components from all tables in a database.
        
        Args:
            database_data: Dictionary of table data keyed by table name
            
        Returns:
            Dictionary of ComponentMapping lists keyed by table name
        """
        result = {}
        
        self.logger.info(f"Mapping components from {len(database_data)} tables")
        
        for table_name, table_data in database_data.items():
            try:
                result[table_name] = self.map_table_data(table_name, table_data)
            except Exception as e:
                self.logger.error(f"Error mapping table {table_name}: {str(e)}")
                result[table_name] = []
        
        return result