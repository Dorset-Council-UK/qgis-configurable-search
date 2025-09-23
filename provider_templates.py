"""
Provider templates for common API services.
These templates provide pre-configured settings for popular geocoding and search APIs.
"""

PROVIDER_TEMPLATES = {
    "google_places": {
        "name": "Google Places API",
        "display_name": "Google Places API",
        "description": "Google Places API for location search",
        "provider_type": "api",
        "url_template": "https://places.googleapis.com/v1/places:searchText",
        "request_method": "POST",
        "post_body": '{\n  "textQuery": "{search_term}",\n  "maxResultCount": 10\n}',
        "headers": {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": "YOUR_API_KEY_HERE",
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.viewport"
        },
        "result_parser": {
            "results_path": "places",
            "name_field": "formattedAddress",
            "lat_field": "location.latitude",
            "lon_field": "location.longitude",
            "bbox_field": "{viewport.low.longitude},{viewport.low.latitude},{viewport.high.longitude},{viewport.high.latitude}"
        },
        "enabled": True,
        "regex_filter": "",
        "stop_on_result": False,
        "auth_config_id": "",
        "setup_instructions": [
            "1. Get an API key from Google Cloud Console",
            "2. Enable the Places API (New)",
            "3. Replace 'YOUR_API_KEY_HERE' in the headers with your actual API key",
            "4. Optionally customize the fields mask and max results"
        ]
    },
    
    "nominatim": {
        "name": "Nominatim (OpenStreetMap)",
        "display_name": "Nominatim (OpenStreetMap)",
        "description": "Free geocoding service using OpenStreetMap data",
        "provider_type": "api",
        "url_template": "https://nominatim.openstreetmap.org/search?q={search_term}&format=json&limit=10&addressdetails=1",
        "request_method": "GET",
        "post_body": "",
        "headers": {
            "User-Agent": "QGIS Advanced Search Panel"
        },
        "result_parser": {
            "results_path": "",  # Direct array response
            "name_field": "display_name",
            "lat_field": "lat",
            "lon_field": "lon",
            "bbox_field": "{boundingbox.2},{boundingbox.0},{boundingbox.3},{boundingbox.1}"
        },
        "enabled": True,
        "regex_filter": "",
        "stop_on_result": False,
        "auth_config_id": "",
        "setup_instructions": [
            "1. No API key required - ready to use!",
            "2. Optionally customize the User-Agent header",
            "3. Consider your usage - for heavy use, consider setting up your own Nominatim instance",
            "4. Respect the usage policy: max 1 request per second"
        ]
    },
    
    "mapbox_geocoding": {
        "name": "Mapbox Geocoding API",
        "display_name": "Mapbox Geocoding API", 
        "description": "Mapbox Search API for places and addresses",
        "provider_type": "api",
        "url_template": "https://api.mapbox.com/search/geocode/v6/forward?q={search_term}&access_token=YOUR_ACCESS_TOKEN_HERE",
        "request_method": "GET",
        "post_body": "",
        "headers": {},
        "result_parser": {
            "results_path": "features",
            "name_field": "place_formatted",
            "lat_field": "geometry.coordinates.1",
            "lon_field": "geometry.coordinates.0", 
            "bbox_field": "{bbox.0},{bbox.1},{bbox.2},{bbox.3}"
        },
        "enabled": True,
        "regex_filter": "",
        "stop_on_result": False,
        "auth_config_id": "",
        "setup_instructions": [
            "1. Sign up for a Mapbox account",
            "2. Get your access token from your account dashboard",
            "3. Replace 'YOUR_ACCESS_TOKEN_HERE' with your actual token",
            "4. Customize search types if needed (poi, address, etc.)"
        ]
    }
}

def get_template_names():
    """Get list of available template names for UI dropdown."""
    return list(PROVIDER_TEMPLATES.keys())

def get_template_display_names():
    """Get list of display names for UI dropdown."""
    return [template["display_name"] for template in PROVIDER_TEMPLATES.values()]

def get_template_by_name(template_name):
    """Get a specific template by its key name."""
    return PROVIDER_TEMPLATES.get(template_name, {}).copy()

def get_template_by_display_name(display_name):
    """Get a specific template by its display name."""
    for key, template in PROVIDER_TEMPLATES.items():
        if template.get("display_name") == display_name:
            return template.copy()
    return {}

def apply_template_to_provider(template_name, custom_name=None):
    """
    Apply a template to create a new provider configuration.
    
    Args:
        template_name: Key name of the template
        custom_name: Optional custom name for the provider instance
        
    Returns:
        dict: Provider configuration with template applied
    """
    template = get_template_by_name(template_name)
    if not template:
        return {}
    
    # Create a copy to avoid modifying the original template
    provider = template.copy()
    
    # Set custom name if provided
    if custom_name:
        provider["name"] = custom_name
    
    # Remove template-specific fields that shouldn't be in the final provider config
    provider.pop("display_name", None)
    provider.pop("description", None) 
    provider.pop("setup_instructions", None)
    
    return provider