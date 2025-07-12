@echo off
REM Script to build documentation and place it in the docs_build folder
REM This helps with readthedocs.org build issues by providing a local build option

echo Building documentation...

REM Get the project root directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set DOCS_DIR=%PROJECT_ROOT%\docs
set BUILD_DIR=%PROJECT_ROOT%\docs_build\html

REM Ensure the build directory exists
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

REM Change to the docs directory
cd "%DOCS_DIR%"

REM Try to build the documentation using make
where make >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Using make to build documentation...
    make html
    if %ERRORLEVEL% NEQ 0 (
        echo Make build failed, trying sphinx-build directly...
        goto USE_SPHINX
    )
) else (
    echo Make not found, using sphinx-build directly...
    :USE_SPHINX
    where sphinx-build >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        sphinx-build -b html . ..\docs_build\html
    ) else (
        echo ERROR: sphinx-build not found. Please install Sphinx:
        echo pip install sphinx sphinx_rtd_theme
        exit /b 1
    )
)

REM If make was successful, copy the files to the docs_build directory
if exist "%DOCS_DIR%\_build\html" (
    echo Copying files from _build\html to docs_build\html...
    
    REM Clear the destination directory first
    del /q "%BUILD_DIR%\*" >nul 2>&1
    for /d %%x in ("%BUILD_DIR%\*") do @rd /s /q "%%x" >nul 2>&1
    
    REM Copy the files
    xcopy "%DOCS_DIR%\_build\html\*" "%BUILD_DIR%\" /E /I /Y
)

echo Documentation built successfully! Output is in %BUILD_DIR%
echo You can open %BUILD_DIR%\index.html in your browser to view it.

REM Open the documentation in the default browser
start "" "%BUILD_DIR%\index.html"

exit /b 0