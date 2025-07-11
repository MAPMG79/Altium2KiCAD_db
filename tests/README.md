# Altium to KiCAD Migration Tool Testing

This directory contains the test suite for the Altium to KiCAD Database Migration Tool. This README provides an overview of the testing structure, how to run tests, and how to add new tests.

## Test Structure

The tests are organized into the following categories:

- **Unit Tests** (`tests/unit/`): Tests for individual components in isolation
- **Integration Tests** (`tests/integration/`): Tests for interactions between components
- **Performance Tests** (`tests/performance/`): Tests for performance characteristics

## Running Tests

To run the tests, you need to install the development dependencies:

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

### Running All Tests

```bash
# Run all tests
pytest
```

### Running with Coverage

```bash
# Run with coverage
pytest --cov=migration_tool --cov-report=html
```

This will generate an HTML coverage report in the `htmlcov/` directory.

### Running Specific Test Categories

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/
```

### Running Specific Test Files

```bash
# Run a specific test file
pytest tests/unit/test_altium_parser.py
```

### Running Specific Test Functions

```bash
# Run a specific test function
pytest tests/unit/test_altium_parser.py::TestAltiumDbLibParser::test_parse_dblib_file
```

## Test Setup and Teardown

Most tests use fixtures defined in `conftest.py` for setup and teardown. These fixtures handle creating temporary directories, sample data, and initializing components.

### Common Fixtures

- `temp_dir`: Creates a temporary directory for test outputs
- `sample_dblib_file`: Creates a sample Altium DbLib file
- `sample_config`: Creates a sample configuration
- `altium_parser`: Provides an initialized AltiumDbLibParser
- `mapping_engine`: Provides an initialized ComponentMappingEngine
- `kicad_generator`: Provides an initialized KiCADDbLibGenerator

## Test Examples

### Unit Test Example

Here's an example of a unit test for the Altium parser:

```python
def test_parse_dblib_file(self):
    """Test parsing of DbLib file."""
    # Arrange
    test_dblib_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'test.DbLib'
    )
    
    # Act
    config = self.parser.parse_dblib_file(test_dblib_path)
    
    # Assert
    self.assertIn('connection_string', config)
    self.assertIn('tables', config)
    self.assertEqual(len(config['tables']), 2)
    self.assertIn('Resistors', config['tables'])
    self.assertIn('Capacitors', config['tables'])
```

### Integration Test Example

Here's an example of an integration test for the full migration process:

```python
def test_full_migration(self):
    """Test the full migration process from Altium to KiCAD."""
    # Arrange
    test_framework = MigrationTestFramework()
    test_dblib_path = test_framework.create_test_altium_dblib()
    output_dir = os.path.join(test_framework.test_output_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Act
    result = test_framework.run_migration_test(test_dblib_path, output_dir)
    
    # Assert
    self.assertTrue(os.path.exists(result['database_path']))
    self.assertTrue(os.path.exists(result['dblib_path']))
    
    # Validate migration
    validation_report = test_framework.validate_migration(
        result['database_path'], 
        result['original_data']
    )
    
    self.assertGreaterEqual(validation_report['data_integrity']['integrity_score'], 0.95)
    self.assertGreaterEqual(validation_report['overall_quality_score'], 0.8)
```

### Performance Test Example

Here's an example of a performance test for large datasets:

```python
def test_large_dataset_performance(self):
    """Test performance with a large dataset."""
    # Arrange
    large_dataset = generate_large_test_dataset(10000)  # 10,000 components
    
    # Act
    start_time = time.time()
    result = self.mapping_engine.map_components(large_dataset)
    end_time = time.time()
    
    # Assert
    processing_time = end_time - start_time
    components_per_second = len(large_dataset) / processing_time
    
    self.assertGreaterEqual(components_per_second, 1000)  # At least 1000 components/sec
    self.assertEqual(len(result), len(large_dataset))
```

## Test Data and Fixtures

The `tests/fixtures/` directory contains test data used by the tests. This includes:

- Sample Altium DbLib files
- Sample component data
- Configuration files for testing

### Creating Test Fixtures

To create a new test fixture, add it to the `conftest.py` file:

```python
@pytest.fixture
def my_new_fixture():
    """Description of the fixture."""
    # Setup code
    yield my_fixture_value
    # Teardown code
```

## Adding New Tests

To add a new test:

1. Identify the appropriate test category (unit, integration, performance)
2. Create or modify a test file in the appropriate directory
3. Add test functions using the pytest framework
4. Use existing fixtures or create new ones as needed

### Test Naming Conventions

- Test files should be named `test_*.py`
- Test classes should be named `Test*`
- Test functions should be named `test_*`
- Test function names should clearly describe what is being tested

## Performance Testing

Performance tests evaluate the tool's performance characteristics, including:

- **Processing Speed**: How quickly the tool can process components
- **Memory Usage**: How much memory the tool consumes during operation
- **Scalability**: How well the tool handles large datasets

### Benchmarking

Performance tests include benchmarks for key operations:

- Parsing Altium DbLib files
- Extracting data from databases
- Mapping components
- Generating KiCAD libraries

### Memory Usage Testing

Memory usage tests monitor the tool's memory consumption during operation:

```python
def test_memory_usage():
    """Test memory usage during migration."""
    import tracemalloc
    
    # Start tracking memory
    tracemalloc.start()
    
    # Run the operation
    result = run_migration(test_data)
    
    # Get memory statistics
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"Current memory usage: {current / 10**6}MB")
    print(f"Peak memory usage: {peak / 10**6}MB")
    
    # Assert memory usage is within acceptable limits
    assert peak < 100 * 10**6  # Less than 100MB peak memory usage
```

### Performance Regression Testing

Performance regression tests compare current performance against baseline measurements to detect regressions:

```python
def test_performance_regression():
    """Test for performance regressions."""
    # Load baseline performance metrics
    with open('baseline_performance.json', 'r') as f:
        baseline = json.load(f)
    
    # Run performance test
    start_time = time.time()
    result = run_migration(test_data)
    end_time = time.time()
    
    # Calculate current performance
    current_performance = end_time - start_time
    
    # Compare with baseline (allow 10% regression)
    max_allowed = baseline['migration_time'] * 1.1
    
    assert current_performance <= max_allowed, (
        f"Performance regression detected: {current_performance:.2f}s vs "
        f"baseline {baseline['migration_time']:.2f}s"
    )
```

## Continuous Integration

Tests are automatically run as part of the continuous integration (CI) pipeline. The CI configuration ensures that:

- All tests pass on each pull request
- Test coverage is maintained or improved
- Performance does not regress significantly

## Additional Resources

For more detailed information about the testing framework, see:

- [Testing Framework Documentation](../docs/developer_guide/testing.md): Comprehensive documentation of the testing framework
- [Contributing Guide](../docs/developer_guide/contributing.md): Guidelines for contributing to the project