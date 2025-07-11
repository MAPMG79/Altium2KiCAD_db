# Creating Custom Mapping Rules

This tutorial explains how to create and use custom mapping rules to improve the accuracy of component mapping in the Altium to KiCAD Database Migration Tool. Custom mapping rules allow you to define specific patterns for matching Altium components to their KiCAD equivalents.

## Why Use Custom Mapping Rules?

The default mapping algorithms in the tool work well for standard components, but you may need custom rules for:

1. **Company-specific components**: Components with naming conventions specific to your organization
2. **Specialized components**: Unique or specialized components not commonly found in standard libraries
3. **Inconsistent naming**: Components with inconsistent or non-standard naming in your Altium libraries
4. **Higher accuracy**: Achieving higher confidence scores for critical components
5. **Specific symbol/footprint requirements**: Ensuring components map to specific KiCAD symbols and footprints

## Understanding Mapping Rules

Mapping rules consist of three main types:

1. **Symbol Mapping**: Maps Altium symbols to KiCAD symbols
2. **Footprint Mapping**: Maps Altium footprints to KiCAD footprints
3. **Category Mapping**: Maps Altium component categories to KiCAD categories

Each rule includes:
- An Altium pattern (regular expression)
- A corresponding KiCAD value
- A confidence score (0.0 to 1.0)

## Basic Mapping Rules File

A mapping rules file is a YAML file with the following structure:

```yaml
symbols:
  - altium_pattern: "pattern1"
    kicad_symbol: "kicad_symbol1"
    confidence: 0.9
  
  - altium_pattern: "pattern2"
    kicad_symbol: "kicad_symbol2"
    confidence: 0.8

footprints:
  - altium_pattern: "pattern3"
    kicad_footprint: "kicad_footprint1"
    confidence: 0.9
  
  - altium_pattern: "pattern4"
    kicad_footprint: "kicad_footprint2"
    confidence: 0.8

categories:
  - altium_pattern: "pattern5"
    kicad_category: "kicad_category1"
    confidence: 1.0
  
  - altium_pattern: "pattern6"
    kicad_category: "kicad_category2"
    confidence: 1.0
```

## Creating Effective Mapping Rules

### Step 1: Analyze Your Altium Components

Before creating mapping rules, analyze your Altium components to understand their naming patterns:

```bash
# Analyze the database
altium2kicad --analyze --input path/to/library.DbLib --detailed-analysis
```

This will generate a report showing:
- Common component prefixes and suffixes
- Symbol naming patterns
- Footprint naming patterns
- Category distributions

### Step 2: Identify Patterns

Look for patterns in your component names, symbols, and footprints. Common patterns include:

- Prefixes: `RES_`, `CAP_`, `IND_`
- Value indicators: `10K`, `100n`, `1u`
- Package types: `0603`, `SOIC8`, `QFP64`
- Manufacturer prefixes: `TI_`, `ST_`, `NXP_`

### Step 3: Create Regular Expressions

Convert the identified patterns into regular expressions. Here are some examples:

#### Symbol Mapping Examples

```yaml
symbols:
  # Resistors
  - altium_pattern: "^RES_.*"
    kicad_symbol: "Device:R"
    confidence: 0.9
  
  # Specific resistor values
  - altium_pattern: "^RES_(\d+)K.*"
    kicad_symbol: "Device:R"
    confidence: 0.95
  
  # Capacitors
  - altium_pattern: "^CAP_.*"
    kicad_symbol: "Device:C"
    confidence: 0.9
  
  # Polarized capacitors
  - altium_pattern: "^CAP_POL_.*"
    kicad_symbol: "Device:CP"
    confidence: 0.95
  
  # Operational amplifiers
  - altium_pattern: "^OPAMP_.*"
    kicad_symbol: "Amplifier_Operational:LM358"
    confidence: 0.8
  
  # Specific op-amp
  - altium_pattern: "^OPAMP_LM358.*"
    kicad_symbol: "Amplifier_Operational:LM358"
    confidence: 0.95
```

