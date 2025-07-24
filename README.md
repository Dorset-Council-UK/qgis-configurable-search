# Configurable Search QGIS Plugin

A modern QGIS plugin that adds a powerful configurable search panel to QGIS. This plugin provides a dockable search interface that allows users to search through multiple APIs and project layers with customizable templates, ordering, and regex filtering.

## Features

### 🔍 **Multi-Source Search**
- Search through multiple API endpoints simultaneously
- Search within project layers and their features
- Coordinate-based search with automatic detection
- Configurable search order and priority
- **Interactive results list** with clickable items
- **Persistent results display** - results remain visible after clicking
- **Loading indicators** with visual feedback during search

### ⚙️ **Advanced Configuration**
- **API Providers**: Add custom API endpoints with URL templates
- **QGIS Authentication**: Use QGIS authentication configurations for secure API access
- **Regex Filtering**: Use regular expressions to determine search relevance
- **Custom Headers**: Support for manual headers alongside authentication
- **Result Parsing**: Configure how to extract location data from API responses
- **Search Behavior**: Control search stopping, timeouts, and result limits
- **Smart Zoom Levels**: Automatic zoom detection based on coordinate system (geographic vs projected)

### 🗺️ **Layer Integration**
- Search layer names and titles
- Search within layer features and attributes
- Automatic zoom to search results with intelligent zoom levels
- Support for all vector layer types

### 🎯 **Smart Search Behavior**
- **Stop on First Result**: Optionally stop searching when first relevant result is found
- **Priority Ordering**: Configure which sources are searched first
- **Regex Validation**: Only search APIs when input matches specified patterns
- **Result Limits**: Control maximum results per provider
- **Interactive Results**: Click individual results to zoom to specific locations
- **Persistent Results**: Results stay visible for easy exploration of multiple results
- **Visual Feedback**: Loading indicators and search status updates

## Installation

1. Download or clone this repository to your QGIS plugins directory:
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

2. Rename the folder to `configurable_search`

3. Start QGIS and enable the plugin in the Plugin Manager

## Usage

### Basic Search
1. After installation, you'll see a search panel that can be docked anywhere in QGIS
2. Use the "Toggle Search Panel" toolbar button to show/hide the panel
3. Type your search term and press Enter
4. A loading indicator will appear showing search progress
5. A dropdown list will appear showing all matching results
6. Click on any result to zoom to that location
7. Results remain visible for easy exploration of multiple locations
4. Click any result in the list to zoom directly to that location
5. Close the results list using the "✕ Close" link or start a new search

### Results Interface
The search results appear in a dropdown list below the search box, showing:
- **Result name** and source provider
- **Hover tooltips** with detailed information (coordinates, bounds, etc.)
- **Visual feedback** during search (yellow background while searching)
- **Error indication** (red background if search fails)
- **Result count** in the header
- **One-click zoom** to any individual result
- **Smart zoom levels** adapted to coordinate system type

### Zoom Configuration
The plugin automatically detects your map's coordinate reference system (CRS) and applies appropriate zoom levels:
- **Geographic CRS** (like WGS84): Uses degree-based buffer (default: 0.001° ≈ 100m)
- **Projected CRS** (like UTM): Uses meter/feet-based buffer (default: 500 units)
- **Configurable**: Adjust zoom levels in General Settings to suit your needs

### Configuration
1. Click the configuration button in the toolbar or go to `Plugins > Configurable Search > Configure Search`
2. Configure your search providers in the **API Providers** tab
3. Adjust layer search settings in the **Layer Search** tab
4. Set general behavior in the **General Settings** tab

### Adding API Providers

#### Example: OpenStreetMap Nominatim
- **Name**: OpenStreetMap Nominatim
- **Type**: API
- **URL Template**: `https://nominatim.openstreetmap.org/search?q={search_term}&format=json&limit=5`
- **Result Parser**:
  - Name Field: `display_name`
  - Latitude Field: `lat`
  - Longitude Field: `lon`
  - Bounding Box Field: `boundingbox`

#### Example: Custom Geocoding Service
- **Name**: My Geocoder
- **Type**: API
- **URL Template**: `https://api.example.com/geocode?query={search_term}&key=YOUR_API_KEY`

### Using QGIS Authentication

The plugin supports QGIS Authentication Configurations for secure API access, which is the recommended approach for APIs requiring authentication.

#### Setting up Authentication:

1. **Create Authentication Configuration**:
   - Go to `Settings > Options > Authentication` in QGIS
   - Click `+` to add a new configuration
   - Choose the appropriate authentication method (Basic, OAuth2, API Key, etc.)
   - Configure your credentials and save with a meaningful name

