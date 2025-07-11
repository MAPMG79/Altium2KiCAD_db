# Contributing to Altium to KiCAD Database Migration Tool

Thank you for your interest in contributing to the Altium to KiCAD Database Migration Tool! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Be patient and welcoming
- Be thoughtful
- Be collaborative
- When disagreeing, try to understand why
- Ask for help when needed
- Step down considerately

## How Can I Contribute?

There are many ways to contribute to the project:

- Reporting bugs
- Suggesting enhancements
- Writing documentation
- Improving code
- Adding tests
- Helping other users
- Spreading the word

### Reporting Bugs

Before creating a bug report:

1. Check the [existing issues](https://github.com/yourusername/Altium2KiCAD_db/issues) to see if the problem has already been reported
2. Check the [FAQ](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/faq.html) and [Troubleshooting Guide](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/troubleshooting.html) for solutions

When creating a bug report, include as much information as possible:

- A clear and descriptive title
- Detailed steps to reproduce the issue
- Expected vs. actual behavior
- Screenshots or code snippets if applicable
- System information (OS, Python version, etc.)
- Log files or error messages
- Any additional context that might be helpful

Use the bug report template when creating a new issue.

### Suggesting Enhancements

Enhancement suggestions are welcome! When suggesting an enhancement:

- Use a clear and descriptive title
- Provide a detailed description of the proposed enhancement
- Explain why this enhancement would be useful
- Include examples of how it would be used
- Consider the impact on existing users and functionality
- Suggest an implementation approach if possible

Use the feature request template when creating a new issue.

### Pull Requests

We welcome pull requests! To submit a pull request:

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes
4. Add or update tests as needed
5. Update documentation as needed
6. Ensure all tests pass
7. Submit a pull request

## Development Environment

### Prerequisites

- Python 3.8 or higher
- Git
- A GitHub account
- Familiarity with both Altium and KiCAD (for certain contributions)

### Setup

1. **Fork the repository**:
   - Visit the [GitHub repository](https://github.com/yourusername/Altium2KiCAD_db)
   - Click the "Fork" button in the top-right corner

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Altium2KiCAD_db.git
   cd Altium2KiCAD_db
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

5. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code that follows the project's style guidelines
   - Add tests for your changes
   - Update documentation as needed

3. **Run tests locally**:
   ```bash
   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=migration_tool
   
   # Run specific test categories
   pytest tests/unit/
   pytest tests/integration/
   pytest tests/functional/
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add your meaningful commit message here"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a pull request**:
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Add a clear description of your changes
   - Submit the pull request

## Code Style

We follow these coding standards:

1. **PEP 8**: Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.
2. **Docstrings**: Use Google-style docstrings for all functions, classes, and methods.
3. **Type Hints**: Include type hints for function parameters and return values.
4. **Imports**: Sort imports using `isort` and follow the standard import order.
5. **Line Length**: Limit lines to 88 characters (compatible with Black).

We use the following tools to enforce code style:

- **Black**: For code formatting
- **isort**: For import sorting
- **flake8**: For linting
- **mypy**: For type checking

You can run these tools with:

```bash
# Format code
black migration_tool/ tests/

# Sort imports
isort migration_tool/ tests/

# Lint code
flake8 migration_tool/ tests/

# Type checking
mypy migration_tool/
```

## Testing

All contributions should include appropriate tests:

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test interactions between components
3. **Functional Tests**: Test end-to-end workflows

Tests should be placed in the `tests/` directory, following the same structure as the code they test.

### Writing Tests

- Use pytest for writing tests
- Keep tests simple and focused
- Use descriptive test names
- Use fixtures for common setup
- Mock external dependencies
- Test both success and failure cases
- Include edge cases

Example test:

```python
def test_mapping_engine_maps_resistor_correctly():
    """Test that the mapping engine correctly maps a resistor component."""
    # Arrange
    component = {
        'LibRef': 'RES_10K',
        'Description': '10K Resistor',
        'Footprint': 'AXIAL-0.3'
    }
    engine = MappingEngine(config_manager)
    
    # Act
    mapped_component = engine.map_component(component)
    
    # Assert
    assert mapped_component['Symbol']['name'] == 'Device:R'
    assert mapped_component['Footprint']['name'] == 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'
    assert mapped_component['Confidence'] >= 0.8
```

## Documentation

Update documentation for any code changes:

1. **Docstrings**: Update docstrings for modified functions/classes
2. **README**: Update README.md if adding features or changing usage
3. **User Guides**: Update relevant user guides for feature changes
4. **API Documentation**: Update API docs for public interface changes

Build documentation with:

```bash
cd docs
make html
```

### Documentation Standards

- Use clear, concise language
- Include examples where appropriate
- Keep documentation up-to-date with code changes
- Follow the existing documentation style
- Use proper spelling and grammar
- Include diagrams or screenshots for complex concepts

## Performance Considerations

When making changes, consider the performance implications:

- Profile your code to identify bottlenecks
- Use efficient algorithms and data structures
- Implement caching for expensive operations
- Consider memory usage for large datasets
- Test with realistic data sizes

You can profile your code with:

```bash
# Profile specific functions
python -m cProfile -o profile.stats your_script.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumtime').print_stats(30)"
```

## Design Principles

Follow these design principles when contributing:

1. **Separation of Concerns**: Each component should have a well-defined responsibility
2. **Dependency Injection**: Components should receive dependencies through constructors or methods
3. **Interface-Based Design**: Components should interact through well-defined interfaces
4. **Configuration Over Convention**: Use explicit configuration rather than implicit conventions
5. **Fail Fast and Validate Early**: Validate input early and provide clear error messages
6. **Comprehensive Logging**: Log operations at appropriate levels

## Adding New Features

When adding new features:

1. **Discuss First**: Open an issue to discuss the feature before implementing
2. **Start Small**: Break large features into smaller, manageable pieces
3. **Maintain Compatibility**: Ensure backward compatibility when possible
4. **Document Thoroughly**: Provide comprehensive documentation for the feature
5. **Add Tests**: Include tests that cover the new functionality
6. **Consider Edge Cases**: Think about potential edge cases and handle them appropriately

## Database Schema Changes

When making changes to the database schema:

1. **Document Changes**: Clearly document schema changes
2. **Provide Migration Path**: Include migration scripts for existing databases
3. **Test Thoroughly**: Test with various database sizes and contents
4. **Consider Backward Compatibility**: Ensure changes don't break existing data

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backward-compatible functionality additions
- **PATCH** version for backward-compatible bug fixes

## Release Checklist

Before a release:

1. Update version number in `__init__.py` and `setup.py`
2. Update CHANGELOG.md with the changes
3. Ensure all tests pass
4. Build and check documentation
5. Create a release branch
6. Tag the release
7. Build and publish the package

## Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions
- **Discussions**: For general questions and discussions
- **Email**: For private inquiries (maintainer@example.com)

## Recognition

All contributors will be recognized in:

1. **CONTRIBUTORS.md**: List of all contributors
2. **Release Notes**: Contributors to each release
3. **Documentation**: Attribution for significant contributions

## Thank You!

Thank you for contributing to the Altium to KiCAD Database Migration Tool! Your contributions help make this tool better for everyone in the electronics design community.