#### Footprint Mapping Examples

```yaml
footprints:
  # SMD resistors
  - altium_pattern: ".*0603.*"
    kicad_footprint: "Resistor_SMD:R_0603_1608Metric"
    confidence: 0.9
  
  - altium_pattern: ".*0805.*"
    kicad_footprint: "Resistor_SMD:R_0805_2012Metric"
    confidence: 0.9
  
  # SOIC packages
  - altium_pattern: ".*SOIC-8.*"
    kicad_footprint: "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    confidence: 0.9
  
  - altium_pattern: ".*SOIC-16.*"
    kicad_footprint: "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
    confidence: 0.9
  
  # QFP packages
  - altium_pattern: ".*QFP-64.*"
    kicad_footprint: "Package_QFP:TQFP-64_10x10mm_P0.5mm"
    confidence: 0.9
```

#### Category Mapping Examples

```yaml
categories:
  - altium_pattern: "Resistors"
    kicad_category: "Passive Components/Resistors"
    confidence: 1.0
  
  - altium_pattern: "Capacitors"
    kicad_category: "Passive Components/Capacitors"
    confidence: 1.0
  
  - altium_pattern: "Integrated Circuits"
    kicad_category: "Integrated Circuits"
    confidence: 1.0
  
  - altium_pattern: "Connectors"
    kicad_category: "Connectors"
    confidence: 1.0
```

### Step 4: Test Your Rules

Test your mapping rules on a small subset of components before applying them to your entire library:

```bash
# Test mapping rules
altium2kicad --input path/to/library.DbLib --output test_output/ --custom-rules path/to/mapping_rules.yaml --component-limit 10 --verbose
```

Review the mapping results and adjust your rules as needed.

## Advanced Mapping Techniques

### Field-Based Mapping

You can create more specific rules by mapping based on component fields:

```yaml
field_mappings:
  - field: "Value"
    altium_pattern: "10K"
    kicad_symbol: "Device:R"
    kicad_value: "10k"
    confidence: 0.95
  
  - field: "Description"
    altium_pattern: ".*resistor.*"
    kicad_symbol: "Device:R"
    confidence: 0.8
  
  - field: "Manufacturer"
    altium_pattern: "Texas Instruments"
    kicad_prefix: "TI_"
    confidence: 0.9
```

### Hierarchical Mapping

You can create hierarchical rules that apply in sequence:

```yaml
hierarchical_mappings:
  - name: "Resistors"
    match:
      field: "Category"
      pattern: "Resistors"
    rules:
      - match:
          field: "Footprint"
          pattern: ".*0603.*"
        apply:
          kicad_symbol: "Device:R"
          kicad_footprint: "Resistor_SMD:R_0603_1608Metric"
          confidence: 0.95
      
      - match:
          field: "Footprint"
          pattern: ".*0805.*"
        apply:
          kicad_symbol: "Device:R"
          kicad_footprint: "Resistor_SMD:R_0805_2012Metric"
          confidence: 0.95
```

### Direct Mappings

For critical components, you can create direct one-to-one mappings:

```yaml
direct_mappings:
  - altium_libref: "LM358"
    kicad_symbol: "Amplifier_Operational:LM358"
    kicad_footprint: "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    confidence: 1.0
  
  - altium_libref: "ATmega328P"
    kicad_symbol: "MCU_Microchip_ATmega:ATmega328P-AU"
    kicad_footprint: "Package_QFP:TQFP-32_7x7mm_P0.8mm"
    confidence: 1.0
```

## Real-World Examples

### Example 1: Resistor Library

