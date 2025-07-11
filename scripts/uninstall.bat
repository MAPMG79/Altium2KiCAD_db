@echo off
:: Altium to KiCAD Database Migration Tool - Uninstallation Script for Windows
:: This script uninstalls the Altium to KiCAD Database Migration Tool

echo Altium to KiCAD Database Migration Tool - Uninstallation
echo This script will uninstall the Altium to KiCAD Database Migration Tool.
echo.

:: Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

:: Check if pip is installed
python -m pip --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: pip is not installed.
    exit /b 1
)

:: Check for virtual environment
set venv_dir=%USERPROFILE%\.venvs\altium2kicad
if exist "%venv_dir%" (
    echo Virtual environment detected at %venv_dir%
    set /p remove_venv=Do you want to remove the virtual environment? (y/n): 
    
    if /i "%remove_venv%"=="y" (
        echo Removing virtual environment...
        rmdir /s /q "%venv_dir%"
        echo Virtual environment removed.
    ) else (
        echo Virtual environment will be kept.
    )
)

:: Remove wrapper batch files
set wrapper_dir=%USERPROFILE%\bin
if exist "%wrapper_dir%\altium2kicad.bat" (
    echo Wrapper batch files detected in %wrapper_dir%
    set /p remove_wrappers=Do you want to remove the wrapper batch files? (y/n): 
    
    if /i "%remove_wrappers%"=="y" (
        echo Removing wrapper batch files...
        if exist "%wrapper_dir%\altium2kicad.bat" del "%wrapper_dir%\altium2kicad.bat"
        if exist "%wrapper_dir%\altium2kicad-gui.bat" del "%wrapper_dir%\altium2kicad-gui.bat"
        if exist "%wrapper_dir%\altium2kicad-api.bat" del "%wrapper_dir%\altium2kicad-api.bat"
        echo Wrapper batch files removed.
    ) else (
        echo Wrapper batch files will be kept.
    )
)

:: Uninstall the package
echo Uninstalling Altium to KiCAD Database Migration Tool...
python -m pip uninstall -y altium2kicad

echo Uninstallation completed successfully!

:: Ask about configuration files
set /p remove_config=Do you want to remove configuration files? (y/n): 

if /i "%remove_config%"=="y" (
    set config_dir=%APPDATA%\altium2kicad
    if exist "%config_dir%" (
        echo Removing configuration files...
        rmdir /s /q "%config_dir%"
        echo Configuration files removed.
    ) else (
        echo No configuration files found.
    )
) else (
    echo Configuration files will be kept.
)

echo.
echo Thank you for using Altium to KiCAD Database Migration Tool!