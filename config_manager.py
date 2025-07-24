import json
import os
from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsProject


class ConfigManager:
    """Manages plugin configuration and settings."""
    
    def __init__(self):
        self.settings = QSettings()
        self.plugin_key = "configurable_search"
        self.default_config = {
            "search_providers": [],
            "stop_on_first_result": False,
            "max_results_per_provider": 10,
            "search_timeout": 30,
            "include_project_layers": True,
            "zoom_buffer_geographic": 0.001,  # Buffer for geographic CRS (degrees)
            "zoom_buffer_projected": 500      # Buffer for projected CRS (meters/feet)
        }
        
    def get_config(self):
        """Get the complete configuration."""
        config_str = self.settings.value(f"{self.plugin_key}/config", "")
        if config_str:
            try:
                return json.loads(config_str)
            except (json.JSONDecodeError, TypeError):
                pass
        return self.default_config.copy()
    
    def save_config(self, config):
        """Save the complete configuration."""
        config_str = json.dumps(config, indent=2)
        self.settings.setValue(f"{self.plugin_key}/config", config_str)
        
    def get_search_providers(self):
        """Get the list of search providers."""
        config = self.get_config()
        return config.get("search_providers", [])
    
    def save_search_providers(self, providers):
        """Save the list of search providers."""
        config = self.get_config()
        config["search_providers"] = providers
        self.save_config(config)
        
    def get_setting(self, key, default=None):
        """Get a specific setting."""
        config = self.get_config()
        return config.get(key, default)
    
    def set_setting(self, key, value):
        """Set a specific setting."""
        config = self.get_config()
        config[key] = value
        self.save_config(config)
        
    def get_project_layers_config(self):
        """Get configuration for project layer searching."""
        return {
            "enabled": self.get_setting("include_project_layers", True),
            "search_fields": self.get_setting("layer_search_fields", ["name", "title"]),
            "feature_search_enabled": self.get_setting("feature_search_enabled", True),
            "max_features_per_layer": self.get_setting("max_features_per_layer", 50)
        }
        
    def create_default_providers(self):
        """Create some default search providers as examples."""
        default_providers = [
            {
                "name": "OpenStreetMap Nominatim",
                "url_template": "https://nominatim.openstreetmap.org/search?q={search_term}&format=json&limit=5",
                "enabled": True,
                "priority": 1,
                "regex_filter": "",
                "stop_on_result": False,
                "provider_type": "api",
                "request_method": "GET",
                "headers": {},
                "result_parser": {
                    "format": "json",
                    "name_field": "display_name",
                    "lat_field": "lat",
                    "lon_field": "lon",
                    "bbox_field": "boundingbox"
                }
            },
            {
                "name": "Coordinate Search",
                "url_template": "",
                "enabled": True,
                "priority": 2,
                "regex_filter": r"^-?\d+\.?\d*\s*,\s*-?\d+\.?\d*$",
                "stop_on_result": True,
                "provider_type": "coordinate",
                "request_method": "GET",
                "headers": {},
                "result_parser": {}
            }
        ]
        
        current_providers = self.get_search_providers()
        if not current_providers:
            self.save_search_providers(default_providers)
