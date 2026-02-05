@echo off
cd %~dp0

REM Configure QGIS installation root (can be overridden by pre-setting QGIS_ROOT)
if not defined QGIS_ROOT set "QGIS_ROOT=C:\PROGRA~1\QGIS_3"

call "%QGIS_ROOT%\bin\o4w_env.bat"

set PYTHONPATH=%QGIS_ROOT%\apps\Python312\Scripts;%PYTHONPATH%
REM Prompt user for QGIS profile
echo.
echo Available QGIS profiles (common options):
echo   - QGIS3 (default)
echo   - QGIS-LTR
echo   - Your custom profile name
echo.

set /p QGIS_PROFILE="Enter QGIS profile name (or press Enter for QGIS3): "

REM Use default if no input provided
if "%QGIS_PROFILE%"=="" set QGIS_PROFILE=QGIS3

echo.
echo Installing to profile: %QGIS_PROFILE%
echo.

python setup.py install --profile %QGIS_PROFILE%

pause

