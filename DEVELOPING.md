# Developing

## Installation

1. Download or clone this repository to your QGIS plugins directory:
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

2. Rename the folder to `configurable_search`

3. Start QGIS and enable the plugin in the Plugin Manager

## Compilation

To test any local changes you should compile the project using the provided `Compile_publish.bat` 
(Windows) script.

The script will ask you to specify which QGIS profile to publish the results into as you may have 
multiple profiles associated with your QGIS installation. You can also control the installation 
path of QGIS itself as the script uses the QGIS python environment to compile the resources.

## Packaging

To package the plugin for distribution, use the provided `Package.bat` (Windows)
This will generate a ZIP file in a directory of your choice that can be uploaded to a QGIS repository. 

## Project Structure
```
qgis-configurable-search/
├── __init__.py                     # Plugin entry point
├── Compile_publish.bat             # Windows compilation script
├── configurable_search.py          # Main plugin class
├── configurable_search_dialog.py   # Configuration dialog UI
├── config_manager.py               # Configuration management & import/export
├── search_engine.py                # Search logic and API handling
├── provider_templates.py           # Pre-configured API provider templates
├── help.py                         # Help system integration
├── resources.py                    # Qt resources (generated)
├── resources.qrc                   # Resource file definitions
├── metadata.txt                    # Plugin metadata for QGIS
├── setup.py                        # Installation script
├── test_plugin.py                  # Plugin tests
├── requirements.txt                # Python dependencies
├── example_export.json             # Sample configuration export
├── help/                           # Help documentation
│   ├── source/
│   │   ├── index.html              # Main help documentation
│   │   ├── default.css             # Help page styling
│   │   └── img/                    # Screenshots and images
│   └── README.md                   # Help documentation guide
├── icon.svg                        # Main plugin icon
├── icon-mono-configure.svg         # Configuration button icon
├── icon-mono-help.svg              # Help button icon
├── icon-mono-search.svg            # Search button icon
├── Package.bat                     # Windows packaging script
├── Makefile                        # Build automation
├── .gitignore                      # Git ignore rules
├── LICENCE                         # License file
├── CODE_OF_CONDUCT.md              # Code of conduct
├── CONTRIBUTING.md                 # Contributing guidelines
├── SECURITY.md                     # Security policy
├── DEVELOPING.md                   # Development documentation
└── README.md                       # Main documentation