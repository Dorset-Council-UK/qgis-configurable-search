# Configurable Search QGIS Plugin

A modern QGIS plugin that adds a powerful configurable search panel to QGIS. This plugin provides a dockable search interface that allows users to search through multiple APIs and project layers with customizable templates, ordering, and regex filtering.

## Features

### Multi-Source Search
- Search through multiple API endpoints simultaneously
- Search within project layers and their features
- Coordinate-based search with automatic detection
- Configurable search order and priority

### Advanced Configuration
- **API Providers**: Add custom API endpoints with URL templates
- **QGIS Authentication**: Use QGIS authentication configurations for secure API access
- **Regex Filtering**: Use regular expressions to determine search relevance
- **Custom Headers**: Support for manual headers alongside authentication
- **Result Parsing**: Configure how to extract location data from API responses
- **Search Behavior**: Control search stopping, timeouts, and result limits

## Installation

1. Download or clone this repository to your QGIS plugins directory:
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

2. Rename the folder to `configurable_search`

3. Start QGIS and enable the plugin in the Plugin Manager

## Usage

### Configuration
1. Click the configuration button in the toolbar or go to `Plugins > Configurable Search > Configure Search`
2. [Configure your search providers](#adding-api-providers) in the **API Providers** tab
3. Adjust layer search settings in the **Layer Search** tab
4. Set general behavior in the **General Settings** tab

### Basic Search
1. After installation, you'll see a search panel that can be docked anywhere in QGIS
2. Use the "Toggle Search Panel" toolbar button to show/hide the panel
3. Type your search term and press Enter
4. A dropdown list will appear showing all matching results
5. Click on any result to zoom to that location

### Zoom Configuration
The plugin automatically detects your map's coordinate reference system (CRS) and applies appropriate zoom levels:
- **Geographic CRS** (like WGS84): Uses degree-based buffer (default: 0.001° ≈ 100m)
- **Projected CRS** (like BNG): Uses meter/feet-based buffer (default: 500 units)
- **Configurable**: Adjust zoom levels in General Settings to suit your needs

### Adding API Providers

Nominatim, Google and Mapbox searches are available as pre-configured templates (bring your own API key for Google and Mapbox) and can be customised. Alternatively, configure any JSON compatible provider using the configuration options.

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

## Configuration Backup and Sharing

The plugin supports exporting and importing provider configurations, making it easy to backup your settings and share configurations with colleagues.

### Exporting Configurations

1. **Open Settings**: Click the settings/configuration button in the search panel
2. **Navigate to Providers**: Go to the "Search Providers" tab
3. **Export**: Click the "Export..." button
4. **Choose Location**: Select where to save the JSON export file
5. **Save**: The file will include all search providers and plugin settings

### Importing Configurations

1. **Open Settings**: Click the settings/configuration button in the search panel
2. **Navigate to Providers**: Go to the "Search Providers" tab  
3. **Import**: Click the "Import..." button
4. **Choose Import Mode**:
   - **Replace All**: Remove existing providers and replace with imported ones
   - **Merge**: Add imported providers alongside existing ones (skips duplicates)
5. **Select File**: Choose the JSON export file to import
6. **Apply**: New providers will appear in your configuration

### Export File Structure

The export creates a comprehensive JSON file containing:

- **Export Metadata**: Plugin version, export date, and provider count
- **Search Providers**: Complete provider configurations including:
  - URL templates and request methods
  - Authentication headers and API keys
  - Result parsing rules and field mappings
  - Regular expression filters
  - Priority settings and enable/disable state
- **Plugin Settings**: General preferences like timeouts and zoom behavior

### Use Cases

- **Team Collaboration**: Share standardized API configurations across teams
- **Backup**: Save configurations before making major changes
- **Migration**: Transfer settings between QGIS installations or computers
- **Templates**: Create organization-wide standard configurations
- **Testing**: Quickly switch between different API provider setups

### Example Export

See `example_export.json` in the plugin directory for a sample export file format that includes common providers like OpenStreetMap Nominatim and Google Places API.

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

## Contributing

Our preferred means of receiving contributions is through [pull requests](https://help.github.com/articles/using-pull-requests). Make sure
that your pull request follows our pull request guidelines below before submitting it.

Before starting work on a feature or issue, make sure you let us know by adding a comment to the relevant issue in the issue tracker.

If you are looking to build new functionality or change something quite significantly, please check with the core developers before starting work to make sure 
it is something we are happy for you to do.

## License

This plugin is released under the MIT license. See LICENSE file for details.


