#!/bin/bash
# Altium to KiCAD Database Migration Tool - Installation Script for Linux/macOS
# This script installs the Altium to KiCAD Database Migration Tool and its dependencies

set -e  # Exit on error

# Print with colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Altium to KiCAD Database Migration Tool - Installation${NC}"
echo "This script will install the Altium to KiCAD Database Migration Tool and its dependencies."
echo ""

# Check if Python 3.7+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ -z "$python_version" ]]; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.7 or higher before continuing."
    exit 1
fi

major=$(echo $python_version | cut -d. -f1)
minor=$(echo $python_version | cut -d. -f2)

if [[ $major -lt 3 || ($major -eq 3 && $minor -lt 7) ]]; then
    echo -e "${RED}Error: Python version must be 3.7 or higher.${NC}"
    echo "Current version: $python_version"
    echo "Please upgrade Python before continuing."
    exit 1
fi

echo -e "${GREEN}Python version $python_version detected.${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed.${NC}"
    echo "Please install pip3 before continuing."
    exit 1
fi

echo -e "${GREEN}pip3 detected.${NC}"

# Check if virtual environment is requested
use_venv=false
install_dir="$HOME/.local/bin"

read -p "Do you want to install in a virtual environment? (y/n) [recommended: y]: " venv_choice
if [[ $venv_choice == "y" || $venv_choice == "Y" ]]; then
    use_venv=true
    
    # Check if venv module is available
    if ! python3 -c "import venv" &> /dev/null; then
        echo -e "${RED}Error: Python venv module is not available.${NC}"
        echo "Please install the Python venv module before continuing."
        exit 1
    fi
    
    # Create virtual environment
    venv_dir="$HOME/.venvs/altium2kicad"
    echo -e "${YELLOW}Creating virtual environment in $venv_dir...${NC}"
    python3 -m venv "$venv_dir"
    
    # Activate virtual environment
    source "$venv_dir/bin/activate"
    install_dir="$venv_dir/bin"
    
    echo -e "${GREEN}Virtual environment created and activated.${NC}"
fi

# Install the package
echo -e "${YELLOW}Installing Altium to KiCAD Database Migration Tool...${NC}"

# Determine installation method
if [ -f "setup.py" ]; then
    # Development mode installation (from source)
    pip3 install -e .
elif [ -f "dist/altium2kicad-1.0.0.tar.gz" ]; then
    # Install from source distribution
    pip3 install dist/altium2kicad-1.0.0.tar.gz
elif [ -f "dist/altium2kicad-1.0.0-py3-none-any.whl" ]; then
    # Install from wheel
    pip3 install dist/altium2kicad-1.0.0-py3-none-any.whl
else
    # Install from PyPI
    pip3 install altium2kicad
fi

# Create symlinks for convenience
if [[ $use_venv == true ]]; then
    mkdir -p "$HOME/.local/bin"
    
    # Create wrapper scripts
    echo -e "${YELLOW}Creating wrapper scripts in $HOME/.local/bin...${NC}"
    
    # CLI wrapper
    cat > "$HOME/.local/bin/altium2kicad" << EOF
#!/bin/bash
source "$venv_dir/bin/activate"
altium2kicad "\$@"
EOF
    chmod +x "$HOME/.local/bin/altium2kicad"
    
    # GUI wrapper
    cat > "$HOME/.local/bin/altium2kicad-gui" << EOF
#!/bin/bash
source "$venv_dir/bin/activate"
altium2kicad-gui "\$@"
EOF
    chmod +x "$HOME/.local/bin/altium2kicad-gui"
    
    # API wrapper
    cat > "$HOME/.local/bin/altium2kicad-api" << EOF
#!/bin/bash
source "$venv_dir/bin/activate"
altium2kicad-api "\$@"
EOF
    chmod +x "$HOME/.local/bin/altium2kicad-api"
    
    echo -e "${GREEN}Wrapper scripts created.${NC}"
    echo "Make sure $HOME/.local/bin is in your PATH."
fi

echo -e "${GREEN}Installation completed successfully!${NC}"

if [[ $use_venv == true ]]; then
    echo ""
    echo "The tool is installed in a virtual environment at: $venv_dir"
    echo "You can activate the virtual environment with:"
    echo "  source $venv_dir/bin/activate"
    echo ""
    echo "Or use the wrapper scripts in $HOME/.local/bin:"
    echo "  altium2kicad - Command-line interface"
    echo "  altium2kicad-gui - Graphical user interface"
    echo "  altium2kicad-api - API server"
else
    echo ""
    echo "The following commands are now available:"
    echo "  altium2kicad - Command-line interface"
    echo "  altium2kicad-gui - Graphical user interface"
    echo "  altium2kicad-api - API server"
fi

echo ""
echo "To verify the installation, run:"
echo "  altium2kicad --version"