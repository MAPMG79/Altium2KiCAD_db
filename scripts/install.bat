@echo off
:: Altium to KiCAD Database Migration Tool - Installation Script for Windows
:: This script installs the Altium to KiCAD Database Migration Tool and its dependencies

echo Altium to KiCAD Database Migration Tool - Installation
echo This script will install the Altium to KiCAD Database Migration Tool and its dependencies.
echo.

:: Check if Python 3.7+ is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.7 or higher before continuing.
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set python_version=%%V

:: Extract major and minor version
for /f "tokens=1,2 delims=." %%a in ("%python_version%") do (
    set major=%%a
    set minor=%%b
)

:: Check if Python version is 3.7+
if %major% LSS 3 (
    echo Error: Python version must be 3.7 or higher.
    echo Current version: %python_version%
    echo Please upgrade Python before continuing.
    exit /b 1
)

if %major% EQU 3 (
    if %minor% LSS 7 (
        echo Error: Python version must be 3.7 or higher.
        echo Current version: %python_version%
        echo Please upgrade Python before continuing.
        exit /b 1
    )
)

echo Python version %python_version% detected.

:: Check if pip is installed
python -m pip --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: pip is not installed.
    echo Please install pip before continuing.
    exit /b 1
)

echo pip detected.

:: Ask if virtual environment is requested
set /p venv_choice=Do you want to install in a virtual environment? (y/n) [recommended: y]: 

if /i "%venv_choice%"=="y" (
    :: Check if venv module is available
    python -c "import venv" > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Python venv module is not available.
        echo Please install the Python venv module before continuing.
        exit /b 1
    )
    
    :: Create virtual environment
    set venv_dir=%USERPROFILE%\.venvs\altium2kicad
    echo Creating virtual environment in %venv_dir%...
    python -m venv "%venv_dir%"
    
    :: Activate virtual environment
    call "%venv_dir%\Scripts\activate.bat"
    
    echo Virtual environment created and activated.
) else (
    echo Installing globally...
)

:: Install the package
echo Installing Altium to KiCAD Database Migration Tool...

:: Determine installation method
if exist setup.py (
    :: Development mode installation (from source)
    python -m pip install -e .
) else if exist dist\altium2kicad-1.0.0.tar.gz (
    :: Install from source distribution
    python -m pip install dist\altium2kicad-1.0.0.tar.gz
) else if exist dist\altium2kicad-1.0.0-py3-none-any.whl (
    :: Install from wheel
    python -m pip install dist\altium2kicad-1.0.0-py3-none-any.whl
) else (
    :: Install from PyPI
    python -m pip install altium2kicad
)

:: Create batch files for convenience if using virtual environment
if /i "%venv_choice%"=="y" (
    echo Creating wrapper batch files...
    
    :: Create directory for batch files
    if not exist "%USERPROFILE%\bin" mkdir "%USERPROFILE%\bin"
    
    :: CLI wrapper
    (
        echo @echo off
        echo call "%venv_dir%\Scripts\activate.bat"
        echo altium2kicad %%*
    ) > "%USERPROFILE%\bin\altium2kicad.bat"
    
    :: GUI wrapper
    (
        echo @echo off
        echo call "%venv_dir%\Scripts\activate.bat"
        echo altium2kicad-gui %%*
    ) > "%USERPROFILE%\bin\altium2kicad-gui.bat"
    
    :: API wrapper
    (
        echo @echo off
        echo call "%venv_dir%\Scripts\activate.bat"
        echo altium2kicad-api %%*
    ) > "%USERPROFILE%\bin\altium2kicad-api.bat"
    
    echo Wrapper batch files created in %USERPROFILE%\bin
    echo Make sure %USERPROFILE%\bin is in your PATH.
)

echo Installation completed successfully!

if /i "%venv_choice%"=="y" (
    echo.
    echo The tool is installed in a virtual environment at: %venv_dir%
    echo You can activate the virtual environment with:
    echo   call "%venv_dir%\Scripts\activate.bat"
    echo.
    echo Or use the wrapper batch files in %USERPROFILE%\bin:
    echo   altium2kicad.bat - Command-line interface
    echo   altium2kicad-gui.bat - Graphical user interface
    echo   altium2kicad-api.bat - API server
) else (
    echo.
    echo The following commands are now available:
    echo   altium2kicad - Command-line interface
    echo   altium2kicad-gui - Graphical user interface
    echo   altium2kicad-api - API server
)

echo.
echo To verify the installation, run:
echo   altium2kicad --version