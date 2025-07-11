"""
KiCAD database library generator.

This module provides functionality to generate KiCAD database libraries
from mapped component data.
"""

import sqlite3
import json
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import asdict
import uuid
import time

from migration_tool.utils.logging_utils import get_logger, ProgressLogger


class KiCADGenerationError(Exception):
    """Base exception for KiCAD generation errors."""
    pass


class DatabaseError(KiCADGenerationError):
    """Exception raised when database operations fail."""
    pass


class ConfigurationError(KiCADGenerationError):
    """Exception raised when configuration is invalid."""
    pass


class KiCADDbLibGenerator:
    """Generator for KiCAD database libraries from mapped component data."""
    
    def __init__(self, output_dir: str, config_manager=None):
        """
        Initialize the generator with output directory.
        
        Args:
            output_dir: Directory where output files will be created
            config_manager: Optional configuration manager instance
        """
        self.logger = get_logger("core.kicad_generator")
        self.config = config_manager
        
        # Set up output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default paths
        self.db_path = self.output_dir / "components.db"
        self.dblib_path = self.output_dir / "components.kicad_dbl"
        
        # Override with config if available
        if self.config:
            if self.config.get('database_name'):
                self.db_path = self.output_dir / self.config.get('database_name')
            if self.config.get('dblib_name'):
                self.dblib_path = self.output_dir / self.config.get('dblib_name')
        
        self.logger.info(f"Initialized KiCADDbLibGenerator with output directory: {self.output_dir}")
        self.logger.info(f"Database path: {self.db_path}")
        self.logger.info(f"DbLib path: {self.dblib_path}")
    def create_database_schema(self) -> None:
        """
        Create SQLite database with KiCAD-compatible schema.
        
        Raises:
            DatabaseError: If database schema creation fails
        """
        self.logger.info("Creating database schema")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Drop existing tables if they exist
            cursor.execute("DROP TABLE IF EXISTS components")
            cursor.execute("DROP TABLE IF EXISTS categories")
            
            # Create categories table
            self.logger.debug("Creating categories table")
            cursor.execute("""
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    parent_id INTEGER REFERENCES categories(id)
                )
            """)
            
            # Create main components table
            self.logger.debug("Creating components table")
            cursor.execute("""
                CREATE TABLE components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    footprint TEXT NOT NULL,
                    reference TEXT NOT NULL,
                    value TEXT,
                    description TEXT,
                    keywords TEXT,
                    manufacturer TEXT,
                    mpn TEXT,
                    datasheet TEXT,
                    supplier TEXT,
                    spn TEXT,
                    package TEXT,
                    voltage TEXT,
                    current TEXT,
                    power TEXT,
                    tolerance TEXT,
                    temperature TEXT,
                    category_id INTEGER REFERENCES categories(id),
                    confidence REAL,
                    original_altium_symbol TEXT,
                    original_altium_footprint TEXT,
                    exclude_from_board BOOLEAN DEFAULT 0,
                    exclude_from_bom BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            self.logger.debug("Creating indexes")
            cursor.execute("CREATE INDEX idx_components_symbol ON components(symbol)")
            cursor.execute("CREATE INDEX idx_components_footprint ON components(footprint)")
            cursor.execute("CREATE INDEX idx_components_mpn ON components(mpn)")
            cursor.execute("CREATE INDEX idx_components_manufacturer ON components(manufacturer)")
            cursor.execute("CREATE INDEX idx_components_category ON components(category_id)")
            cursor.execute("CREATE INDEX idx_components_reference ON components(reference)")
            
            # Create views for different component types
            self.logger.debug("Creating component views")
            self._create_component_views(cursor)
            
            # Add additional fields from config if available
            if self.config and self.config.get('additional_component_fields'):
                self._add_additional_fields(cursor)
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database schema created successfully")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Failed to create database schema: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating database schema: {str(e)}")
            raise DatabaseError(f"Failed to create database schema: {str(e)}")
        conn.close()
    
    def _add_additional_fields(self, cursor) -> None:
        """
        Add additional fields to the components table based on configuration.
        
        Args:
            cursor: SQLite cursor
            
        Raises:
            DatabaseError: If adding fields fails
        """
        try:
            additional_fields = self.config.get('additional_component_fields', [])
            
            if not additional_fields:
                return
                
            self.logger.info(f"Adding {len(additional_fields)} additional fields to components table")
            
            for field in additional_fields:
                field_name = field.get('name')
                field_type = field.get('type', 'TEXT')
                
                if not field_name:
                    self.logger.warning("Skipping additional field with no name")
                    continue
                    
                # Sanitize field name for SQL
                field_name = field_name.replace(' ', '_').lower()
                
                # Add column to components table
                try:
                    cursor.execute(f"ALTER TABLE components ADD COLUMN {field_name} {field_type}")
                    self.logger.debug(f"Added field {field_name} ({field_type}) to components table")
                except sqlite3.Error as e:
                    self.logger.warning(f"Could not add field {field_name}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Error adding additional fields: {str(e)}")
            raise DatabaseError(f"Failed to add additional fields: {str(e)}")
    
    def _create_component_views(self, cursor) -> None:
        """Create views for different component categories."""
        
        # Resistors view
        cursor.execute("""
            CREATE VIEW resistors AS
            SELECT * FROM components 
            WHERE LOWER(description) LIKE '%resistor%' 
               OR symbol LIKE '%:R%'
               OR LOWER(keywords) LIKE '%resistor%'
        """)
        
        # Capacitors view
        cursor.execute("""
            CREATE VIEW capacitors AS
            SELECT * FROM components 
            WHERE LOWER(description) LIKE '%capacitor%' 
               OR symbol LIKE '%:C%'
               OR LOWER(keywords) LIKE '%capacitor%'
        """)
        
        # Inductors view
        cursor.execute("""
            CREATE VIEW inductors AS
            SELECT * FROM components 
            WHERE LOWER(description) LIKE '%inductor%' 
               OR symbol LIKE '%:L%'
               OR LOWER(keywords) LIKE '%inductor%'
        """)
        
        # ICs view
        cursor.execute("""
            CREATE VIEW integrated_circuits AS
            SELECT * FROM components 
            WHERE LOWER(description) LIKE '%ic%' 
               OR LOWER(description) LIKE '%microcontroller%'
               OR LOWER(description) LIKE '%processor%'
               OR symbol LIKE '%:U%'
        """)
        
        # Diodes view
        cursor.execute("""
            CREATE VIEW diodes AS
            SELECT * FROM components 
            WHERE LOWER(description) LIKE '%diode%' 
               OR symbol LIKE '%:D%'
               OR LOWER(keywords) LIKE '%diode%'
        """)
        
        # Transistors view
        cursor.execute("""
            CREATE VIEW transistors AS
            SELECT * FROM components 
            WHERE LOWER(description) LIKE '%transistor%' 
               OR LOWER(description) LIKE '%mosfet%'
               OR LOWER(description) LIKE '%fet%'
               OR symbol LIKE '%:Q%'
        """)
    
    def populate_categories(self, component_mappings: Dict[str, List]) -> Dict[str, int]:
        """
        Populate categories table and return category name to ID mapping.
        
        Args:
            component_mappings: Dictionary of component mappings by table
            
        Returns:
            Dictionary mapping category names to their IDs
            
        Raises:
            DatabaseError: If category population fails
        """
        self.logger.info("Populating component categories")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Define default category hierarchy
            default_categories = [
                ('Resistors', 'Resistive components'),
                ('Capacitors', 'Capacitive components'),
                ('Inductors', 'Inductive components'),
                ('Diodes', 'Diode components'),
                ('Transistors', 'Transistor components'),
                ('Integrated Circuits', 'IC components'),
                ('Connectors', 'Connector components'),
                ('Mechanical', 'Mechanical components'),
                ('Crystals & Oscillators', 'Timing components'),
                ('Sensors', 'Sensor components'),
                ('Power Management', 'Power management ICs'),
                ('Microcontrollers', 'Microcontroller units'),
                ('Memory', 'Memory components'),
                ('Analog', 'Analog components'),
                ('Digital', 'Digital components'),
                ('RF', 'RF components'),
                ('Optoelectronics', 'Optical components'),
                ('Test Points', 'Test and measurement'),
                ('Uncategorized', 'Uncategorized components')
            ]
            
            # Add custom categories from config if available
            categories = default_categories
            if self.config and self.config.get('custom_categories'):
                custom_categories = self.config.get('custom_categories', [])
                if isinstance(custom_categories, list):
                    # Merge custom categories with default ones
                    # Convert to dict to avoid duplicates
                    categories_dict = {name: desc for name, desc in default_categories}
                    for cat_entry in custom_categories:
                        if isinstance(cat_entry, dict) and 'name' in cat_entry:
                            categories_dict[cat_entry['name']] = cat_entry.get('description', '')
                    
                    # Convert back to list
                    categories = [(name, desc) for name, desc in categories_dict.items()]
                    self.logger.info(f"Added {len(custom_categories)} custom categories")
            
            # Insert categories
            category_ids = {}
            for name, description in categories:
                try:
                    cursor.execute(
                        "INSERT INTO categories (name, description) VALUES (?, ?)",
                        (name, description)
                    )
                    category_ids[name] = cursor.lastrowid
                    self.logger.debug(f"Added category: {name}")
                except sqlite3.Error as e:
                    self.logger.warning(f"Error adding category {name}: {str(e)}")
            
            # Ensure we have the Uncategorized category
            if 'Uncategorized' not in category_ids:
                try:
                    cursor.execute(
                        "INSERT INTO categories (name, description) VALUES (?, ?)",
                        ('Uncategorized', 'Uncategorized components')
                    )
                    category_ids['Uncategorized'] = cursor.lastrowid
                    self.logger.debug("Added fallback Uncategorized category")
                except sqlite3.Error as e:
                    self.logger.warning(f"Error adding Uncategorized category: {str(e)}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Populated {len(category_ids)} categories")
            return category_ids
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error populating categories: {str(e)}")
            raise DatabaseError(f"Failed to populate categories: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error populating categories: {str(e)}")
            raise DatabaseError(f"Failed to populate categories: {str(e)}")
    
    def _categorize_component(self, mapping, category_ids: Dict[str, int]) -> int:
        """Determine component category based on mapping data."""
        description = mapping.field_mappings.get('Description', '').lower()
        symbol = mapping.kicad_symbol.lower()
        
        # Category detection logic
        if any(term in description for term in ['resistor', 'resistance']) or ':r' in symbol:
            return category_ids.get('Resistors', category_ids['Uncategorized'])
        elif any(term in description for term in ['capacitor', 'capacitance']) or ':c' in symbol:
            return category_ids.get('Capacitors', category_ids['Uncategorized'])
        elif any(term in description for term in ['inductor', 'inductance']) or ':l' in symbol:
            return category_ids.get('Inductors', category_ids['Uncategorized'])
        elif any(term in description for term in ['diode']) or ':d' in symbol:
            return category_ids.get('Diodes', category_ids['Uncategorized'])
        elif any(term in description for term in ['transistor', 'mosfet', 'fet']) or ':q' in symbol:
            return category_ids.get('Transistors', category_ids['Uncategorized'])
        elif any(term in description for term in ['microcontroller', 'mcu', 'processor']):
            return category_ids.get('Microcontrollers', category_ids['Uncategorized'])
        elif any(term in description for term in ['connector', 'jack', 'plug', 'socket']):
            return category_ids.get('Connectors', category_ids['Uncategorized'])
        elif any(term in description for term in ['crystal', 'oscillator', 'resonator']):
            return category_ids.get('Crystals & Oscillators', category_ids['Uncategorized'])
        else:
            return category_ids.get('Uncategorized', category_ids['Uncategorized'])
    
    def populate_components(self, component_mappings: Dict[str, List], category_ids: Dict[str, int]) -> None:
        """
        Populate components table with mapped data.
        
        Args:
            component_mappings: Dictionary of component mappings by table
            category_ids: Dictionary mapping category names to their IDs
            
        Raises:
            DatabaseError: If component population fails
        """
        self.logger.info("Populating components table")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            total_components = 0
            failed_components = 0
            
            # Create progress logger
            total_mappings = sum(len(mappings) for mappings in component_mappings.values())
            progress = ProgressLogger(self.logger, total_mappings)
            
            for table_name, mappings in component_mappings.items():
                self.logger.info(f"Populating components from table: {table_name} ({len(mappings)} components)")
                
                table_components = 0
                for mapping in mappings:
                    try:
                        # Determine category
                        category_id = self._categorize_component(mapping, category_ids)
                        
                        # Prepare component data
                        component_data = {
                            'symbol': mapping.kicad_symbol,
                            'footprint': mapping.kicad_footprint,
                            'reference': mapping.field_mappings.get('Reference', 'U'),
                            'value': mapping.field_mappings.get('Value', ''),
                            'description': mapping.field_mappings.get('Description', ''),
                            'keywords': self._generate_keywords(mapping),
                            'manufacturer': mapping.field_mappings.get('Manufacturer', ''),
                            'mpn': mapping.field_mappings.get('MPN', ''),
                            'datasheet': mapping.field_mappings.get('Datasheet', ''),
                            'supplier': mapping.field_mappings.get('Supplier', ''),
                            'spn': mapping.field_mappings.get('SPN', ''),
                            'package': mapping.field_mappings.get('Package', ''),
                            'voltage': mapping.field_mappings.get('Voltage', ''),
                            'current': mapping.field_mappings.get('Current', ''),
                            'power': mapping.field_mappings.get('Power', ''),
                            'tolerance': mapping.field_mappings.get('Tolerance', ''),
                            'temperature': mapping.field_mappings.get('Temperature', ''),
                            'category_id': category_id,
                            'confidence': mapping.confidence,
                            'original_altium_symbol': mapping.altium_symbol,
                            'original_altium_footprint': mapping.altium_footprint
                        }
                        
                        # Add custom fields from mapping if they exist
                        if hasattr(mapping, 'category') and mapping.category:
                            component_data['category'] = mapping.category
                            
                        if hasattr(mapping, 'subcategory') and mapping.subcategory:
                            component_data['subcategory'] = mapping.subcategory
                        
                        # Insert component
                        placeholders = ', '.join(['?' for _ in component_data])
                        columns = ', '.join(component_data.keys())
                        
                        cursor.execute(
                            f"INSERT INTO components ({columns}) VALUES ({placeholders})",
                            list(component_data.values())
                        )
                        
                        total_components += 1
                        table_components += 1
                        
                        # Commit every 100 components to avoid large transactions
                        if total_components % 100 == 0:
                            conn.commit()
                            
                    except Exception as e:
                        self.logger.error(f"Error inserting component: {str(e)}")
                        failed_components += 1
                    
                    # Update progress
                    progress.update()
                
                self.logger.info(f"Added {table_components} components from table {table_name}")
                
                # Commit after each table
                conn.commit()
            
            # Final commit
            conn.commit()
            conn.close()
            
            # Complete progress
            progress.complete()
            
            self.logger.info(f"Populated {total_components} components in database")
            if failed_components > 0:
                self.logger.warning(f"Failed to insert {failed_components} components")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error populating components: {str(e)}")
            raise DatabaseError(f"Failed to populate components: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error populating components: {str(e)}")
            raise DatabaseError(f"Failed to populate components: {str(e)}")
    
    def _generate_keywords(self, mapping) -> str:
        """Generate keywords for component searchability."""
        keywords = []
        
        # Add description words
        description = mapping.field_mappings.get('Description', '')
        if description:
            # Extract meaningful words
            desc_words = [word.strip().lower() for word in description.replace(',', ' ').split() 
                         if len(word.strip()) > 2]
            keywords.extend(desc_words)
        
        # Add manufacturer
        manufacturer = mapping.field_mappings.get('Manufacturer', '')
        if manufacturer:
            keywords.append(manufacturer.lower())
        
        # Add package info
        package = mapping.field_mappings.get('Package', '')
        if package:
            keywords.append(package.lower())
        
        # Remove duplicates and return
        return ' '.join(list(set(keywords)))
    
    def generate_kicad_dblib_file(self) -> None:
        """
        Generate KiCAD .kicad_dbl configuration file.
        
        Raises:
            ConfigurationError: If dblib file generation fails
        """
        self.logger.info("Generating KiCAD database library file")
        
        try:
            # Get library name and description from config if available
            library_name = "Migrated Altium Library"
            library_description = "Components migrated from Altium database library"
            
            if self.config:
                if self.config.get('library_name'):
                    library_name = self.config.get('library_name')
                if self.config.get('library_description'):
                    library_description = self.config.get('library_description')
            
            # Build library configuration
            config = {
                "meta": {
                    "version": 1.0
                },
                "name": library_name,
                "description": library_description,
                "source": {
                    "type": "odbc",
                    "dsn": "",
                    "username": "",
                    "password": "",
                    "timeout_seconds": 10,
                    "connection_string": f"Driver=SQLite3;Database={self.db_path.absolute()};"
                },
                "libraries": []
            }
            
            # Create library definitions for different views/categories
            library_definitions = [
                {
                    "name": "All Components",
                    "table": "components",
                    "key": "id",
                    "symbols": "symbol",
                    "footprints": "footprint",
                    "fields": self._get_standard_field_definitions()
                },
                {
                    "name": "Resistors",
                    "table": "resistors",
                    "key": "id",
                    "symbols": "symbol",
                    "footprints": "footprint",
                    "fields": self._get_resistor_field_definitions()
                },
                {
                    "name": "Capacitors",
                    "table": "capacitors",
                    "key": "id",
                    "symbols": "symbol",
                    "footprints": "footprint",
                    "fields": self._get_capacitor_field_definitions()
                },
                {
                    "name": "Inductors",
                    "table": "inductors",
                    "key": "id",
                    "symbols": "symbol",
                    "footprints": "footprint",
                    "fields": self._get_inductor_field_definitions()
                },
                {
                    "name": "Integrated Circuits",
                    "table": "integrated_circuits",
                    "key": "id",
                    "symbols": "symbol",
                    "footprints": "footprint",
                    "fields": self._get_ic_field_definitions()
                }
            ]
            
            # Add custom library definitions from config if available
            if self.config and self.config.get('custom_library_definitions'):
                custom_libs = self.config.get('custom_library_definitions', [])
                if isinstance(custom_libs, list):
                    for lib_def in custom_libs:
                        if isinstance(lib_def, dict) and 'name' in lib_def and 'table' in lib_def:
                            # Ensure required fields are present
                            if 'key' not in lib_def:
                                lib_def['key'] = 'id'
                            if 'symbols' not in lib_def:
                                lib_def['symbols'] = 'symbol'
                            if 'footprints' not in lib_def:
                                lib_def['footprints'] = 'footprint'
                            if 'fields' not in lib_def:
                                lib_def['fields'] = self._get_standard_field_definitions()
                                
                            library_definitions.append(lib_def)
                            self.logger.debug(f"Added custom library definition: {lib_def['name']}")
            
            config["libraries"] = library_definitions
            
            # Write configuration file
            with open(self.dblib_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Generated KiCAD database library file: {self.dblib_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating KiCAD database library file: {str(e)}")
            raise ConfigurationError(f"Failed to generate KiCAD database library file: {str(e)}")
    
    def _get_standard_field_definitions(self) -> List[Dict[str, Any]]:
        """Standard field definitions for all components."""
        return [
            {
                "column": "reference",
                "name": "Reference",
                "visible_on_add": True,
                "visible_in_chooser": True,
                "show_name": False
            },
            {
                "column": "value",
                "name": "Value", 
                "visible_on_add": True,
                "visible_in_chooser": True,
                "show_name": False
            },
            {
                "column": "description",
                "name": "Description",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            },
            {
                "column": "manufacturer",
                "name": "Manufacturer",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            },
            {
                "column": "mpn",
                "name": "MPN",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            },
            {
                "column": "package",
                "name": "Package",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            },
            {
                "column": "datasheet",
                "name": "Datasheet",
                "visible_on_add": False,
                "visible_in_chooser": False,
                "show_name": True
            }
        ]
    
    def _get_resistor_field_definitions(self) -> List[Dict[str, Any]]:
        """Field definitions specific to resistors."""
        fields = self._get_standard_field_definitions()
        fields.extend([
            {
                "column": "tolerance",
                "name": "Tolerance",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            },
            {
                "column": "power",
                "name": "Power",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            }
        ])
        return fields
    
    def _get_capacitor_field_definitions(self) -> List[Dict[str, Any]]:
        """Field definitions specific to capacitors."""
        fields = self._get_standard_field_definitions()
        fields.extend([
            {
                "column": "voltage",
                "name": "Voltage",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            },
            {
                "column": "tolerance",
                "name": "Tolerance",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            }
        ])
        return fields
    
    def _get_inductor_field_definitions(self) -> List[Dict[str, Any]]:
        """Field definitions specific to inductors."""
        fields = self._get_standard_field_definitions()
        fields.extend([
            {
                "column": "current",
                "name": "Current",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            }
        ])
        return fields
    
    def _get_ic_field_definitions(self) -> List[Dict[str, Any]]:
        """Field definitions specific to ICs."""
        fields = self._get_standard_field_definitions()
        fields.extend([
            {
                "column": "voltage",
                "name": "Supply Voltage",
                "visible_on_add": False,
                "visible_in_chooser": True,
                "show_name": True
            }
        ])
        return fields
    
    def generate_migration_report(self, component_mappings: Dict[str, List]) -> None:
        """
        Generate a migration report with statistics and issues.
        
        Args:
            component_mappings: Dictionary of component mappings by table
            
        Raises:
            ConfigurationError: If report generation fails
        """
        self.logger.info("Generating migration report")
        
        try:
            report = {
                "migration_summary": {
                    "total_tables": len(component_mappings),
                    "total_components": 0,
                    "high_confidence": 0,
                    "medium_confidence": 0,
                    "low_confidence": 0
                },
                "table_details": {},
                "issues": [],
                "recommendations": []
            }
            
            # Add timestamp to report
            report["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Process each table
            for table_name, mappings in component_mappings.items():
                table_stats = {
                    "component_count": len(mappings),
                    "high_confidence": 0,
                    "medium_confidence": 0,
                    "low_confidence": 0,
                    "missing_symbols": [],
                    "missing_footprints": []
                }
                
                # Check for issues in this table
                for mapping in mappings:
                    report["migration_summary"]["total_components"] += 1
                    
                    # Categorize by confidence level
                    if mapping.confidence > 0.8:
                        report["migration_summary"]["high_confidence"] += 1
                        table_stats["high_confidence"] += 1
                    elif mapping.confidence >= 0.5:
                        report["migration_summary"]["medium_confidence"] += 1
                        table_stats["medium_confidence"] += 1
                    else:
                        report["migration_summary"]["low_confidence"] += 1
                        table_stats["low_confidence"] += 1
                    
                    # Check for missing symbols or footprints
                    if not mapping.kicad_symbol or mapping.kicad_symbol == 'Device:U':
                        if mapping.altium_symbol not in table_stats["missing_symbols"]:
                            table_stats["missing_symbols"].append(mapping.altium_symbol)
                            
                    if not mapping.kicad_footprint or mapping.kicad_footprint == 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm':
                        if mapping.altium_footprint not in table_stats["missing_footprints"]:
                            table_stats["missing_footprints"].append(mapping.altium_footprint)
                
                report["table_details"][table_name] = table_stats
                
                # Log table statistics
                self.logger.info(f"Table {table_name}: {table_stats['component_count']} components " +
                               f"({table_stats['high_confidence']} high, " +
                               f"{table_stats['medium_confidence']} medium, " +
                               f"{table_stats['low_confidence']} low confidence)")
                
                if table_stats["missing_symbols"]:
                    self.logger.warning(f"Table {table_name}: {len(table_stats['missing_symbols'])} missing symbols")
                    
                if table_stats["missing_footprints"]:
                    self.logger.warning(f"Table {table_name}: {len(table_stats['missing_footprints'])} missing footprints")
            
            # Generate recommendations
            recommendations = []
            
            if report["migration_summary"]["low_confidence"] > 0:
                recommendations.append(
                    f"Review {report['migration_summary']['low_confidence']} low-confidence mappings manually"
                )
            
            # Check for missing symbols and footprints across all tables
            missing_symbols_count = sum(len(table["missing_symbols"]) for table in report["table_details"].values())
            missing_footprints_count = sum(len(table["missing_footprints"]) for table in report["table_details"].values())
            
            if missing_symbols_count > 0:
                recommendations.append(
                    f"Create custom symbol mappings for {missing_symbols_count} missing symbols"
                )
                
            if missing_footprints_count > 0:
                recommendations.append(
                    f"Create custom footprint mappings for {missing_footprints_count} missing footprints"
                )
            
            report["recommendations"] = recommendations
            
            # Add issues to report
            if report["migration_summary"]["low_confidence"] > 0:
                report["issues"].append({
                    "type": "low_confidence",
                    "count": report["migration_summary"]["low_confidence"],
                    "description": "Components with low confidence mapping"
                })
                
            if missing_symbols_count > 0:
                report["issues"].append({
                    "type": "missing_symbols",
                    "count": missing_symbols_count,
                    "description": "Altium symbols without specific KiCAD mapping"
                })
                
            if missing_footprints_count > 0:
                report["issues"].append({
                    "type": "missing_footprints",
                    "count": missing_footprints_count,
                    "description": "Altium footprints without specific KiCAD mapping"
                })
            
            # Save report
            report_path = self.output_dir / "migration_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Generate summary
            summary = (
                f"Migration Summary:\n"
                f"- Total Components: {report['migration_summary']['total_components']}\n"
                f"- High Confidence: {report['migration_summary']['high_confidence']} "
                f"({report['migration_summary']['high_confidence'] / max(1, report['migration_summary']['total_components']) * 100:.1f}%)\n"
                f"- Medium Confidence: {report['migration_summary']['medium_confidence']} "
                f"({report['migration_summary']['medium_confidence'] / max(1, report['migration_summary']['total_components']) * 100:.1f}%)\n"
                f"- Low Confidence: {report['migration_summary']['low_confidence']} "
                f"({report['migration_summary']['low_confidence'] / max(1, report['migration_summary']['total_components']) * 100:.1f}%)\n"
            )
            
            self.logger.info(f"Generated migration report: {report_path}")
            self.logger.info(summary)
            
        except Exception as e:
            self.logger.error(f"Error generating migration report: {str(e)}")
            raise ConfigurationError(f"Failed to generate migration report: {str(e)}")
    
    def generate(self, component_mappings: Dict[str, List]) -> Dict[str, str]:
        """
        Generate complete KiCAD database library.
        
        Args:
            component_mappings: Dictionary of component mappings by table
            
        Returns:
            Dictionary with paths to generated files
            
        Raises:
            KiCADGenerationError: If generation fails
        """
        self.logger.info("Starting KiCAD database library generation")
        start_time = time.time()
        
        try:
            # Create database schema
            self.logger.info("Step 1/5: Creating database schema")
            self.create_database_schema()
            
            # Populate categories
            self.logger.info("Step 2/5: Populating categories")
            category_ids = self.populate_categories(component_mappings)
            
            # Populate components
            self.logger.info("Step 3/5: Populating components")
            self.populate_components(component_mappings, category_ids)
            
            # Generate KiCAD database library file
            self.logger.info("Step 4/5: Generating KiCAD database library file")
            self.generate_kicad_dblib_file()
            
            # Generate migration report
            self.logger.info("Step 5/5: Generating migration report")
            self.generate_migration_report(component_mappings)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            self.logger.info(f"KiCAD database library generation completed in {elapsed_time:.2f} seconds")
            
            # Return paths to generated files
            result = {
                "database_path": str(self.db_path),
                "dblib_path": str(self.dblib_path),
                "output_directory": str(self.output_dir),
                "report_path": str(self.output_dir / "migration_report.json")
            }
            
            self.logger.info(f"Generated files: {', '.join(result.values())}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating KiCAD database library: {str(e)}")
            raise KiCADGenerationError(f"Failed to generate KiCAD database library: {str(e)}")