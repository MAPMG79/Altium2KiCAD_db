#!/bin/bash
# Altium to KiCAD Database Migration Tool - Uninstallation Script for Linux/macOS
# This script uninstalls the Altium to KiCAD Database Migration Tool

set -e  # Exit on error

# Print with colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Altium to KiCAD Database Migration Tool - Uninstallation${NC}"
echo "This script will uninstall the Altium to KiCAD Database Migration Tool."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed.${NC}"
    exit 1
fi

# Check for virtual environment
venv_dir="$HOME/.venvs/altium2kicad"
if [ -d "$venv_dir" ]; then
    echo -e "${YELLOW}Virtual environment detected at $venv_dir${NC}"
    read -p "Do you want to remove the virtual environment? (y/n): " remove_venv
    
    if [[ $remove_venv == "y" || $remove_venv == "Y" ]]; then
        echo -e "${YELLOW}Removing virtual environment...${NC}"
        rm -rf "$venv_dir"
        echo -e "${GREEN}Virtual environment removed.${NC}"
    else
        echo "Virtual environment will be kept."
    fi
fi

# Remove wrapper scripts
wrapper_dir="$HOME/.local/bin"
if [ -f "$wrapper_dir/altium2kicad" ] || [ -f "$wrapper_dir/altium2kicad-gui" ] || [ -f "$wrapper_dir/altium2kicad-api" ]; then
    echo -e "${YELLOW}Wrapper scripts detected in $wrapper_dir${NC}"
    read -p "Do you want to remove the wrapper scripts? (y/n): " remove_wrappers
    
    if [[ $remove_wrappers == "y" || $remove_wrappers == "Y" ]]; then
        echo -e "${YELLOW}Removing wrapper scripts...${NC}"
        rm -f "$wrapper_dir/altium2kicad"
        rm -f "$wrapper_dir/altium2kicad-gui"
        rm -f "$wrapper_dir/altium2kicad-api"
        echo -e "${GREEN}Wrapper scripts removed.${NC}"
    else
        echo "Wrapper scripts will be kept."
    fi
fi

# Uninstall the package
echo -e "${YELLOW}Uninstalling Altium to KiCAD Database Migration Tool...${NC}"
pip3 uninstall -y altium2kicad

echo -e "${GREEN}Uninstallation completed successfully!${NC}"

# Ask about configuration files
read -p "Do you want to remove configuration files? (y/n): " remove_config

if [[ $remove_config == "y" || $remove_config == "Y" ]]; then
    config_dir="$HOME/.config/altium2kicad"
    if [ -d "$config_dir" ]; then
        echo -e "${YELLOW}Removing configuration files...${NC}"
        rm -rf "$config_dir"
        echo -e "${GREEN}Configuration files removed.${NC}"
    else
        echo "No configuration files found."
    fi
else
    echo "Configuration files will be kept."
fi

echo ""
echo "Thank you for using Altium to KiCAD Database Migration Tool!"