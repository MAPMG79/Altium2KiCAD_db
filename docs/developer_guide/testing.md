# Testing Framework

This document describes the testing framework for the Altium to KiCAD Database Migration Tool, including the sample data generation system for comprehensive testing.

## Overview

The testing framework consists of several components:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing interactions between components
3. **Performance Tests**: Testing system performance under various conditions
4. **Sample Data Generation**: Creating realistic test data for comprehensive testing

## Sample Data Generation

The `SampleDataGenerator` class provides a sophisticated system for generating realistic component data for testing. This allows for comprehensive testing without requiring actual Altium databases.

### Component Type Specifications

The system defines component types using an enumeration:

```python
class ComponentType(Enum):
    """Enumeration of component types for sample generation"""
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    TRANSISTOR = "transistor"
    IC = "ic"
    CONNECTOR = "connector"
    CRYSTAL = "crystal"
```

Each component type has detailed specifications that define its properties:

```python
def _initialize_component_specs(self) -> Dict[ComponentType, Dict[str, Any]]:
    """Initialize component specifications for realistic data generation"""
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
        # Additional component types...
    }
```

### Package Types

The system defines realistic package types for each component:

```python
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
```

### Generating Components

The `generate_component` method creates realistic component data:

```python
def generate_component(self, comp_type: ComponentType, part_number_prefix: str = None) -> Dict[str, Any]:
    """Generate a single realistic component"""
    specs = self.component_specs[comp_type]
    manufacturer = random.choice(self.manufacturers)
    package = random.choice(self.packages[comp_type])
    
    # Generate part number
    if not part_number_prefix:
        part_number_prefix = f"{comp_type.value[:3].upper()}"
    
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
        'Comment': f"{comp_type.value.title()} component"
    }
    
    # Add type-specific properties
    if comp_type == ComponentType.RESISTOR:
        component.update({
            'Value': random.choice(specs['values']),
            'Tolerance': random.choice(specs['tolerances']),
            'Power': random.choice(specs['powers']),
            'Temperature Coefficient': f"{random.randint(10, 200)}ppm/°C"
        })
    
    # Additional component type handling...
    
    return component
```

### Creating Test Databases

The `create_sample_database` method creates a SQLite database with realistic component data:

```python
def create_sample_database(self, db_path: str, table_configs: Dict[str, Dict[str, Any]]) -> str:
    """Create sample SQLite database with realistic data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for table_name, config in table_configs.items():
        component_count = config.get('component_count', 50)
        component_types = config.get('component_types', list(ComponentType))
        
        # Generate component data
        components = self.generate_table_data(table_name, component_count, component_types)
        
        if components:
            # Create table based on first component's fields
            fields = list(components[0].keys())
            escaped_fields = [f'[{field}]' for field in fields]
            
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS [{table_name}] (
                    {', '.join(f'{field} TEXT' for field in escaped_fields)}
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
```

### Creating Altium DbLib Files

The `create_sample_dblib` method creates an Altium DbLib file that points to the sample database:

```python
def create_sample_dblib(self, dblib_path: str, db_path: str, 
                       table_configs: Dict[str, Dict[str, Any]]) -> str:
    """Create sample Altium .DbLib file"""
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
```

### Generating Complete Sample Projects

The `generate_complete_sample` method creates a complete sample project with database, DbLib file, and metadata:

```python
def generate_complete_sample(self, project_name: str = "SampleProject", 
                           num_tables: int = 4) -> Dict[str, str]:
    """Generate complete sample project with database and DbLib file"""
    
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
        'created_at': datetime.now().isoformat(),
        'database_path': str(db_path),
        'dblib_path': str(dblib_path),
        'table_configs': table_configs,
        'total_components': sum(config['component_count'] for config in table_configs.values())
    }
    
    metadata_path = self.output_dir / f"{project_name}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return {
        'database_path': str(db_path),
        'dblib_path': str(dblib_path),
        'metadata_path': str(metadata_path)
    }
```

## Using the Sample Data Generator

### Basic Usage

```python
# Create a sample data generator
generator = SampleDataGenerator(output_dir="test_data")

# Generate a complete sample project
sample_project = generator.generate_complete_sample(
    project_name="TestProject",
    num_tables=4
)

print(f"Generated sample project at: {sample_project['database_path']}")
```

### Customizing Component Types

```python
# Generate specific component types
resistors = generator.generate_table_data(
    table_name="CustomResistors",
    component_count=50,
    component_types=[ComponentType.RESISTOR]
)

# Create a database with custom components
db_path = "test_data/custom_components.db"
generator.create_sample_database(
    db_path=db_path,
    table_configs={
        "CustomResistors": {
            "component_count": 50,
            "component_types": [ComponentType.RESISTOR]
        },
        "CustomCapacitors": {
            "component_count": 30,
            "component_types": [ComponentType.CAPACITOR]
        }
    }
)
```

### Generating Individual Components

```python
# Generate a single resistor
resistor = generator.generate_component(
    comp_type=ComponentType.RESISTOR,
    part_number_prefix="RES"
)

print(f"Generated resistor: {resistor['Part Number']}")
print(f"Value: {resistor['Value']}")
print(f"Tolerance: {resistor['Tolerance']}")
```

## Integration with Test Framework

The sample data generator integrates with the test framework to provide realistic test data:

```python
# test_migration_with_sample_data.py
import unittest
from migration_tool.core import MigrationEngine
from tests.utils import SampleDataGenerator

class TestMigrationWithSampleData(unittest.TestCase):
    
    def setUp(self):
        # Create sample data for testing
        self.generator = SampleDataGenerator(output_dir="test_temp")
        self.sample_project = self.generator.generate_complete_sample(
            project_name="TestMigration",
            num_tables=2
        )
        
        # Initialize migration engine
        self.engine = MigrationEngine()
    
    def test_migration_with_sample_data(self):
        # Perform migration
        result = self.engine.migrate(
            altium_dblib_path=self.sample_project['dblib_path'],
            output_path="test_temp/output.db"
        )
        
        # Verify migration results
        self.assertTrue(result['success'])
        self.assertEqual(result['total_components'], 180)  # 100 resistors + 80 capacitors
    
    def tearDown(self):
        # Clean up test data
        import shutil
        shutil.rmtree("test_temp")
```

## Automated Test Data Generation

The repository includes a script for generating test data:

```bash
# Generate sample data for testing
python scripts/generate_sample_data.py --output-dir test_data --project-name TestProject --tables 4
```

## Best Practices

1. **Use Realistic Data**: Generate data that closely resembles real-world components
2. **Test Edge Cases**: Include edge cases in your test data
3. **Vary Component Counts**: Test with different numbers of components
4. **Include Invalid Data**: Test how the system handles invalid or malformed data
5. **Automate Data Generation**: Integrate data generation into your CI/CD pipeline

## Conclusion

The sample data generation system provides a powerful way to create realistic test data for comprehensive testing of the Altium to KiCAD Database Migration Tool. By using this system, you can ensure that your code is thoroughly tested with a wide variety of component data.