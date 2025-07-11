import re
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections import defaultdict
import pickle
import logging

@dataclass
class SymbolMatch:
    """Result of symbol matching operation"""
    kicad_symbol: str
    confidence: float
    match_type: str  # 'exact', 'fuzzy', 'semantic', 'fallback'
    reasoning: str

@dataclass
class FootprintMatch:
    """Result of footprint matching operation"""
    kicad_footprint: str
    confidence: float
    match_type: str
    reasoning: str

class FuzzyMatcher:
    """Advanced fuzzy matching for symbols and footprints"""
    
    def __init__(self):
        self.symbol_cache = {}
        self.footprint_cache = {}
        self.kicad_symbols = self._load_kicad_symbols()
        self.kicad_footprints = self._load_kicad_footprints()
        
    def _load_kicad_symbols(self) -> Dict[str, List[str]]:
        """Load KiCAD symbol library structure"""
        # This would ideally scan actual KiCAD symbol libraries
        # For now, we'll use a comprehensive list of common symbols
        symbols = {
            'Device': [
                'R', 'R_Small', 'R_Variable', 'R_Potentiometer',
                'C', 'C_Small', 'C_Polarized', 'C_Variable',
                'L', 'L_Small', 'L_Core_Ferrite',
                'D', 'D_Zener', 'D_Schottky', 'D_Bridge_+A-A',
                'Q_NPN_BCE', 'Q_PNP_BCE', 'Q_NMOS_GSD', 'Q_PMOS_GSD',
                'LED', 'Fuse', 'Crystal', 'Resonator'
            ],
            'Amplifier_Operational': [
                'LM358', 'LM324', 'TL071', 'TL072', 'TL074',
                'AD8051', 'AD8052', 'AD8054', 'OPA2134', 'OPA4134'
            ]
        }
        return symbols
    
    def _load_kicad_footprints(self) -> Dict[str, List[str]]:
        """Load KiCAD footprint library structure"""
        footprints = {
            'Resistor_SMD': [
                'R_0201_0603Metric', 'R_0402_1005Metric', 'R_0603_1608Metric',
                'R_0805_2012Metric', 'R_1206_3216Metric', 'R_1210_3225Metric',
                'R_2010_5025Metric', 'R_2512_6332Metric'
            ],
            'Capacitor_SMD': [
                'C_0201_0603Metric', 'C_0402_1005Metric', 'C_0603_1608Metric',
                'C_0805_2012Metric', 'C_1206_3216Metric', 'C_1210_3225Metric'
            ]
        }
        return footprints
    
    def find_symbol_match(self, altium_symbol: str, component_data: Dict[str, any]) -> SymbolMatch:
        """Find best KiCAD symbol match using multiple strategies"""
        
        # Strategy 1: Exact match
        exact_match = self._find_exact_symbol_match(altium_symbol)
        if exact_match:
            return SymbolMatch(
                kicad_symbol=exact_match,
                confidence=1.0,
                match_type='exact',
                reasoning=f'Exact match found for {altium_symbol}'
            )
        
        # Strategy 2: Fuzzy string matching
        fuzzy_match = self._find_fuzzy_symbol_match(altium_symbol)
        if fuzzy_match and fuzzy_match[1] > 0.8:
            return SymbolMatch(
                kicad_symbol=fuzzy_match[0],
                confidence=fuzzy_match[1],
                match_type='fuzzy',
                reasoning=f'High confidence fuzzy match (similarity: {fuzzy_match[1]:.2f})'
            )
        
        # Strategy 3: Semantic matching based on component description
        semantic_match = self._find_semantic_symbol_match(component_data)
        if semantic_match:
            return SymbolMatch(
                kicad_symbol=semantic_match[0],
                confidence=semantic_match[1],
                match_type='semantic',
                reasoning=f'Semantic match based on component description'
            )
        
        # Strategy 4: Pattern-based matching
        pattern_match = self._find_pattern_symbol_match(altium_symbol, component_data)
        if pattern_match:
            return SymbolMatch(
                kicad_symbol=pattern_match[0],
                confidence=pattern_match[1],
                match_type='pattern',
                reasoning='Pattern-based match using component characteristics'
            )
        
        # Strategy 5: Fallback to generic component
        fallback_match = self._get_fallback_symbol(component_data)
        return SymbolMatch(
            kicad_symbol=fallback_match,
            confidence=0.3,
            match_type='fallback',
            reasoning='No good match found, using generic symbol'
        )
    
    def _find_exact_symbol_match(self, altium_symbol: str) -> Optional[str]:
        """Find exact match for symbol in KiCAD libraries"""
        # Check cache first
        if altium_symbol in self.symbol_cache:
            return self.symbol_cache[altium_symbol]
        
        # Look for exact matches in KiCAD libraries
        for library, symbols in self.kicad_symbols.items():
            # Try direct match
            if altium_symbol in symbols:
                kicad_symbol = f"{library}:{altium_symbol}"
                self.symbol_cache[altium_symbol] = kicad_symbol
                return kicad_symbol
            
            # Try with library prefix removed
            if ':' in altium_symbol:
                symbol_name = altium_symbol.split(':')[-1]
                if symbol_name in symbols:
                    kicad_symbol = f"{library}:{symbol_name}"
                    self.symbol_cache[altium_symbol] = kicad_symbol
                    return kicad_symbol
        
        return None
    
    def _find_fuzzy_symbol_match(self, altium_symbol: str) -> Optional[Tuple[str, float]]:
        """Find fuzzy match for symbol using string similarity"""
        best_match = None
        best_score = 0.0
        
        # Remove library prefix if present
        if ':' in altium_symbol:
            symbol_name = altium_symbol.split(':')[-1]
        else:
            symbol_name = altium_symbol
        
        # Compare with all KiCAD symbols
        for library, symbols in self.kicad_symbols.items():
            for kicad_symbol in symbols:
                score = SequenceMatcher(None, symbol_name.lower(), kicad_symbol.lower()).ratio()
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = f"{library}:{kicad_symbol}"
        
        if best_match:
            return (best_match, best_score)
        return None
    
    def _find_semantic_symbol_match(self, component_data: Dict[str, any]) -> Optional[Tuple[str, float]]:
        """Find symbol match based on component description and attributes"""
        description = component_data.get('Description', '').lower()
        value = component_data.get('Value', '').lower()
        
        # Keywords to symbol mappings
        keyword_mappings = {
            'resistor': ('Device:R', 0.9),
            'capacitor': ('Device:C', 0.9),
            'inductor': ('Device:L', 0.9),
            'diode': ('Device:D', 0.9),
            'led': ('Device:LED', 0.9),
            'transistor': ('Device:Q_NPN_BCE', 0.8),
            'mosfet': ('Device:Q_NMOS_GSD', 0.8),
            'crystal': ('Device:Crystal', 0.9),
            'fuse': ('Device:Fuse', 0.9),
            'opamp': ('Amplifier_Operational:LM358', 0.8)
        }
        
        # Check for keyword matches
        for keyword, (symbol, confidence) in keyword_mappings.items():
            if keyword in description or keyword in value:
                return (symbol, confidence)
        
        return None
    
    def _find_pattern_symbol_match(self, altium_symbol: str, component_data: Dict[str, any]) -> Optional[Tuple[str, float]]:
        """Find symbol match using regex patterns"""
        # Common patterns in Altium symbols
        patterns = [
            (r'res.*', 'Device:R', 0.8),
            (r'cap.*', 'Device:C', 0.8),
            (r'ind.*', 'Device:L', 0.8),
            (r'diode.*', 'Device:D', 0.8),
            (r'led.*', 'Device:LED', 0.8),
            (r'transistor.*', 'Device:Q_NPN_BCE', 0.7),
            (r'fet.*', 'Device:Q_NMOS_GSD', 0.7),
            (r'crystal.*', 'Device:Crystal', 0.8),
            (r'fuse.*', 'Device:Fuse', 0.8),
            (r'opamp.*', 'Amplifier_Operational:LM358', 0.7)
        ]
        
        for pattern, symbol, confidence in patterns:
            if re.search(pattern, altium_symbol.lower()):
                return (symbol, confidence)
        
        return None
    
    def _get_fallback_symbol(self, component_data: Dict[str, any]) -> str:
        """Get fallback symbol based on component data"""
        # Default to resistor if nothing else matches
        return 'Device:R'