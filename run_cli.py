#!/usr/bin/env python3
"""
Altium to KiCAD Database Migration Tool - CLI Launcher

This script provides a convenient way to launch the command-line interface
for the Altium to KiCAD Database Migration Tool.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path if running from the project directory
project_root = Path(__file__).resolve().parent
if project_root not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the CLI module
try:
    from migration_tool.cli import main as cli_main
except ImportError:
    print("Error: Could not import the migration_tool package.")
    print("Make sure the package is installed or you are running this script from the project root.")
    sys.exit(1)

def main():
    """Main entry point for the CLI launcher."""
    # Pass all command-line arguments to the CLI main function
    cli_main()

if __name__ == "__main__":
    main()