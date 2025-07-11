# Contributing Guide

This guide provides information for developers who want to contribute to the Altium to KiCAD Database Migration Tool. We welcome contributions of all kinds, including bug fixes, feature additions, documentation improvements, and more.

## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Be patient and welcoming
- Be thoughtful
- Be collaborative
- When disagreeing, try to understand why
- Ask for help when needed
- Step down considerately

## Getting Started

### Prerequisites

Before you begin contributing, ensure you have:

1. Python 3.8 or higher
2. Git
3. A GitHub account
4. Familiarity with both Altium and KiCAD (for certain contributions)

### Development Environment Setup

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
   pytest
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

## Contribution Guidelines

### Code Style

We follow these coding standards:

1. **PEP 8**: Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.
2. **Docstrings**: Use Google-style docstrings for all functions, classes, and methods.
3. **Type Hints**: Include type hints for function parameters and return values.
4. **Imports**: Sort imports using `isort` and follow the standard import order.
5. **Line Length**: Limit lines to 88 characters (compatible with Black).

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

Run tests with:

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

### Documentation

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

### Pull Request Process

1. **Keep PRs Focused**: Each PR should address a single concern
2. **Write Clear Descriptions**: Explain what your PR does and why
3. **Include Tests**: All PRs should include appropriate tests
4. **Update Documentation**: Update relevant documentation
5. **Pass CI Checks**: Ensure all CI checks pass
6. **Address Review Comments**: Be responsive to review feedback

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

### Database Schema Changes

When making changes to the database schema:

1. **Document Changes**: Clearly document schema changes
2. **Provide Migration Path**: Include migration scripts for existing databases
3. **Test Thoroughly**: Test with various database sizes and contents
4. **Consider Backward Compatibility**: Ensure changes don't break existing data

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

Our release process follows these steps:

1. **Version Bump**: Update version in `__init__.py` and `setup.py`
2. **Update Changelog**: Document changes in CHANGELOG.md
3. **Create Release Branch**: Create a release branch (e.g., `release/1.2.0`)
4. **Run Tests**: Ensure all tests pass
5. **Build Documentation**: Update and build documentation
6. **Create Release**: Tag the release in Git
7. **Publish Package**: Upload to PyPI
8. **Announce Release**: Announce the release to the community

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

## Thank You

Thank you for considering contributing to the Altium to KiCAD Database Migration Tool! Your contributions help make this tool better for everyone in the electronics design community.