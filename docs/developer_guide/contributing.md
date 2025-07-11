# Contributing Guide

This guide provides information for developers who want to contribute to the Altium to KiCAD Database Migration Tool. We welcome contributions of all kinds, including bug fixes, feature additions, documentation improvements, and more.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](../../CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

Our Code of Conduct principles:

- Be respectful and inclusive
- Be patient and welcoming
- Be thoughtful
- Be collaborative
- When disagreeing, try to understand why
- Ask for help when needed
- Step down considerately

## Getting Started

## Getting Started

### Prerequisites

Before you begin contributing, ensure you have:

1. Python 3.7+
2. Git
3. A GitHub account
4. Virtual environment tool (venv, conda, etc.)
5. Familiarity with both Altium and KiCAD (for certain contributions)

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-org/altium-kicad-migration.git
cd altium-kicad-migration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
make install-dev

# Set up pre-commit hooks
pre-commit install

# Run tests to verify setup
make test
```

### Development Workflow

```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes and test
make test
make lint
make format

# Commit changes
git add .
git commit -m "Add feature: your feature description"

# Push and create pull request
git push origin feature/your-feature-name
```

## Contribution Guidelines

## Contribution Guidelines

### Code Style

We use the following tools for code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run all checks with:

```bash
make lint
```

Format code with:

```bash
make format
```

Example of proper code style:

```python
from typing import Dict, List, Optional

import numpy as np
from tqdm import tqdm

from migration_tool.utils.logging_utils import setup_logger


def process_components(
    components: List[Dict[str, any]],
    confidence_threshold: float = 0.7,
    validate: bool = True
) -> List[Dict[str, any]]:
    """
    Process components with validation and filtering.
    
    Args:
        components: List of component dictionaries to process
        confidence_threshold: Minimum confidence score to accept
        validate: Whether to validate components
        
    Returns:
        List of processed components
        
    Raises:
        ValueError: If confidence_threshold is not between 0 and 1
    """
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("Confidence threshold must be between 0 and 1")
        
    logger = setup_logger(__name__)
    logger.info(f"Processing {len(components)} components")
    
    result = []
    for component in tqdm(components, desc="Processing"):
        # Processing logic here
        if component.get("confidence", 0) >= confidence_threshold:
            result.append(component)
            
    return result
```

### Testing

All contributions should include appropriate tests:

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test interactions between components
3. **Functional Tests**: Test end-to-end workflows
4. **Performance Tests**: Test performance with large datasets

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
make test-coverage
```

#### Writing Tests

- Write tests for all new functionality
- Follow existing test patterns
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies

Example test structure:

```python
def test_component_mapping_success():
    """Test successful component mapping with valid data."""
    # Arrange
    component_data = {...}
    mapper = ComponentMappingEngine()
    
    # Act
    result = mapper.map_component(component_data)
    
    # Assert
    assert result.confidence > 0.8
    assert result.kicad_symbol == "Device:R"
```

### Documentation

Update documentation for any code changes:

1. **Docstrings**: Update docstrings for modified functions/classes
2. **README**: Update README.md if adding features or changing usage
3. **User Guides**: Update relevant user guides for feature changes
4. **API Documentation**: Update API docs for public interface changes
5. **Examples**: Add or update examples demonstrating the changes

Build documentation with:

```bash
cd docs
make html
```

#### Documentation Standards

- Use clear, concise language
- Include code examples
- Update API documentation for code changes
- Add screenshots for UI changes

### Pull Request Process

1. **Keep PRs Focused**: Each PR should address a single concern
2. **Write Clear Descriptions**: Explain what your PR does and why
3. **Include Tests**: All PRs should include appropriate tests
4. **Update Documentation**: Update relevant documentation
5. **Pass CI Checks**: Ensure all CI checks pass
6. **Address Review Comments**: Be responsive to review feedback
7. **Update Changelog**: Add your changes to the CHANGELOG.md file

## Types of Contributions

### Bug Fixes

1. **Identify the Bug**: Clearly describe the bug in a GitHub issue
2. **Reproduce the Bug**: Create a test case that reproduces the bug
3. **Fix the Bug**: Implement a fix that addresses the root cause
4. **Add Tests**: Add tests to prevent regression

### Feature Additions

1. **Propose the Feature**: Discuss new features in a GitHub issue first
2. **Design the Feature**: Consider how it fits into the existing architecture
3. **Implement the Feature**: Add the feature with appropriate tests
4. **Document the Feature**: Update documentation to cover the new feature

### Documentation Improvements

1. **Identify Gaps**: Find areas where documentation is missing or unclear
2. **Improve Content**: Make documentation more clear, complete, or accurate
3. **Fix Typos/Grammar**: Correct any language issues
4. **Add Examples**: Provide practical examples where helpful

### Performance Improvements

1. **Identify Bottlenecks**: Use profiling to identify performance issues
2. **Benchmark Current Performance**: Establish baseline metrics
3. **Implement Improvements**: Make targeted improvements
4. **Verify Improvements**: Demonstrate performance gains with benchmarks

## Advanced Topics

## Advanced Topics

### Performance Guidelines

- Profile code for performance bottlenecks
- Use appropriate data structures
- Implement caching where beneficial
- Consider memory usage for large datasets
- Optimize database queries

### Benchmarking

```bash
# Run performance benchmarks
python scripts/performance_benchmark.py

# Profile specific functions
python -m cProfile -o profile.stats script.py
```

### Architecture Guidelines

#### Design Principles

- **Single Responsibility**: Each class/function has one clear purpose
- **Dependency Injection**: Use configuration and dependency injection
- **Error Handling**: Comprehensive error handling with recovery
- **Logging**: Detailed logging for debugging
- **Testability**: Design for easy testing

#### Adding New Features

1. **Design first**: Create design document for complex features
2. **Interface definition**: Define clear interfaces
3. **Implementation**: Implement with tests
4. **Documentation**: Update relevant documentation
5. **Examples**: Provide usage examples

### Database Schema Changes

When modifying database schemas:

1. **Migration scripts**: Provide upgrade/downgrade scripts
2. **Backward compatibility**: Maintain compatibility when possible
3. **Documentation**: Update schema documentation
4. **Testing**: Test migration scripts thoroughly

### Adding New Database Support

To add support for a new database type:

1. **Create Adapter**: Implement a new database adapter class
2. **Add Connection Logic**: Implement connection handling
3. **Add Query Logic**: Implement query execution
4. **Add Tests**: Test with the new database type
5. **Update Documentation**: Document the new database support

### Adding New Mapping Algorithms

To add a new mapping algorithm:

1. **Design Algorithm**: Design the algorithm with clear inputs and outputs
2. **Implement Algorithm**: Add the implementation to the mapping engine
3. **Make Configurable**: Allow users to enable/disable via configuration
4. **Add Tests**: Test with various component types
5. **Document Algorithm**: Explain how and when to use the algorithm

## Release Process

### Version Numbering

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version number
2. Update CHANGELOG.md
3. Run full test suite
4. Update documentation
5. Create release tag
6. Publish to PyPI
7. Update Docker images

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussion and questions
- **Pull Requests**: Code contributions and reviews

### Recognition

Contributors are recognized in:

- README.md contributors section
- Release notes
- Documentation credits

Thank you for contributing to the Altium to KiCAD Migration Tool!