@echo off
echo Building Configurable Search QGIS Plugin...
call "C:\PROGRA~1\QGIS_3\bin\o4w_env.bat"
set PYTHONPATH=C:\PROGRA~1\QGIS_3\apps\Python312\Scripts;%PYTHONPATH%
REM Create resources file
call pyrcc5 -o resources.py resources.qrc 2>nul
if %ERRORLEVEL% neq 0 (
    echo Warning: Could not build resources with pyrcc5.
    echo Using fallback resources.py file instead.
    echo Note: This is normal if PyQt5 tools are not installed.
)

REM Create plugin zip
if exist configurable_search.zip del configurable_search.zip

echo Creating plugin package...
if exist powershell.exe (
    powershell -command "Compress-Archive -Path *.py, *.txt, *.md, *.svg, *.qrc -DestinationPath configurable_search.zip"
) else (
    echo PowerShell not available, creating package manually...
    REM Create a simple archive using built-in tools or skip
    echo Please manually create a zip file with all plugin files.
)

echo Plugin build complete: configurable_search.zip

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