```yaml
# mapping_rules_resistors.yaml
symbols:
  # Standard resistors
  - altium_pattern: "^RES.*"
    kicad_symbol: "Device:R"
    confidence: 0.9
  
  # Potentiometers
  - altium_pattern: "^POT.*"
    kicad_symbol: "Device:R_Potentiometer"
    confidence: 0.9
  
  # Thermistors
  - altium_pattern: "^THERM.*"
    kicad_symbol: "Device:Thermistor"
    confidence: 0.9

footprints:
  # SMD resistors
  - altium_pattern: ".*0402.*"
    kicad_footprint: "Resistor_SMD:R_0402_1005Metric"
    confidence: 0.9
  
  - altium_pattern: ".*0603.*"
    kicad_footprint: "Resistor_SMD:R_0603_1608Metric"
    confidence: 0.9
  
  - altium_pattern: ".*0805.*"
    kicad_footprint: "Resistor_SMD:R_0805_2012Metric"
    confidence: 0.9
  
  - altium_pattern: ".*1206.*"
    kicad_footprint: "Resistor_SMD:R_1206_3216Metric"
    confidence: 0.9
  
  # Through-hole resistors
  - altium_pattern: ".*AXIAL.*"
    kicad_footprint: "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
    confidence: 0.9

categories:
  - altium_pattern: "Resistors"
    kicad_category: "Passive Components/Resistors"
    confidence: 1.0
  
  - altium_pattern: "Potentiometers"
    kicad_category: "Passive Components/Resistors/Potentiometers"
    confidence: 1.0
```

### Example 2: Integrated Circuits Library

```yaml
# mapping_rules_ics.yaml
symbols:
  # Operational amplifiers
  - altium_pattern: "^OPAMP_.*"
    kicad_symbol: "Amplifier_Operational:LM358"
    confidence: 0.8
  
  - altium_pattern: "^OPAMP_LM358.*"
    kicad_symbol: "Amplifier_Operational:LM358"
    confidence: 0.95
  
  - altium_pattern: "^OPAMP_LM741.*"
    kicad_symbol: "Amplifier_Operational:LM741"
    confidence: 0.95
  
  # Microcontrollers
  - altium_pattern: "^MCU_ATMEGA328.*"
    kicad_symbol: "MCU_Microchip_ATmega:ATmega328P-AU"
    confidence: 0.9
  
  - altium_pattern: "^MCU_STM32F103.*"
    kicad_symbol: "MCU_ST_STM32F1:STM32F103C8Tx"
    confidence: 0.9

footprints:
  # SOIC packages
  - altium_pattern: ".*SOIC-8.*"
    kicad_footprint: "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    confidence: 0.9
  
  - altium_pattern: ".*SOIC-16.*"
    kicad_footprint: "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
    confidence: 0.9
  
  # QFP packages
  - altium_pattern: ".*TQFP-32.*"
    kicad_footprint: "Package_QFP:TQFP-32_7x7mm_P0.8mm"
    confidence: 0.9
  
  - altium_pattern: ".*LQFP-48.*"
    kicad_footprint: "Package_QFP:LQFP-48_7x7mm_P0.5mm"
    confidence: 0.9

categories:
  - altium_pattern: "Operational Amplifiers"
    kicad_category: "Integrated Circuits/Amplifiers"
    confidence: 1.0
  
  - altium_pattern: "Microcontrollers"
    kicad_category: "Integrated Circuits/Microcontrollers"
    confidence: 1.0
```

## Using Custom Mapping Rules

### Command Line Usage

```bash
# Use custom mapping rules
altium2kicad --input path/to/library.DbLib --output output/ --custom-rules path/to/mapping_rules.yaml
```

### Configuration File Usage

```yaml
# migration_config.yaml
input:
  path: path/to/library.DbLib

output:
  directory: output/
  library_name: MyLibrary

mapping:
  confidence_threshold: 0.7
  use_custom_rules: true
  custom_rules_path: path/to/mapping_rules.yaml
```

```bash
altium2kicad --config migration_config.yaml
```

### Python API Usage

