#!/usr/bin/env python3
"""
Altium to KiCAD Database Migration Tool - GUI Launcher

This script provides a convenient way to launch the graphical user interface
for the Altium to KiCAD Database Migration Tool.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to the Python path if running from the project directory
project_root = Path(__file__).resolve().parent
if project_root not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the GUI module
try:
    from migration_tool.gui import main as gui_main
except ImportError:
    print("Error: Could not import the migration_tool package.")
    print("Make sure the package is installed or you are running this script from the project root.")
    sys.exit(1)

def setup_logging(verbose=False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Launch the Altium to KiCAD Database Migration Tool GUI"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        type=str
    )
    parser.add_argument(
        "--verbose", "-v",
        help="Enable verbose logging",
        action="store_true"
    )
    parser.add_argument(
        "--theme", "-t",
        help="GUI theme (light, dark, system)",
        choices=["light", "dark", "system"],
        default="system"
    )
    parser.add_argument(
        "--size", "-s",
        help="Initial window size (width,height)",
        type=str,
        default="1024,768"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the GUI launcher."""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    # Parse window size
    try:
        width, height = map(int, args.size.split(","))
    except ValueError:
        print(f"Error: Invalid window size format: {args.size}")
        print("Expected format: width,height (e.g., 1024,768)")
        sys.exit(1)
    
    # Launch the GUI
    gui_main(
        config_path=args.config,
        theme=args.theme,
        window_size=(width, height)
    )

if __name__ == "__main__":
    main()