#!/usr/bin/env python3
"""
Sample Data Generation Script for Altium to KiCAD Database Migration Tool.

This script generates sample data for testing the Altium to KiCAD Migration Tool,
including:
- Sample Altium .DbLib files
- Sample database files (SQLite, Access MDB if possible)
- Sample component data with realistic values
- Test cases for different component types
"""

import argparse
import configparser
import json
import os
import random
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class ComponentType:
    """Component type constants."""
    
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    TRANSISTOR = "transistor"
    IC = "ic"
    CONNECTOR = "connector"
    CRYSTAL = "crystal"


class SampleDataGenerator:
    """Generate sample data for testing the migration tool."""
    
    def __init__(self, output_dir: str):
        """Initialize the generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Component specifications
        self.component_specs = self._initialize_component_specs()
        
        # Manufacturers
        self.manufacturers = [
            "Vishay", "Yageo", "Murata", "TDK", "Samsung", "Panasonic",
            "Texas Instruments", "Analog Devices", "Maxim", "Linear Technology",
            "STMicroelectronics", "NXP", "Infineon", "ON Semiconductor",
            "Microchip", "Atmel", "Intel", "Broadcom", "Qualcomm"
        ]
        
        # Package types
        self.packages = {
            ComponentType.RESISTOR: ["0201", "0402", "0603", "0805", "1206", "1210", "2010", "2512"],
            ComponentType.CAPACITOR: ["0201", "0402", "0603", "0805", "1206", "1210", "1812", "2220"],
            ComponentType.INDUCTOR: ["0603", "0805", "1206", "1210", "1812", "2520"],
            ComponentType.DIODE: ["SOD-123", "SOD-323", "SOD-523", "SMA", "SMB"],
            ComponentType.TRANSISTOR: ["SOT-23", "SOT-23-5", "SOT-323", "TO-252", "TO-263"],
            ComponentType.IC: ["SOIC-8", "TSSOP-16", "QFN-32", "TQFP-44", "BGA-64"],
            ComponentType.CONNECTOR: ["2.54mm", "1.27mm", "0.5mm", "USB", "RJ45"],
            ComponentType.CRYSTAL: ["3.2x2.5mm", "5x3.2mm", "7x5mm", "HC-49"]
        }
    
    def _initialize_component_specs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize component specifications for realistic data generation."""
        return {
            ComponentType.RESISTOR: {
                'values': ['1R', '2.2R', '4.7R', '10R', '22R', '47R', '100R', '220R', '470R', 
                          '1K', '2.2K', '4.7K', '10K', '22K', '47K', '100K', '220K', '470K', '1M'],
                'tolerances': ['1%', '5%', '10%'],
                'powers': ['0.063W', '0.1W', '0.125W', '0.25W', '0.5W', '1W'],
                'symbol': 'Resistor'
            },
            ComponentType.CAPACITOR: {
                'values': ['1pF', '10pF', '100pF', '1nF', '10nF', '100nF', '1uF', '10uF', '100uF', '1000uF'],
                'voltages': ['6.3V', '10V', '16V', '25V', '35V', '50V', '100V', '200V'],
                'tolerances': ['5%', '10%', '20%'],
                'symbol': 'Capacitor'
            },
            ComponentType.INDUCTOR: {
                'values': ['1nH', '10nH', '100nH', '1uH', '10uH', '100uH', '1mH'],
                'currents': ['0.1A', '0.2A', '0.5A', '1A', '2A', '5A'],
                'tolerances': ['10%', '20%'],
                'symbol': 'Inductor'
            },
            ComponentType.DIODE: {
                'types': ['Standard', 'Schottky', 'Zener', 'LED'],
                'voltages': ['20V', '40V', '60V', '100V', '200V'],
                'currents': ['0.1A', '0.2A', '0.5A', '1A', '3A'],
                'symbol': 'Diode'
            },
            ComponentType.TRANSISTOR: {
                'types': ['NPN', 'PNP', 'NMOS', 'PMOS'],
                'voltages': ['20V', '30V', '60V', '100V'],
                'currents': ['0.1A', '0.5A', '1A', '2A', '5A'],
                'symbol': 'Transistor'
            },
            ComponentType.IC: {
                'types': ['Op-Amp', 'Comparator', 'Logic', 'MCU', 'ADC', 'DAC', 'Regulator'],
                'supply_voltages': ['3.3V', '5V', '12V', '15V'],
                'pin_counts': [8, 14, 16, 20, 28, 32, 44, 64, 100],
                'symbol': 'IC'
            },
            ComponentType.CONNECTOR: {
                'types': ['Header', 'Socket', 'USB', 'Audio', 'Power'],
                'pin_counts': [2, 4, 6, 8, 10, 16, 20, 24],
                'pitches': ['2.54mm', '1.27mm', '0.5mm'],
                'symbol': 'Connector'
            },
            ComponentType.CRYSTAL: {
                'frequencies': ['32.768kHz', '8MHz', '12MHz', '16MHz', '20MHz', '25MHz'],
                'tolerances': ['10ppm', '20ppm', '50ppm'],
                'load_capacitances': ['12pF', '18pF', '20pF'],
                'symbol': 'Crystal'
            }
        }
    
    def generate_component(self, comp_type: str, part_number_prefix: str = None) -> Dict[str, Any]:
        """Generate a single realistic component."""
        specs = self.component_specs[comp_type]
        manufacturer = random.choice(self.manufacturers)
        package = random.choice(self.packages[comp_type])
        
        # Generate part number
        if not part_number_prefix:
            part_number_prefix = f"{comp_type[:3].upper()}"
        
        part_number = f"{part_number_prefix}-{random.randint(1000, 9999)}-{package}"
        
        # Base component data
        component = {
            'Part Number': part_number,
            'Symbol': specs['symbol'],
            'Footprint': package,
            'Manufacturer': manufacturer,
            'Manufacturer Part Number': f"{manufacturer[:3].upper()}{random.randint(1000, 9999)}",
            'Package': package,
            'Description': self._generate_description(comp_type, specs),
            'Datasheet': f"https://www.{manufacturer.lower().replace(' ', '')}.com/ds/{part_number}.pdf",
            'Supplier': random.choice(['Digi-Key', 'Mouser', 'Arrow', 'Avnet', 'RS Components']),
            'Supplier Part Number': f"SP{random.randint(100000, 999999)}",
            'Comment': f"{comp_type.title()} component"
        }
        
        # Add type-specific properties
        if comp_type == ComponentType.RESISTOR:
            component.update({
                'Value': random.choice(specs['values']),
                'Tolerance': random.choice(specs['tolerances']),
                'Power': random.choice(specs['powers']),
                'Temperature Coefficient': f"{random.randint(10, 200)}ppm/°C"
            })
        
        elif comp_type == ComponentType.CAPACITOR:
            component.update({
                'Value': random.choice(specs['values']),
                'Voltage': random.choice(specs['voltages']),
                'Tolerance': random.choice(specs['tolerances']),
                'Dielectric': random.choice(['C0G', 'X7R', 'Y5V', 'X5R'])
            })
        
        elif comp_type == ComponentType.INDUCTOR:
            component.update({
                'Value': random.choice(specs['values']),
                'Current': random.choice(specs['currents']),
                'Tolerance': random.choice(specs['tolerances']),
                'SRF': f"{random.randint(10, 1000)}MHz"
            })
        
        elif comp_type == ComponentType.DIODE:
            diode_type = random.choice(specs['types'])
            component.update({
                'Type': diode_type,
                'Forward Voltage': f"{random.uniform(0.2, 3.3):.1f}V",
                'Reverse Voltage': random.choice(specs['voltages']),
                'Forward Current': random.choice(specs['currents'])
            })
            if diode_type == 'Zener':
                component['Zener Voltage'] = f"{random.uniform(2.4, 15.0):.1f}V"
        
        elif comp_type == ComponentType.TRANSISTOR:
            trans_type = random.choice(specs['types'])
            component.update({
                'Type': trans_type,
                'Collector-Emitter Voltage': random.choice(specs['voltages']),
                'Collector Current': random.choice(specs['currents']),
                'hFE': random.randint(50, 400)
            })
        
        elif comp_type == ComponentType.IC:
            ic_type = random.choice(specs['types'])
            component.update({
                'Type': ic_type,
                'Supply Voltage': random.choice(specs['supply_voltages']),
                'Pin Count': random.choice(specs['pin_counts']),
                'Operating Temperature': f"-40°C to +85°C"
            })
        
        elif comp_type == ComponentType.CONNECTOR:
            conn_type = random.choice(specs['types'])
            component.update({
                'Type': conn_type,
                'Pin Count': random.choice(specs['pin_counts']),
                'Pitch': random.choice(specs['pitches']),
                'Current Rating': f"{random.uniform(0.5, 10.0):.1f}A"
            })
        
        elif comp_type == ComponentType.CRYSTAL:
            component.update({
                'Frequency': random.choice(specs['frequencies']),
                'Tolerance': random.choice(specs['tolerances']),
                'Load Capacitance': random.choice(specs['load_capacitances']),
                'ESR': f"{random.randint(10, 200)}Ohm"
            })
        
        return component
    
    def _generate_description(self, comp_type: str, specs: Dict[str, Any]) -> str:
        """Generate realistic component description."""
        if comp_type == ComponentType.RESISTOR:
            value = random.choice(specs['values'])
            tolerance = random.choice(specs['tolerances'])
            return f"{value} Ohm {tolerance} Thick Film Resistor"
        
        elif comp_type == ComponentType.CAPACITOR:
            value = random.choice(specs['values'])
            voltage = random.choice(specs['voltages'])
            return f"{value} {voltage} Ceramic Capacitor"
        
        elif comp_type == ComponentType.INDUCTOR:
            value = random.choice(specs['values'])
            return f"{value} Multilayer Chip Inductor"
        
        elif comp_type == ComponentType.DIODE:
            diode_type = random.choice(specs['types'])
            return f"{diode_type} Diode"
        
        elif comp_type == ComponentType.TRANSISTOR:
            trans_type = random.choice(specs['types'])
            return f"{trans_type} Transistor"
        
        elif comp_type == ComponentType.IC:
            ic_type = random.choice(specs['types'])
            return f"{ic_type} Integrated Circuit"
        
        elif comp_type == ComponentType.CONNECTOR:
            conn_type = random.choice(specs['types'])
            pins = random.choice(specs['pin_counts'])
            return f"{pins}-Pin {conn_type} Connector"
        
        elif comp_type == ComponentType.CRYSTAL:
            freq = random.choice(specs['frequencies'])
            return f"{freq} Crystal Oscillator"
        
        return f"{comp_type.title()} Component"
    
    def generate_table_data(self, table_name: str, component_count: int, 
                           component_types: List[str] = None) -> List[Dict[str, Any]]:
        """Generate a table of components."""
        if component_types is None:
            component_types = list(self.component_specs.keys())
        
        components = []
        for i in range(component_count):
            comp_type = random.choice(component_types)
            part_prefix = f"{table_name[:3].upper()}"
            component = self.generate_component(comp_type, part_prefix)
            components.append(component)
        
        return components
    
    def create_sample_database(self, db_path: str, table_configs: Dict[str, Dict[str, Any]]) -> str:
        """Create sample SQLite database with realistic data."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for table_name, config in table_configs.items():
            component_count = config.get('component_count', 50)
            component_types = config.get('component_types', list(self.component_specs.keys()))
            
            # Generate component data
            components = self.generate_table_data(table_name, component_count, component_types)
            
            if components:
                # Create table based on first component's fields
                fields = list(components[0].keys())
                field_defs = [f'[{field}] TEXT' for field in fields]
                
                create_sql = f"""
                    CREATE TABLE [{table_name}] (
                        {', '.join(field_defs)}
                    )
                """
                cursor.execute(create_sql)
                
                # Insert components
                placeholders = ', '.join(['?' for _ in fields])
                insert_sql = f"INSERT INTO [{table_name}] VALUES ({placeholders})"
                
                for component in components:
                    values = [component.get(field, '') for field in fields]
                    cursor.execute(insert_sql, values)
                
                print(f"Created table '{table_name}' with {len(components)} components")
        
        conn.commit()
        conn.close()
        
        return db_path
    
    def create_sample_dblib(self, dblib_path: str, db_path: str, 
                           table_configs: Dict[str, Dict[str, Any]]) -> str:
        """Create sample Altium .DbLib file."""
        config = configparser.ConfigParser()
        
        # Database connection section
        config['DatabaseLinks'] = {
            'ConnectionString': f'Driver=SQLite3;Database={db_path};',
            'AddMode': '3',
            'RemoveMode': '1',
            'UpdateMode': '2',
            'ViewMode': '0',
            'LeftQuote': '[',
            'RightQuote': ']',
            'QuoteTableNames': '1',
            'UseTableSchemaName': '0',
            'DefaultColumnType': 'VARCHAR(255)',
            'LibraryDatabaseType': '',
            'LibraryDatabasePath': '',
            'DatabasePathRelative': '0'
        }
        
        # Table configurations
        for i, (table_name, table_config) in enumerate(table_configs.items(), 1):
            config[f'Table{i}'] = {
                'SchemaName': '',
                'TableName': table_name,
                'Enabled': 'True',
                'UserWhere': '0',
                'UserWhereText': '',
                'Key': 'Part Number',
                'Symbols': 'Symbol',
                'Footprints': 'Footprint',
                'Description': 'Description'
            }
        
        # Write configuration file
        with open(dblib_path, 'w') as f:
            config.write(f)
        
        return dblib_path
    
    def generate_complete_sample(self, project_name: str = "SampleProject", 
                               num_tables: int = 4) -> Dict[str, str]:
        """Generate complete sample project with database and DbLib file."""
        
        # Define table configurations
        table_configs = {
            'Resistors': {
                'component_count': 100,
                'component_types': [ComponentType.RESISTOR]
            },
            'Capacitors': {
                'component_count': 80,
                'component_types': [ComponentType.CAPACITOR]
            },
            'Semiconductors': {
                'component_count': 60,
                'component_types': [ComponentType.DIODE, ComponentType.TRANSISTOR]
            },
            'Integrated_Circuits': {
                'component_count': 40,
                'component_types': [ComponentType.IC]
            }
        }
        
        # Limit to requested number of tables
        if num_tables < len(table_configs):
            table_configs = dict(list(table_configs.items())[:num_tables])
        
        # Create file paths
        db_path = self.output_dir / f"{project_name}.db"
        dblib_path = self.output_dir / f"{project_name}.DbLib"
        
        # Generate database
        self.create_sample_database(str(db_path), table_configs)
        
        # Generate DbLib file
        self.create_sample_dblib(str(dblib_path), str(db_path), table_configs)
        
        # Generate metadata file
        metadata = {
            'project_name': project_name,
            'created_at': str(Path(db_path).stat().st_mtime),
            'database_path': str(db_path),
            'dblib_path': str(dblib_path),
            'table_configs': table_configs,
            'total_components': sum(config['component_count'] for config in table_configs.values())
        }
        
        metadata_path = self.output_dir / f"{project_name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return {
            'database_path': str(db_path),
            'dblib_path': str(dblib_path),
            'metadata_path': str(metadata_path)
        }
    
    def generate_test_cases(self, output_dir: str = None) -> Dict[str, str]:
        """Generate test cases for different scenarios."""
        if output_dir:
            test_dir = Path(output_dir)
        else:
            test_dir = self.output_dir / "test_cases"
        
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_cases = {}
        
        # Test case 1: Basic sample with all component types
        print("Generating basic test case...")
        basic_sample = self.generate_complete_sample(
            project_name="BasicSample",
            num_tables=4
        )
        test_cases["basic"] = basic_sample
        
        # Test case 2: Large dataset
        print("Generating large dataset test case...")
        large_configs = {
            'Large_Components': {
                'component_count': 1000,
                'component_types': list(self.component_specs.keys())
            }
        }
        
        db_path = test_dir / "LargeDataset.db"
        dblib_path = test_dir / "LargeDataset.DbLib"
        
        self.create_sample_database(str(db_path), large_configs)
        self.create_sample_dblib(str(dblib_path), str(db_path), large_configs)
        
        test_cases["large"] = {
            'database_path': str(db_path),
            'dblib_path': str(dblib_path)
        }
        
        # Test case 3: Complex schema
        print("Generating complex schema test case...")
        complex_configs = {
            'Resistors': {
                'component_count': 50,
                'component_types': [ComponentType.RESISTOR]
            },
            'Capacitors': {
                'component_count': 50,
                'component_types': [ComponentType.CAPACITOR]
            },
            'ICs': {
                'component_count': 50,
                'component_types': [ComponentType.IC]
            },
            'Connectors': {
                'component_count': 50,
                'component_types': [ComponentType.CONNECTOR]
            },
            'Misc': {
                'component_count': 50,
                'component_types': [
                    ComponentType.DIODE,
                    ComponentType.TRANSISTOR,
                    ComponentType.INDUCTOR,
                    ComponentType.CRYSTAL
                ]
            }
        }
        
        db_path = test_dir / "ComplexSchema.db"
        dblib_path = test_dir / "ComplexSchema.DbLib"
        
        self.create_sample_database(str(db_path), complex_configs)
        self.create_sample_dblib(str(dblib_path), str(db_path), complex_configs)
        
        test_cases["complex"] = {
            'database_path': str(db_path),
            'dblib_path': str(dblib_path)
        }
        
        # Save test case metadata
        metadata_path = test_dir / "test_cases.json"
        with open(metadata_path, 'w') as f:
            json.dump(test_cases, f, indent=2, default=str)
        
        print(f"Test cases generated in {test_dir}")
        return test_cases


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate sample data for Altium to KiCAD Migration Tool"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="sample_data",
        help="Output directory for sample data",
    )
    parser.add_argument(
        "--project-name",
        default="SampleProject",
        help="Name for the sample project",
    )
    parser.add_argument(
        "--tables",
        type=int,
        default=4,
        help="Number of component tables to generate",
    )
    parser.add_argument(
        "--components",
        type=int,
        default=100,
        help="Number of components per table",
    )
    parser.add_argument(
        "--test-cases",
        action="store_true",
        help="Generate test cases for different scenarios",
    )
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    
    generator = SampleDataGenerator(args.output_dir)
    
    if args.test_cases:
        generator.generate_test_cases()
    else:
        # Define custom table configurations
        table_configs = {
            'Resistors': {
                'component_count': args.components,
                'component_types': [ComponentType.RESISTOR]
            },
            'Capacitors': {
                'component_count': args.components,
                'component_types': [ComponentType.CAPACITOR]
            },
            'Semiconductors': {
                'component_count': args.components,
                'component_types': [ComponentType.DIODE, ComponentType.TRANSISTOR]
            },
            'Integrated_Circuits': {
                'component_count': args.components,
                'component_types': [ComponentType.IC]
            }
        }
        
        # Limit to requested number of tables
        if args.tables < len(table_configs):
            table_configs = dict(list(table_configs.items())[:args.tables])
        
        # Create file paths
        db_path = Path(args.output_dir) / f"{args.project_name}.db"
        dblib_path = Path(args.output_dir) / f"{args.project_name}.DbLib"
        
        # Generate database
        generator.create_sample_database(str(db_path), table_configs)
        
        # Generate DbLib file
        generator.create_sample_dblib(str(dblib_path), str(db_path), table_configs)
        
        print(f"Sample data generated:")
        print(f"  Database: {db_path}")
        print(f"  DbLib file: {dblib_path}")
        print(f"  Total components: {sum(config['component_count'] for config in table_configs.values())}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())