```python
from migration_tool import MigrationAPI

# Initialize API
api = MigrationAPI()

# Configure migration with custom rules
config = {
    'input': {
        'path': 'path/to/library.DbLib'
    },
    'output': {
        'directory': 'output/',
        'library_name': 'MyLibrary'
    },
    'mapping': {
        'confidence_threshold': 0.7,
        'use_custom_rules': True,
        'custom_rules_path': 'path/to/mapping_rules.yaml'
    }
}

# Run migration
result = api.run_migration(config)
```

## Best Practices for Custom Mapping Rules

### 1. Start with General Rules, Then Add Specifics

Begin with general rules that cover broad categories, then add more specific rules for exceptions:

```yaml
symbols:
  # General rule for all resistors
  - altium_pattern: "^RES.*"
    kicad_symbol: "Device:R"
    confidence: 0.8
  
  # More specific rule for precision resistors
  - altium_pattern: "^RES_PREC.*"
    kicad_symbol: "Device:R"
    confidence: 0.9
```

### 2. Use Appropriate Confidence Scores

Assign confidence scores based on the specificity of the rule:
- General patterns: 0.7-0.8
- Specific patterns: 0.8-0.9
- Exact matches: 0.9-1.0

### 3. Test and Refine Incrementally

Test your rules on small batches and refine them before applying to your entire library:

```bash
# Test on a small batch
altium2kicad --input path/to/library.DbLib --output test_output/ --custom-rules path/to/mapping_rules.yaml --component-limit 10

# Generate a mapping report
altium2kicad --input path/to/library.DbLib --output test_output/ --custom-rules path/to/mapping_rules.yaml --generate-mapping-report
```

### 4. Organize Rules by Component Type

Split large rule sets into multiple files organized by component type:

```
mapping_rules/
├── resistors.yaml
├── capacitors.yaml
├── inductors.yaml
├── diodes.yaml
├── transistors.yaml
└── ics.yaml
```

Then combine them in your configuration:

```yaml
mapping:
  use_custom_rules: true
  custom_rules_paths:
    - mapping_rules/resistors.yaml
    - mapping_rules/capacitors.yaml
    - mapping_rules/inductors.yaml
    - mapping_rules/diodes.yaml
    - mapping_rules/transistors.yaml
    - mapping_rules/ics.yaml
```

### 5. Document Your Rules

Add comments to your mapping rules to explain their purpose:

```yaml
symbols:
  # Map all resistors to the standard resistor symbol
  # This covers standard resistors with various values and tolerances
  - altium_pattern: "^RES.*"
    kicad_symbol: "Device:R"
    confidence: 0.9
  
  # Special case for high-power resistors
  # These need a different symbol with appropriate power rating
  - altium_pattern: "^RES_PWR.*"
    kicad_symbol: "Device:R_Small"
    confidence: 0.9
```

## Troubleshooting Mapping Issues

### Low Confidence Scores

If you're getting low confidence scores:

1. **Check your patterns**: Ensure your regular expressions match the component names
2. **Add more specific rules**: Create more targeted rules for problematic components
3. **Analyze the mapping report**: Look for patterns in components with low confidence

### Missing Mappings

If components aren't being mapped:

1. **Check for typos**: Ensure KiCAD symbol and footprint names are correct
2. **Verify pattern matching**: Test your regular expressions against actual component names
3. **Add fallback rules**: Create general rules with lower confidence scores as a fallback

### Conflicting Rules

If you have conflicting rules:

1. **Check rule order**: Rules are applied in the order they appear in the file
2. **Adjust confidence scores**: Give higher confidence to more specific rules
3. **Use more specific patterns**: Make patterns more specific to avoid overlap

## Conclusion

Custom mapping rules are a powerful feature of the Altium to KiCAD Database Migration Tool that allows you to achieve higher accuracy in component mapping. By creating well-crafted rules tailored to your specific component libraries, you can significantly improve the quality of your migrations.

For more advanced usage, check out the [API Reference](../developer_guide/api_reference.md) and [Extending the Tool](../developer_guide/extending.md) guides.