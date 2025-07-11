#!/usr/bin/env python3
"""
Development Environment Setup Script for Altium to KiCAD Database Migration Tool.

This script automates the setup of a development environment for the project,
including:
- Creating a virtual environment
- Installing dependencies
- Setting up pre-commit hooks
- Configuring development tools
"""

import argparse
import os
import platform
import subprocess
import sys
import venv
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Setup development environment for Altium to KiCAD Migration Tool"
    )
    parser.add_argument(
        "--venv-dir",
        default=".venv",
        help="Directory for virtual environment (default: .venv)",
    )
    parser.add_argument(
        "--python",
        default=None,
        help="Python executable to use (default: current Python)",
    )
    parser.add_argument(
        "--with-odbc",
        action="store_true",
        help="Install ODBC drivers (requires admin/sudo)",
    )
    parser.add_argument(
        "--no-pre-commit",
        action="store_true",
        help="Skip pre-commit hooks installation",
    )
    return parser.parse_args()


def create_venv(venv_dir, python=None):
    """Create a virtual environment."""
    print(f"Creating virtual environment in {venv_dir}...")
    venv_builder = venv.EnvBuilder(with_pip=True)
    venv_builder.create(venv_dir)
    return Path(venv_dir)


def get_venv_python(venv_dir):
    """Get the Python executable path from the virtual environment."""
    if platform.system() == "Windows":
        return Path(venv_dir) / "Scripts" / "python.exe"
    return Path(venv_dir) / "bin" / "python"


def install_dependencies(venv_python):
    """Install project dependencies."""
    print("Installing development dependencies...")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-e", ".[dev]"],
        check=True,
    )
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", "requirements-dev.txt"],
        check=True,
    )


def install_odbc_drivers():
    """Install ODBC drivers based on the platform."""
    system = platform.system()
    print(f"Installing ODBC drivers for {system}...")

    if system == "Windows":
        print(
            "Please download and install Microsoft Access Database Engine from:\n"
            "https://www.microsoft.com/en-us/download/details.aspx?id=54920"
        )
    elif system == "Linux":
        try:
            subprocess.run(
                ["sudo", "apt-get", "update"],
                check=True,
            )
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", "unixodbc-dev"],
                check=True,
            )
        except subprocess.CalledProcessError:
            print("Failed to install ODBC drivers. Please install manually.")
    elif system == "Darwin":  # macOS
        try:
            subprocess.run(
                ["brew", "install", "unixodbc"],
                check=True,
            )
        except subprocess.CalledProcessError:
            print(
                "Failed to install ODBC drivers. Please install manually:\n"
                "brew install unixodbc"
            )
    else:
        print(f"Unsupported platform: {system}. Please install ODBC drivers manually.")


def setup_pre_commit(venv_python):
    """Set up pre-commit hooks."""
    print("Setting up pre-commit hooks...")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "pre-commit"],
        check=True,
    )
    subprocess.run(
        [str(venv_python), "-m", "pre_commit", "install"],
        check=True,
    )


def create_env_file():
    """Create a .env file with development settings."""
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file with development settings...")
        env_content = """# Development environment settings
DEBUG=True
LOG_LEVEL=DEBUG
"""
        env_file.write_text(env_content)


def main():
    """Main function to set up the development environment."""
    args = parse_args()

    # Ensure we're in the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Create virtual environment
    venv_dir = create_venv(args.venv_dir, args.python)
    venv_python = get_venv_python(venv_dir)

    # Install dependencies
    install_dependencies(venv_python)

    # Install ODBC drivers if requested
    if args.with_odbc:
        install_odbc_drivers()

    # Set up pre-commit hooks
    if not args.no_pre_commit:
        setup_pre_commit(venv_python)

    # Create .env file
    create_env_file()

    print("\nDevelopment environment setup complete!")
    print(f"Virtual environment created at: {venv_dir}")
    print("\nTo activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"    {venv_dir}\\Scripts\\activate")
    else:
        print(f"    source {venv_dir}/bin/activate")

    print("\nTo run tests:")
    print("    make test")
    print("\nTo run the application:")
    print("    make run-cli")
    print("    make run-gui")


if __name__ == "__main__":
    main()