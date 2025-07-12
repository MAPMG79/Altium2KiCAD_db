#!/bin/bash
# Script to build documentation and place it in the docs_build folder
# This helps with readthedocs.org build issues by providing a local build option

echo "Building documentation..."

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"
BUILD_DIR="$PROJECT_ROOT/docs_build/html"

# Ensure the build directory exists
mkdir -p "$BUILD_DIR"

# Change to the docs directory
cd "$DOCS_DIR"

# Try to build the documentation using make
if command -v make &> /dev/null; then
    echo "Using make to build documentation..."
    make html
    if [ $? -ne 0 ]; then
        echo "Make build failed, trying sphinx-build directly..."
        USE_SPHINX=1
    fi
else
    echo "Make not found, using sphinx-build directly..."
    USE_SPHINX=1
fi

# If make failed or is not available, use sphinx-build directly
if [ -n "$USE_SPHINX" ]; then
    if command -v sphinx-build &> /dev/null; then
        sphinx-build -b html . ../docs_build/html
    else
        echo "ERROR: sphinx-build not found. Please install Sphinx:"
        echo "pip install sphinx sphinx_rtd_theme"
        exit 1
    fi
fi

# If make was successful, copy the files to the docs_build directory
if [ -d "$DOCS_DIR/_build/html" ]; then
    echo "Copying files from _build/html to docs_build/html..."
    
    # Clear the destination directory first
    rm -rf "$BUILD_DIR"/*
    
    # Copy the files
    cp -r "$DOCS_DIR/_build/html/"* "$BUILD_DIR/"
fi

echo "Documentation built successfully! Output is in $BUILD_DIR"
echo "You can open $BUILD_DIR/index.html in your browser to view it."

# Try to open the documentation in the default browser
if command -v xdg-open &> /dev/null; then
    xdg-open "$BUILD_DIR/index.html" &> /dev/null &
elif command -v open &> /dev/null; then
    open "$BUILD_DIR/index.html" &> /dev/null &
fi

exit 0