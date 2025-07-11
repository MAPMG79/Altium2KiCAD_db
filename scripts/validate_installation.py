#!/usr/bin/env python3
"""
Installation Validation Script for Altium to KiCAD Database Migration Tool.

This script validates the installation of the Altium to KiCAD Migration Tool
and its dependencies, checking:
- Python version
- Required packages
- ODBC drivers
- Database connectivity
- File permissions
- GUI dependencies
"""

import argparse
import importlib
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate installation of Altium to KiCAD Migration Tool"
    )
    parser.add_argument(
        "--check-odbc",
        action="store_true",
        help="Check ODBC drivers installation",
    )
    parser.add_argument(
        "--check-gui",
        action="store_true",
        help="Check GUI dependencies",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output",
    )
    return parser.parse_args()


def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    min_version = (3, 7)
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        raise ValidationError(
            f"Python {min_version[0]}.{min_version[1]} or higher is required. "
            f"Found Python {current_version[0]}.{current_version[1]}."
        )
    
    print(f"✓ Python version: {sys.version.split()[0]}")
    return True


def check_required_packages():
    """Check required packages."""
    print("Checking required packages...")
    required_packages = [
        "pyodbc",
        "pyyaml",
        "tqdm",
        "colorama",
        "click",
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is missing")
    
    if missing_packages:
        raise ValidationError(
            f"Missing required packages: {', '.join(missing_packages)}. "
            "Please install them using: pip install -r requirements.txt"
        )
    
    return True


def check_odbc_drivers():
    """Check ODBC drivers installation."""
    print("Checking ODBC drivers...")
    
    try:
        import pyodbc
        drivers = pyodbc.drivers()
        
        if not drivers:
            print("✗ No ODBC drivers found")
            raise ValidationError(
                "No ODBC drivers found. Please install ODBC drivers."
            )
        
        print(f"✓ Found {len(drivers)} ODBC drivers:")
        for driver in drivers:
            print(f"  - {driver}")
        
        return True
    except ImportError:
        print("✗ pyodbc module not found")
        raise ValidationError(
            "pyodbc module not found. Please install it using: pip install pyodbc"
        )


def check_file_permissions():
    """Check file permissions."""
    print("Checking file permissions...")
    
    # Check if we can create temporary files
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"test")
            print(f"✓ Can create temporary files: {tmp.name}")
    except Exception as e:
        print(f"✗ Cannot create temporary files: {e}")
        raise ValidationError(
            f"Cannot create temporary files: {e}"
        )
    
    # Check if we can access the config directory
    config_dir = Path(__file__).parent.parent / "config"
    if not config_dir.exists():
        print(f"✗ Config directory not found: {config_dir}")
        raise ValidationError(
            f"Config directory not found: {config_dir}"
        )
    
    try:
        config_files = list(config_dir.glob("*.yaml"))
        if not config_files:
            print(f"✗ No config files found in {config_dir}")
            raise ValidationError(
                f"No config files found in {config_dir}"
            )
        
        print(f"✓ Found {len(config_files)} config files")
        for config_file in config_files:
            with open(config_file, "r") as f:
                f.read(1)  # Try to read one byte
            print(f"  - {config_file.name} (readable)")
    except Exception as e:
        print(f"✗ Cannot read config files: {e}")
        raise ValidationError(
            f"Cannot read config files: {e}"
        )
    
    return True


def check_gui_dependencies():
    """Check GUI dependencies."""
    print("Checking GUI dependencies...")
    
    # Check tkinter
    try:
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        root.destroy()
        print("✓ tkinter is installed and working")
    except ImportError:
        print("✗ tkinter is not installed")
        raise ValidationError(
            "tkinter is not installed. Please install it for your platform."
        )
    except Exception as e:
        print(f"✗ tkinter error: {e}")
        raise ValidationError(
            f"tkinter error: {e}"
        )
    
    return True


def check_cli_functionality():
    """Check CLI functionality."""
    print("Checking CLI functionality...")
    
    try:
        # Import the CLI module
        from migration_tool import cli
        
        # Check if the main function exists
        if not hasattr(cli, "main"):
            print("✗ CLI main function not found")
            raise ValidationError(
                "CLI main function not found in migration_tool.cli"
            )
        
        print("✓ CLI module is available")
        return True
    except ImportError as e:
        print(f"✗ Cannot import CLI module: {e}")
        raise ValidationError(
            f"Cannot import CLI module: {e}"
        )


def main():
    """Main function to validate installation."""
    args = parse_args()
    
    print("Validating Altium to KiCAD Migration Tool installation...\n")
    
    validation_steps = [
        check_python_version,
        check_required_packages,
        check_file_permissions,
        check_cli_functionality,
    ]
    
    if args.check_odbc:
        validation_steps.append(check_odbc_drivers)
    
    if args.check_gui:
        validation_steps.append(check_gui_dependencies)
    
    success = True
    for step in validation_steps:
        try:
            step()
            print("")  # Add a blank line after each step
        except ValidationError as e:
            print(f"\n❌ Validation Error: {e}\n")
            success = False
            break
        except Exception as e:
            print(f"\n❌ Unexpected Error: {e}\n")
            if args.verbose:
                import traceback
                traceback.print_exc()
            success = False
            break
    
    if success:
        print("✅ All validation checks passed! The installation is valid.")
        return 0
    else:
        print("❌ Validation failed. Please fix the issues and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())