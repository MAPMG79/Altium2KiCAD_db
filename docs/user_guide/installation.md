# Installation Guide

This guide provides detailed instructions for installing the Altium to KiCAD Database Migration Tool on various platforms.

## System Requirements

Before installing, ensure your system meets the following requirements:

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+, Debian 10+, Fedora 32+)
- **Python**: Python 3.8 or higher
- **Disk Space**: At least 500 MB of free disk space
- **Memory**: Minimum 4 GB RAM (8 GB recommended for large databases)
- **Database Drivers**: Appropriate database drivers for your source database

## Installation Methods

Choose one of the following installation methods based on your preferences and requirements.

### Method 1: Using pip (Recommended)

The simplest way to install the tool is using pip, Python's package manager:

```bash
# Create a virtual environment (recommended)
python -m venv altium2kicad-env
source altium2kicad-env/bin/activate  # On Windows: altium2kicad-env\Scripts\activate

# Install the package
pip install altium2kicad-db
```

### Method 2: From Source

For the latest development version or to contribute to the project:

```bash
# Clone the repository
git clone https://github.com/yourusername/Altium2KiCAD_db.git
cd Altium2KiCAD_db

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Method 3: Using Docker

For a containerized installation that includes all dependencies:

```bash
# Pull the Docker image
docker pull yourusername/altium2kicad-db:latest

# Run the container
docker run -it --rm -v $(pwd):/data yourusername/altium2kicad-db
```

### Method 4: Standalone Executable (Windows only)

For users who prefer not to install Python:

1. Download the latest release from the [GitHub Releases page](https://github.com/yourusername/Altium2KiCAD_db/releases)
2. Extract the ZIP file to a location of your choice
3. Run `Altium2KiCAD_db.exe`

## Database Drivers

Depending on your source database, you'll need to install the appropriate drivers:

### SQLite

SQLite support is included by default, no additional drivers needed.

### MySQL/MariaDB

```bash
pip install mysqlclient
```

### PostgreSQL

```bash
pip install psycopg2-binary
```

### Microsoft SQL Server

#### Windows

```bash
pip install pyodbc
```

Then install the [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

#### Linux

```bash
# Ubuntu/Debian
sudo apt-get install unixodbc-dev
pip install pyodbc

# Install Microsoft ODBC Driver
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install msodbcsql17
```

#### macOS

```bash
brew install unixodbc
pip install pyodbc

# Install Microsoft ODBC Driver
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
ACCEPT_EULA=Y brew install msodbcsql17
```

## Verifying Installation

To verify that the installation was successful:

```bash
# Check the installed version
altium2kicad --version

# Run the validation script
altium2kicad --validate
```

You should see the version number and a confirmation that all dependencies are correctly installed.

## Troubleshooting Installation Issues

### Common Issues

#### Missing Python

If you receive a "command not found" error, ensure Python is installed and in your PATH:

```bash
python --version
```

#### Permission Errors

If you encounter permission errors during installation:

- On Linux/macOS, try using `sudo pip install altium2kicad-db`
- On Windows, run the command prompt as Administrator

#### Database Driver Issues

If you have issues with database drivers:

1. Ensure you've installed the correct driver for your database
2. Check that the driver is compatible with your database version
3. Verify that any required system libraries are installed

#### Virtual Environment Issues

If you have problems with virtual environments:

```bash
# Remove the environment and create a new one
rm -rf altium2kicad-env
python -m venv altium2kicad-env
source altium2kicad-env/bin/activate
pip install altium2kicad-db
```

## Next Steps

After successful installation, proceed to the [Quickstart Guide](quickstart.md) to perform your first migration.