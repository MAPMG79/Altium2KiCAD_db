#!/usr/bin/env python3
"""
Altium to KiCAD Database Migration Tool - API Server Launcher

This script provides a convenient way to launch the API server
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

# Import the API module
try:
    from migration_tool.api import start_api_server
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
        description="Launch the Altium to KiCAD Database Migration Tool API Server"
    )
    parser.add_argument(
        "--host", "-H",
        help="Host to bind the server to",
        type=str,
        default="127.0.0.1"
    )
    parser.add_argument(
        "--port", "-p",
        help="Port to bind the server to",
        type=int,
        default=8000
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
        "--reload",
        help="Enable auto-reload for development",
        action="store_true"
    )
    parser.add_argument(
        "--workers", "-w",
        help="Number of worker processes",
        type=int,
        default=1
    )
    parser.add_argument(
        "--ssl-cert",
        help="Path to SSL certificate file",
        type=str
    )
    parser.add_argument(
        "--ssl-key",
        help="Path to SSL key file",
        type=str
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the API server launcher."""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    # Check if SSL is enabled
    ssl_context = None
    if args.ssl_cert and args.ssl_key:
        import ssl
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(args.ssl_cert, args.ssl_key)
    
    # Launch the API server
    start_api_server(
        host=args.host,
        port=args.port,
        config_path=args.config,
        reload=args.reload,
        workers=args.workers,
        ssl_context=ssl_context
    )

if __name__ == "__main__":
    main()