2. **Configure API Provider with Authentication**:
   - In the plugin's API Providers tab, add or edit a provider
   - In the "HTTP Headers & Authentication" section:
     - Select your authentication configuration from the dropdown
     - Optionally add manual headers that will be merged with auth headers
   - The authentication will be applied automatically to all requests

#### Benefits of QGIS Authentication:
- **Secure**: Credentials are encrypted and stored securely by QGIS
- **Reusable**: Same auth config can be used across multiple plugins and data sources
- **Flexible**: Supports various authentication methods (Basic, Bearer tokens, OAuth2, etc.)
- **No hardcoding**: Avoid putting sensitive credentials in configuration files

#### Manual Headers vs Authentication:
- **Authentication Config**: Recommended for credentials and sensitive headers
- **Manual Headers**: Use for non-sensitive headers like `Content-Type`, `User-Agent`, etc.
- **Combined**: You can use both - auth config for credentials, manual headers for other needs
- **Headers**: `{"Authorization": "Bearer YOUR_TOKEN"}`
- **Result Parser**:
  - Name Field: `results.0.formatted_address`
  - Latitude Field: `results.0.geometry.location.lat`
  - Longitude Field: `results.0.geometry.location.lng`

#### Example: Coordinate Search
- **Name**: Coordinate Search
- **Type**: Coordinate
- **Regex Filter**: `^-?\d+\.?\d*\s*,\s*-?\d+\.?\d*$`
- **Stop on Result**: Yes

## Configuration Options

### API Providers
- **Name**: Display name for the provider
- **Type**: API, Coordinate, or Layer
- **Enabled**: Whether this provider is active
- **URL Template**: API endpoint with `{search_term}` placeholder
- **HTTP Method**: GET or POST
- **Headers**: JSON object with HTTP headers
- **Regex Filter**: Regular expression to validate search terms
- **Stop on Result**: Stop searching other providers when this one returns results
- **Result Parser**: Configure how to extract data from API responses

### Layer Search
- **Enable layer search**: Search through project layer names
- **Search within features**: Search layer feature attributes
- **Max features per layer**: Limit results per layer to improve performance

### General Settings
- **Stop on first result**: Stop all searching when any provider returns results
- **Max results per provider**: Limit results per API provider
- **Search timeout**: Maximum time to wait for API responses
- **Zoom levels**: Configure zoom buffer for geographic (degrees) and projected (meters/feet) coordinate systems

## URL Template Variables

Use these placeholders in your URL templates:
- `{search_term}`: The user's search input (URL-encoded)

## Result Parser Field Paths

Use dot notation to access nested JSON fields:
- `name` - Top-level field
- `results.0.name` - First item in results array
- `geometry.location.lat` - Nested object access

## Regex Examples

Common regex patterns for search validation:
- Coordinates: `^-?\d+\.?\d*\s*,\s*-?\d+\.?\d*$`
- Postal codes: `^\d{5}(-\d{4})?$`
- Phone numbers: `^\+?[\d\s\-\(\)]+$`
- Email addresses: `^[^\s@]+@[^\s@]+\.[^\s@]+$`

## Requirements

- QGIS 3.16 or higher
- Python 3.6+
- `requests` library (usually included with QGIS)

## Development

### Project Structure
```
configurable_search/
├── __init__.py                 # Plugin entry point
├── configurable_search.py      # Main plugin class
├── config_manager.py          # Configuration management
├── search_engine.py           # Search logic and API handling
├── configurable_search_dialog.py # Configuration dialog
├── resources.py               # Qt resources
├── resources.qrc             # Resource file
├── metadata.txt              # Plugin metadata
├── icon.svg                  # Plugin icon
└── README.md                 # This file
```

### Building Resources
To rebuild the resources file after modifying `resources.qrc`:
```bash
pyrcc5 -o resources.py resources.qrc
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This plugin is released under the GPL v3 license. See LICENSE file for details.

## Support

For issues, feature requests, or questions:
- Create an issue on GitHub
- Check the QGIS plugin documentation
- Visit the QGIS community forums

## Changelog

### Version 1.1.0
- **New**: Interactive results dropdown list
- **New**: Click individual results to zoom to specific locations
- **New**: Visual search feedback (colored search box during search)
- **New**: Detailed tooltips for each result showing coordinates and bounds
- **New**: Result count display
- **New**: Smart zoom levels adapted to coordinate system type
- **New**: Configurable zoom buffers for geographic and projected CRS
- **Improved**: Better user experience with non-blocking search results
- **Improved**: Enhanced result formatting and display
- **Fixed**: Zoom level now appropriate for different coordinate systems

### Version 1.0.0
- Initial release
- Multi-API search support
- Layer search integration
- Configurable search providers
- Regex filtering
- Custom result parsing
- Search prioritization
