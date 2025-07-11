import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

class KiCADDbLibGenerator:
    """Generator for KiCAD database libraries from mapped component data"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.output_dir / "components.db"
        self.dblib_path = self.output_dir / "components.kicad_dbl"
        
    def create_database_schema(self) -> None:
        """Create SQLite database with KiCAD-compatible schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS components")
        cursor.execute("DROP TABLE IF EXISTS categories")
        
        # Create categories table
        cursor.execute("""
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                parent_id INTEGER REFERENCES categories(id)
            )
        """)
        
        # Create main components table
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
        cursor.execute("CREATE INDEX idx_components_symbol ON components(symbol)")
        cursor.execute("CREATE INDEX idx_components_footprint ON components(footprint)")
        cursor.execute("CREATE INDEX idx_components_mpn ON components(mpn)")
        cursor.execute("CREATE INDEX idx_components_manufacturer ON components(manufacturer)")
        cursor.execute("CREATE INDEX idx_components_category ON components(category_id)")
        
        # Create views for different component types
        self._create_component_views(cursor)
        
        conn.commit()
        conn.close()
        
    def _create_component_views(self, cursor) -> None:
        """Create views for different component categories"""
        
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
    
    def populate_categories(self, component_mappings: Dict[str, List]) -> Dict[str, int]:
        """Populate categories table and return category name to ID mapping"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Define category hierarchy
        categories = [
            ('Resistors', 'Resistive components'),
            ('Capacitors', 'Capacitive components'),
            ('Inductors', 'Inductive components'),
            ('Diodes', 'Diode components'),
            ('Transistors', 'Transistor components'),
            ('Integrated Circuits', 'IC components'),
            ('Connectors', 'Connector components'),
            ('Mechanical', 'Mechanical components')
        ]
        
        category_ids = {}
        for name, description in categories:
            cursor.execute(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                (name, description)
            )
            category_ids[name] = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return category_ids
    
    def _categorize_component(self, mapping, category_ids: Dict[str, int]) -> int:
        """Determine component category based on mapping data"""
        description = mapping.field_mappings.get('Description', '').lower()
        symbol = mapping.kicad_symbol.lower()
        
        # Category detection logic
        if any(term in description for term in ['resistor', 'resistance']) or ':r' in symbol:
            return category_ids.get('Resistors', category_ids['Uncategorized'])
        elif any(term in description for term in ['capacitor', 'capacitance']) or ':c' in symbol:
            return category_ids.get('Capacitors', category_ids['Uncategorized'])
        elif any(term in description for term in ['inductor', 'inductance']) or ':l' in symbol:
            return category_ids.get('Inductors', category_ids['Uncategorized'])
        else:
            return category_ids.get('Uncategorized', category_ids['Uncategorized'])
    
    def generate_kicad_dblib_file(self, component_mappings: Dict[str, List]) -> None:
        """Generate KiCAD .kicad_dbl configuration file"""
        
        # Build library configuration
        config = {
            "meta": {
                "version": 1.0
            },
            "name": "Migrated Altium Library",
            "description": "Components migrated from Altium database library",
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
            }
        ]
        
        config["libraries"] = library_definitions
        
        # Write configuration file
        with open(self.dblib_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _get_standard_field_definitions(self) -> List[Dict[str, Any]]:
        """Standard field definitions for all components"""
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
            }
        ]
    
    def generate(self, component_mappings: Dict[str, List]) -> Dict[str, str]:
        """Generate complete KiCAD database library"""
        print("Creating database schema...")
        self.create_database_schema()
        
        print("Populating categories...")
        category_ids = self.populate_categories(component_mappings)
        
        print("Generating KiCAD database library file...")
        self.generate_kicad_dblib_file(component_mappings)
        
        return {
            "database_path": str(self.db_path),
            "dblib_path": str(self.dblib_path),
            "output_directory": str(self.output_dir)
        }