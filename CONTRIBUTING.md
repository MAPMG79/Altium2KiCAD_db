# Contributing to Altium to KiCAD Database Migration Tool

Thank you for your interest in contributing to the Altium to KiCAD Database Migration Tool! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

Our Code of Conduct principles:

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

Before creating bug reports, please check the issue list as you might find that the problem has already been reported. When creating a bug report, include:

- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Log files** and error messages
- **Sample data** (remove sensitive information)

Use the bug report template when creating a new issue.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide detailed description** of the enhancement
- **Explain why this enhancement would be useful**
- **Consider providing mockups** for UI changes

Use the feature request template when creating a new issue.

### Pull Requests

1. **Fork** the repository
2. **Create a feature branch** from `develop`
3. **Make your changes** with clear commit messages
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Ensure tests pass** and code quality checks pass
7. **Submit a pull request**

## Development Environment

### Prerequisites

- Python 3.7+
- Git
- Virtual environment tool (venv, conda, etc.)
- Familiarity with both Altium and KiCAD (for certain contributions)

### Development Setup

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

## Code Style

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

## Testing

### Running Tests

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

### Writing Tests

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

## Architecture Guidelines

### Design Principles

- **Single Responsibility**: Each class/function has one clear purpose
- **Dependency Injection**: Use configuration and dependency injection
- **Error Handling**: Comprehensive error handling with recovery
- **Logging**: Detailed logging for debugging
- **Testability**: Design for easy testing

### Adding New Features

1. **Design first**: Create design document for complex features
2. **Interface definition**: Define clear interfaces
3. **Implementation**: Implement with tests
4. **Documentation**: Update relevant documentation
5. **Examples**: Provide usage examples

## Database Schema Changes

When modifying database schemas:

1. **Migration scripts**: Provide upgrade/downgrade scripts
2. **Backward compatibility**: Maintain compatibility when possible
3. **Documentation**: Update schema documentation
4. **Testing**: Test migration scripts thoroughly

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