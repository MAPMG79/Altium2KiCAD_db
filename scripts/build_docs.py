#!/usr/bin/env python3
"""
Script to build documentation and place it in the docs_build folder.
This helps with readthedocs.org build issues by providing a local build option.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs"
    build_dir = project_root / "docs_build"
    
    # Ensure the build directory exists
    os.makedirs(build_dir / "html", exist_ok=True)
    
    print(f"Building documentation from {docs_dir}...")
    
    # Change to the docs directory
    os.chdir(docs_dir)
    
    # Build the documentation
    try:
        # First, try using make
        result = subprocess.run(["make", "html"], capture_output=True, text=True)
        if result.returncode != 0:
            print("Make build failed, trying sphinx-build directly...")
            # If make fails, try using sphinx-build directly
            result = subprocess.run(
                ["sphinx-build", "-b", "html", ".", "../docs_build/html"],
                capture_output=True,
                text=True
            )
    except FileNotFoundError:
        # If make is not available, use sphinx-build directly
        print("Make not found, using sphinx-build directly...")
        result = subprocess.run(
            ["sphinx-build", "-b", "html", ".", "../docs_build/html"],
            capture_output=True,
            text=True
        )
    
    # Print the output
    print(result.stdout)
    if result.stderr:
        print("Errors/Warnings:")
        print(result.stderr)
    
    # Check if the build was successful
    if result.returncode != 0:
        print("Documentation build failed!")
        return 1
    
    # If make was successful, copy the files to the docs_build directory
    if os.path.exists(docs_dir / "_build" / "html"):
        print("Copying files from _build/html to docs_build/html...")
        # Clear the destination directory first
        for item in os.listdir(build_dir / "html"):
            item_path = build_dir / "html" / item
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        
        # Copy the files
        for item in os.listdir(docs_dir / "_build" / "html"):
            src = docs_dir / "_build" / "html" / item
            dst = build_dir / "html" / item
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    
    print(f"Documentation built successfully! Output is in {build_dir}/html")
    return 0

if __name__ == "__main__":
    sys.exit(main())