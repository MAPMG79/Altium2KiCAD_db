# Deployment Guide

This guide provides comprehensive information about deploying the Altium to KiCAD Migration Tool in various environments. It covers Docker configuration, continuous integration, deployment automation, and platform-specific strategies.

## Table of Contents

- [Docker Configuration](#docker-configuration)
  - [Development Environment](#development-environment)
  - [Production Environment](#production-environment)
  - [Custom Configurations](#custom-configurations)
- [Continuous Integration and Deployment](#continuous-integration-and-deployment)
  - [GitHub Actions Workflow](#github-actions-workflow)
  - [Quality Checks](#quality-checks)
  - [Automated Testing](#automated-testing)
  - [Release Process](#release-process)
- [Deployment Automation](#deployment-automation)
  - [DeploymentManager](#deploymentmanager)
  - [Building Packages](#building-packages)
  - [Creating Executables](#creating-executables)
  - [Release Packaging](#release-packaging)
- [Platform-Specific Deployment](#platform-specific-deployment)
  - [Windows Deployment](#windows-deployment)
  - [Linux Deployment](#linux-deployment)
  - [macOS Deployment](#macos-deployment)
- [Monitoring and Logging](#monitoring-and-logging)
  - [Prometheus Configuration](#prometheus-configuration)
  - [Grafana Dashboards](#grafana-dashboards)
  - [Production Logging](#production-logging)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Deployment Checklist](#deployment-checklist)

## Docker Configuration

The Altium to KiCAD Migration Tool can be deployed using Docker, which provides a consistent and isolated environment for running the application.

### Development Environment

For development purposes, we provide a Docker Compose configuration that sets up the migration tool along with optional services like a test database.

```yaml
# docker-compose.yml - Development environment
version: '3.8'

services:
  migration-tool:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: altium-kicad-migration
    volumes:
      - ./data:/app/data
      - ./output:/app/output
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
    
  # Optional: Database for testing
  test-database:
    image: postgres:13
    container_name: migration-test-db
    environment:
      - POSTGRES_DB=test_components
      - POSTGRES_USER=testuser
      - POSTGRES_PASSWORD=testpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

To start the development environment:

```bash
docker-compose up -d
```

For GUI access (if needed), uncomment the X11 forwarding configuration in the docker-compose.yml file:

```yaml
environment:
  - DISPLAY=${DISPLAY}
volumes:
  - /tmp/.X11-unix:/tmp/.X11-unix:rw
network_mode: host
```

### Production Environment

For production deployment, we use a more streamlined Docker configuration. The Dockerfile is optimized for security and performance:

```dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        unixodbc-dev \
        curl \
        gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Create directories for data
RUN mkdir -p /app/data /app/output /app/logs

# Expose port for web interface (if implemented)
EXPOSE 8080

# Default command
CMD ["python", "-m", "migration_tool.cli", "--help"]
```

To build and run the production Docker image:

```bash
docker build -t altium-kicad-migration:latest .
docker run -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output altium-kicad-migration:latest
```

### Custom Configurations

For custom deployment scenarios, you can extend the base Docker configuration:

1. **High-Performance Configuration**: Add more CPU resources and optimize for large datasets:

```yaml
services:
  migration-tool:
    build:
      context: .
      dockerfile: Dockerfile
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
      - MIGRATION_PARALLEL_WORKERS=4
```

2. **Enterprise Configuration**: Connect to enterprise databases and authentication systems:

```yaml
services:
  migration-tool:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
      - DB_CONNECTION_STRING=mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server
      - AUTH_SERVICE_URL=https://auth.example.com
    secrets:
      - db_credentials
      - api_key
```

## Continuous Integration and Deployment

The project uses GitHub Actions for continuous integration and deployment, ensuring code quality and automating the release process.

### GitHub Actions Workflows

The project uses multiple GitHub Actions workflows for different purposes:

#### 1. Continuous Integration (`.github/workflows/ci.yml`)

The main CI workflow handles testing across multiple platforms and Python versions:

```yaml
name: CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.7', '3.8', '3.9', '3.10', '3.11']
    steps:
    # Testing, linting, and coverage steps
```

#### 2. Release Management (`.github/workflows/release.yml`)

Handles package building and publishing when releases are created:

```yaml
name: Release

on:
  release:
    types: [published]

jobs:
  build-and-publish:
    # Builds and publishes to PyPI
  build-docker:
    # Builds and pushes Docker images
```

#### 3. Documentation (`.github/workflows/docs.yml`)

Builds and deploys project documentation:

```yaml
name: Documentation

on:
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
      - 'migration_tool/**'

jobs:
  build-docs:
    # Builds Sphinx documentation
  deploy-docs:
    # Deploys to GitHub Pages
```

#### 4. Library Migration (`.github/workflows/migrate-libraries.yml`)

Automated migration of component libraries:

```yaml
name: Migrate Component Libraries

on:
  push:
    paths:
      - 'altium_libraries/**'
  workflow_dispatch:

jobs:
  migrate:
    # Runs migration tool
  test_libraries:
    # Validates migrated libraries
  publish_libraries:
    # Commits and releases libraries
```

### Quality Checks

The CI pipeline performs several quality checks:

1. **Linting with flake8**: Ensures code follows PEP 8 style guidelines
2. **Formatting with black**: Verifies consistent code formatting
3. **Type checking with mypy**: Validates type annotations
4. **Security scanning**: Checks for security vulnerabilities

### Automated Testing

Tests are run on multiple operating systems and Python versions:

1. **Unit tests**: Test individual components in isolation
2. **Integration tests**: Test interactions between components
3. **Performance tests**: Ensure the tool meets performance requirements

### Release Process

When a new release is created on GitHub:

1. The test job runs to ensure everything passes
2. The build job creates Python packages and publishes to PyPI
3. The docker job builds and pushes Docker images to Docker Hub

## Deployment Automation

The project includes a deployment automation script (`scripts/deploy.py`) that provides tools for building, packaging, and deploying the application.

### DeploymentManager

The `DeploymentManager` class handles various deployment tasks:

```python
from scripts.deploy import DeploymentManager

# Initialize the deployment manager
manager = DeploymentManager()

# Build a Python package
package_info = manager.build_package()
print(f"Built package: {package_info['wheel']}")

# Build a Docker image
docker_tag = manager.build_docker_image()
print(f"Built Docker image: {docker_tag}")

# Create a complete release package
release_path = manager.create_release_package()
print(f"Created release package: {release_path}")
```

### Building Packages

To build Python packages for distribution:

```bash
python -m scripts.deploy deploy --build-package
```

This creates both wheel and source distribution packages in the `dist/` directory.

### Creating Executables

To create standalone executables for different platforms:

```bash
python -m scripts.deploy deploy --build-executable
```

This uses PyInstaller to create platform-specific executables for both CLI and GUI applications.

### Release Packaging

To create a complete release package with all artifacts:

```bash
python -m scripts.deploy deploy --create-release
```

This builds Python packages, Docker images, and executables, then packages them into a single ZIP archive with a manifest.

## Platform-Specific Deployment

### Windows Deployment

For Windows deployment:

1. **Installer**: Use the standalone executable created by PyInstaller
2. **Dependencies**: Ensure ODBC drivers are installed if connecting to SQL Server
3. **Installation Path**: Typically `C:\Program Files\Altium-KiCAD-Migration\`

Example installation script (PowerShell):

```powershell
# Create installation directory
$installDir = "C:\Program Files\Altium-KiCAD-Migration"
New-Item -ItemType Directory -Force -Path $installDir

# Copy executable and configuration
Copy-Item -Path ".\dist\win32\altium-kicad-migrate-*.exe" -Destination $installDir
Copy-Item -Path ".\config\*" -Destination "$installDir\config\" -Recurse

# Create shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Altium-KiCAD Migration.lnk")
$Shortcut.TargetPath = "$installDir\migration-gui-1.0.0.exe"
$Shortcut.Save()
```

### Linux Deployment

For Linux deployment:

1. **Package Manager**: Create DEB or RPM packages for distribution
2. **System Service**: Configure as a system service if running as an API
3. **Dependencies**: Install required system libraries

Example systemd service configuration:

```ini
[Unit]
Description=Altium to KiCAD Migration Service
After=network.target

[Service]
User=migration
Group=migration
WorkingDirectory=/opt/altium-kicad-migration
ExecStart=/opt/altium-kicad-migration/altium-kicad-migrate
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### macOS Deployment

For macOS deployment:

1. **Application Bundle**: Create a proper .app bundle for GUI application
2. **Code Signing**: Sign the application for Gatekeeper
3. **Homebrew Formula**: Create a Homebrew formula for easy installation

Example Homebrew formula:

```ruby
class AltiumKicadMigration < Formula
  desc "Tool for migrating Altium component libraries to KiCAD format"
  homepage "https://github.com/your-org/altium-kicad-migration"
  url "https://github.com/your-org/altium-kicad-migration/releases/download/v1.0.0/altium-kicad-migration-v1.0.0.tar.gz"
  sha256 "..."
  license "MIT"

  depends_on "python@3.9"
  depends_on "unixodbc"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/altium-kicad-migrate", "--version"
  end
end
```

## Monitoring and Logging

### Prometheus Configuration

The application can be monitored using Prometheus. A sample configuration is provided:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'altium-kicad-migration'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

To set up Prometheus monitoring:

```bash
python -m scripts.deploy monitor --prometheus
```

### Grafana Dashboards

A Grafana dashboard is provided for visualizing metrics:

```bash
python -m scripts.deploy monitor --grafana
```

This creates a dashboard with panels for:
- Migration success rate
- Migration duration
- Components processed
- Error rate

### Production Logging

For production environments, a structured logging configuration is provided:

```bash
python -m scripts.deploy monitor --logging
```

This creates a logging configuration with:
- Console output for immediate visibility
- JSON-formatted log files for machine parsing
- Rotating file handlers to manage disk space
- Separate error logs for easier troubleshooting

## Troubleshooting

### Common Issues

1. **Docker Permission Issues**:
   - Ensure volumes have correct permissions
   - Use the provided non-root user in the container

2. **Database Connection Problems**:
   - Verify ODBC drivers are installed
   - Check connection strings and credentials
   - Ensure database is accessible from the container network

3. **Performance Issues**:
   - Increase parallel workers for large datasets
   - Monitor memory usage and adjust container limits
   - Use volume mounts for efficient I/O

### Deployment Checklist

Before deploying to production:

- [ ] Run the full test suite
- [ ] Verify all quality checks pass
- [ ] Test with representative data
- [ ] Configure proper logging
- [ ] Set up monitoring
- [ ] Create backup and recovery procedures
- [ ] Document deployment-specific configurations