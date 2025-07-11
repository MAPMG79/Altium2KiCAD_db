# Altium to KiCAD Database Migration Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![Documentation Status](https://readthedocs.org/projects/altium2kicad-db/badge/?version=latest)](https://altium2kicad-db.readthedocs.io/en/latest/?badge=latest)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/example/altium2kicad/releases)

A comprehensive tool for migrating component libraries from Altium's DbLib format to KiCAD's database library format, making it easier to transition between these two popular EDA platforms.

## 🚀 Features

- **Database Support**: Parse Altium DbLib files and connect to SQLite, MySQL, PostgreSQL, and MS SQL databases
- **Intelligent Mapping**: Map Altium components to KiCAD equivalents with confidence scoring
- **Symbol & Footprint Mapping**: Automatically map Altium symbols and footprints to KiCAD equivalents
- **Custom Mapping Rules**: Define custom mapping rules for specialized components
- **ML-Based Mapping**: Advanced machine learning algorithms for improved mapping accuracy
- **Batch Processing**: Process multiple libraries in a single operation
- **Validation**: Validate mappings against KiCAD libraries
- **Detailed Reporting**: Generate comprehensive reports of the migration process
- **Multiple Interfaces**: Command-line, graphical user interface, and API server
- **Extensible Architecture**: Easily extend with new database support or mapping algorithms
- **Performance Optimized**: Parallel processing and caching for handling large libraries
- **Comprehensive Error Handling**: Advanced error recovery and reporting system
- **Monitoring & Metrics**: Prometheus and Grafana integration for performance monitoring
- **Testing Framework**: Sophisticated sample data generation for comprehensive testing

## 📋 Requirements

- Python 3.7 or higher
- Database drivers for your source database type
- KiCAD 6.0 or higher (for using the migrated libraries)

## 🔧 Installation

### Using pip (Recommended)

```bash
pip install altium2kicad
```

### From Source

```bash
git clone https://github.com/example/altium2kicad.git
cd altium2kicad
pip install -e .
```

### Using Installation Scripts

#### Linux/macOS

```bash
./scripts/install.sh
```

#### Windows

```bash
scripts\install.bat
```

### Docker Installation

```bash
./scripts/docker_deploy.sh
```

## 🚀 Quick Start

### Command-Line Interface

```bash
# Basic migration
altium2kicad migrate --input path/to/altium.DbLib --output path/to/output

# With custom mapping rules
altium2kicad migrate --input path/to/altium.DbLib --output path/to/output --mapping-rules path/to/rules.yaml

# Batch processing
altium2kicad batch --input-dir path/to/dblibfiles --output-dir path/to/output
```

### Graphical User Interface

```bash
# Launch the GUI
altium2kicad-gui

# Or use the launcher script
python run_gui.py
```

### API Server

```bash
# Start the API server
altium2kicad-api

# Or use the launcher script
python run_api.py
```

## 📚 Documentation

Comprehensive documentation is available at [https://altium2kicad-db.readthedocs.io/](https://altium2kicad-db.readthedocs.io/)

### User Guide

- [Installation](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/installation.html)
- [Quick Start](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/quickstart.html)
- [Basic Usage](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/basic_usage.html)
- [Advanced Features](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/advanced_features.html)
- [FAQ](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/faq.html)
- [Troubleshooting](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/troubleshooting.html)

### Developer Guide

- [Architecture](https://altium2kicad-db.readthedocs.io/en/latest/developer_guide/architecture.html)
- [API Reference](https://altium2kicad-db.readthedocs.io/en/latest/developer_guide/api_reference.html)
- [Extending the Tool](https://altium2kicad-db.readthedocs.io/en/latest/developer_guide/extending.html)
- [Error Handling](https://altium2kicad-db.readthedocs.io/en/latest/developer_guide/error_handling.html)
- [Testing Framework](https://altium2kicad-db.readthedocs.io/en/latest/developer_guide/testing.html)
- [Monitoring & Metrics](https://altium2kicad-db.readthedocs.io/en/latest/developer_guide/monitoring.html)
- [Contributing](https://altium2kicad-db.readthedocs.io/en/latest/developer_guide/contributing.html)

### Examples

- [Basic Migration](https://altium2kicad-db.readthedocs.io/en/latest/examples/basic_migration.html)
- [Custom Mapping](https://altium2kicad-db.readthedocs.io/en/latest/examples/custom_mapping.html)
- [Batch Processing](https://altium2kicad-db.readthedocs.io/en/latest/examples/batch_processing.html)
- [Enterprise Setup](https://altium2kicad-db.readthedocs.io/en/latest/examples/enterprise_setup.html)

## 🔧 Configuration

The tool can be configured using YAML configuration files. See the [configuration documentation](https://altium2kicad-db.readthedocs.io/en/latest/user_guide/advanced_features.html#configuration) for details.

Example configuration:

```yaml
# Database connection settings
database:
  timeout: 30
  max_retries: 3
  retry_delay: 2

# Migration settings
migration:
  create_component_views: true
  include_confidence_scores: true
  validate_symbols: false
  batch_size: 1000
  min_confidence: 50
  use_optimized_engine: true
  parallel_processing: true
  enable_caching: true
  enable_ml_mapping: true
  ml_model_path: "models/symbol_classifier.pkl"
  ml_fallback_threshold: 0.6
```

## 🛠️ Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/example/altium2kicad.git
cd altium2kicad

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_altium_parser.py

# Run with coverage
pytest --cov=migration_tool
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

For information about security policies and procedures, please see [SECURITY.md](SECURITY.md).

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes in each release.

## 👥 Authors

- **Altium2KiCAD Team** - *Initial work*

## 🙏 Acknowledgments

- The KiCAD team for their excellent EDA platform
- The Altium team for their documentation on the DbLib format
- All contributors who have helped with this project