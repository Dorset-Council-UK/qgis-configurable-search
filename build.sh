#!/bin/bash

echo "Building Configurable Search QGIS Plugin..."

# Create resources file
if command -v pyrcc5 &> /dev/null; then
    pyrcc5 -o resources.py resources.qrc
    echo "Resources built successfully"
else
    echo "Warning: pyrcc5 not found. Resources file not updated."
    echo "You may need to install PyQt5-tools: pip install PyQt5-tools"
fi

# Create plugin zip
if [ -f "configurable_search.zip" ]; then
    rm configurable_search.zip
fi

echo "Creating plugin package..."
zip -r configurable_search.zip *.py *.txt *.md *.png *.qrc

echo "Plugin build complete: configurable_search.zip"

echo ""
echo "To install:"
echo "1. Copy this folder to your QGIS plugins directory, or"
echo "2. Install the zip file through QGIS Plugin Manager"
echo ""
echo "Plugin directory locations:"
echo "Linux: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/"
echo "macOS: ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/"
echo "Windows: %APPDATA%\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"
