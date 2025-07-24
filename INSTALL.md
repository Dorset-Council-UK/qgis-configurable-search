# Installation Guide for Configurable Search QGIS Plugin

## Quick Installation

### Method 1: Using Setup Script (Recommended)
1. Open a terminal/command prompt in the plugin directory
2. Run: `python setup.py install`
3. Restart QGIS
4. Enable the plugin in `Plugins > Manage and Install Plugins`

### Method 2: Manual Installation
1. Copy the entire plugin folder to your QGIS plugins directory:
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\configurable_search`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/configurable_search`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/configurable_search`
2. Restart QGIS
3. Enable the plugin in the Plugin Manager

### Method 3: Development Setup
For developers who want to modify the plugin:
1. Run: `python setup.py dev`
2. This creates a symbolic link so changes are reflected immediately
3. Restart QGIS to load changes

## Building from Source

### Prerequisites
- Python 3.6 or higher
- PyQt5 development tools (optional, for building resources)

### Build Steps
1. **Install PyQt5 tools** (optional):
   ```bash
   pip install PyQt5-tools
   ```

2. **Build resources** (if you modify resources.qrc):
   ```bash
   pyrcc5 -o resources.py resources.qrc
   ```

3. **Create distribution package**:
   - **Windows**: Run `build.bat`
   - **Linux/macOS**: Run `bash build.sh` or `make zip`

## Configuration

After installation, configure the plugin:

1. **Access Configuration**:
   - Click the search configuration button in the toolbar, or
   - Go to `Plugins > Configurable Search > Configure Search`

2. **Add API Providers** (examples):
   - **OpenStreetMap Nominatim**:
     - URL: `https://nominatim.openstreetmap.org/search?q={search_term}&format=json&limit=5`
     - Name field: `display_name`
     - Lat field: `lat`, Lon field: `lon`
   
   - **Google Geocoding** (requires API key):
     - URL: `https://maps.googleapis.com/maps/api/geocode/json?address={search_term}&key=YOUR_API_KEY`
     - Name field: `results.0.formatted_address`
     - Lat field: `results.0.geometry.location.lat`

3. **Configure Layer Search**:
   - Enable searching project layers
   - Set maximum features per layer
   - Choose which layer fields to search

4. **Set General Options**:
   - Configure search timeouts
   - Set result limits
   - Choose search behavior

## Usage

1. **Basic Search**:
   - Type in the search bar and press Enter
   - Results will zoom the map to found locations

2. **Coordinate Search**:
   - Enter coordinates like "40.7128, -74.0060"
   - The map will zoom to that location

3. **Layer Search**:
   - Search for layer names or feature attributes
   - Results will highlight matching layers/features

## Troubleshooting

### Plugin Won't Load
- Check QGIS version (requires 3.16+)
- Verify plugin is in correct directory
- Check QGIS Python console for error messages

### Search Not Working
- Verify internet connection for API searches
- Check API provider configurations
- Review search regex filters
- Check QGIS message log for errors

### Configuration Dialog Issues
- Restart QGIS if dialog doesn't appear
- Check for conflicting plugins
- Verify PyQt5 installation

### API Search Errors
- Check API endpoint URLs
- Verify API keys and authentication
- Test URLs manually in a browser
- Check rate limits and usage quotas

## Development

### Project Structure
```
configurable_search/
├── __init__.py                     # Plugin entry point
├── configurable_search.py          # Main plugin class and search widget
├── config_manager.py              # Configuration management
├── search_engine.py               # Search logic and API handling
├── configurable_search_dialog.py  # Configuration dialog UI
├── resources.py                   # Qt resources (generated)
├── resources.qrc                  # Resource definitions
├── metadata.txt                   # Plugin metadata
└── README.md                      # Documentation
```

### Key Classes
- **ConfigurableSearch**: Main plugin class
- **SearchWidget**: Toolbar search widget
- **SearchEngine**: Handles search logic and API calls
- **ConfigManager**: Manages plugin settings
- **ConfigurableSearchDialog**: Configuration UI

### Extending the Plugin
1. **Adding New Provider Types**:
   - Extend `SearchEngine._search_provider()`
   - Add new provider type to configuration dialog

2. **Custom Result Parsers**:
   - Modify `SearchEngine._parse_api_results()`
   - Add new parser options to provider configuration

3. **Additional Search Sources**:
   - Extend `SearchEngine.search()`
   - Add new search methods

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: See README.md for detailed documentation
- **QGIS Community**: Ask questions on QGIS forums
- **Plugin Documentation**: Visit QGIS plugin development docs

## License

This plugin is released under the GPL v3 license.
