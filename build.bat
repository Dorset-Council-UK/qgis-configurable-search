@echo off
echo Building Configurable Search QGIS Plugin...

REM Configure QGIS installation root (can be overridden by pre-setting QGIS_ROOT)
if not defined QGIS_ROOT set "QGIS_ROOT=C:\PROGRA~1\QGIS_3"

call "%QGIS_ROOT%\bin\o4w_env.bat"

set PYTHONPATH=%QGIS_ROOT%\apps\Python312\Scripts;%PYTHONPATH%

REM Prompt user for output location
set /p OUTPUT_FOLDER="Enter output location (blank for current directory): "

REM Use default if no input provided
if "%OUTPUT_FOLDER%"=="" set OUTPUT_FOLDER=%~dp0

echo.
echo Outputting configurable_search.zip to: %OUTPUT_FOLDER%
echo.

REM Create resources file
call pyrcc5 -o resources.py resources.qrc 2>nul
if %ERRORLEVEL% neq 0 (
    echo Warning: Could not build resources with pyrcc5.
    echo Using fallback resources.py file instead.
    echo Note: This is normal if PyQt5 tools are not installed.
)

REM Create plugin zip
if exist "%OUTPUT_FOLDER%\configurable_search.zip" del "%OUTPUT_FOLDER%\configurable_search.zip"

echo Creating plugin package...
REM Use full path to PowerShell instead of relying on PATH
if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
    "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -command "Compress-Archive -Path *.py, *.txt, *.md, *.svg, *.qrc, help -DestinationPath '%OUTPUT_FOLDER%\configurable_search.zip'"
    echo Plugin build complete: %OUTPUT_FOLDER%\configurable_search.zip
) else (
    echo PowerShell not available, creating package manually...
    REM Create a simple archive using built-in tools or skip
    echo Please manually create a zip file with all plugin files.
)

echo.
echo To install:
echo 1. Copy this folder to your QGIS plugins directory, or
echo 2. Install the zip file through QGIS Plugin Manager
echo.
echo Plugin directory locations:
echo Windows: %%APPDATA%%\QGIS\QGIS3\profiles\default\python\plugins\
echo Linux: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
echo macOS: ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/

pause
