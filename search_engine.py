import re
import json
import requests
from qgis.PyQt.QtCore import QThread, pyqtSignal, QObject, QVariant
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeatureRequest, QgsGeometry, 
    QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsRectangle, QgsMessageLog, Qgis, QgsApplication, QgsNetworkAccessManager,
    QgsExpression
)
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QUrl, QEventLoop


class SearchEngine(QObject):
    """Main search engine that coordinates searches across providers."""
    
    # Signals
    search_started = pyqtSignal(str)
    search_completed = pyqtSignal(list)
    search_error = pyqtSignal(str)
    provider_search_started = pyqtSignal(str, str)  # provider_name, search_term
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.active_searches = []
        
    def refresh_config(self):
        """Refresh configuration from config manager."""
        # Create default providers if none exist
        self.config_manager.create_default_providers()
        
    def search(self, search_term, iface):
        """Perform search with the given term."""
        if not search_term.strip():
            return
            
        print(f"DEBUG: Starting search for term: {search_term}")
        self.search_started.emit(search_term)
        
        # Force UI update to show loading message before starting search
        from qgis.PyQt.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Get configuration
        providers = self.config_manager.get_search_providers()
        stop_on_first = self.config_manager.get_setting("stop_on_first_result", False)
        
        # Sort providers by priority
        providers = sorted([p for p in providers if p.get("enabled", True)], 
                         key=lambda x: x.get("priority", 999))
        
        results = []
        search_stopped = False
        
        print(f"DEBUG: Found {len(providers)} enabled providers")
        
        # Search through providers in priority order
        # Two ways to stop searching:
        # 1. Individual provider has "stop_on_result" enabled and returns results
        # 2. Global "stop_on_first_result" setting is enabled and any provider returns results
        for provider in providers:
            provider_name = provider.get("name", "Unknown")
            print(f"DEBUG: Starting search for provider: {provider_name}")
            
            # Emit provider-specific signal
            self.provider_search_started.emit(provider_name, search_term)
            QApplication.processEvents()
            
            provider_results = self._search_provider(provider, search_term, iface)
            print(f"DEBUG: Provider {provider_name} returned {len(provider_results) if provider_results else 0} results")
            
            if provider_results:
                results.extend(provider_results)
                # Stop if this provider has "stop on result" enabled and returned results
                if provider.get("stop_on_result", False):
                    search_stopped = True
                    break
                # Or stop if global "stop on first result" is enabled and we got any results
                if stop_on_first:
                    search_stopped = True
                    break
            
        # Process results
        print(f"DEBUG: Processing {len(results)} total results")
        self._process_results(results, iface)
        self.search_completed.emit(results)
        
    def _search_provider(self, provider, search_term, iface):
        """Search a specific provider."""
        try:
            provider_type = provider.get("provider_type", "api")
            
            # Check regex filter
            regex_filter = provider.get("regex_filter", "")
            if regex_filter:
                if not re.match(regex_filter, search_term):
                    return []
                    
            if provider_type == "coordinate":
                return self._search_coordinates(search_term, provider, iface)
            elif provider_type == "api":
                return self._search_api(provider, search_term)
            elif provider_type == "layer":
                return self._search_layer(provider, search_term, iface)
                
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error searching provider {provider.get('name', 'Unknown')}: {str(e)}", 
                "Advanced Search Panel", 
                Qgis.Warning
            )
            
        return []
        
    def _search_coordinates(self, search_term, provider, iface=None):
        """Enhanced coordinate search supporting current map CRS and multiple formats."""
        if not iface:
            # Fallback to simple lat/lon parsing if no iface provided
            return self._search_coordinates_simple(search_term, provider)
        
        canvas = iface.mapCanvas()
        current_crs = canvas.mapSettings().destinationCrs()
        
        # Parse coordinates from the search term
        coords = self._parse_coordinates(search_term)
        if not coords:
            return []
        
        x, y = coords
        
        # Detect the coordinate system based on values and current map CRS
        source_crs = self._detect_coordinate_system(x, y, current_crs, search_term)
        if not source_crs or not source_crs.isValid():
            return []
        
        # Transform to map CRS if needed
        if source_crs != current_crs:
            transform = QgsCoordinateTransform(source_crs, current_crs, QgsProject.instance())
            try:
                map_point = transform.transform(QgsPointXY(x, y))
                map_x, map_y = map_point.x(), map_point.y()
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"Coordinate transformation failed: {str(e)}", 
                    "Advanced Search Panel", 
                    Qgis.Warning
                )
                return []
        else:
            map_x, map_y = x, y
        
        # Create result with appropriate display format
        if source_crs.isGeographic():
            # For geographic coordinates, show as lat, lon
            display_coords = f"{y:.6f}, {x:.6f}"
            coord_type = "Geographic"
        else:
            # For projected coordinates, show as x, y
            display_coords = f"{x:.2f}, {y:.2f}"
            coord_type = "Projected"
        
        # Get CRS description
        crs_desc = source_crs.description() or source_crs.authid()
        
        return [{
            "name": f"{coord_type}: {display_coords} ({crs_desc})",
            "provider": provider.get("name", "Coordinate Search"),
            "type": "coordinate",
            "geometry": {
                "x": map_x,
                "y": map_y,
                "crs": current_crs.authid()
            },
            "data": {
                "original_x": x,
                "original_y": y,
                "original_crs": source_crs.authid(),
                "map_x": map_x,
                "map_y": map_y,
                "map_crs": current_crs.authid(),
                "search_term": search_term,
                "source_crs_description": crs_desc
            }
        }]
    
    def _search_coordinates_simple(self, search_term, provider):
        """Simple coordinate search for lat/lon (fallback method)."""
        # Match coordinate patterns like: "lat, lon" or "lat,lon"
        coord_pattern = r'^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$'
        match = re.match(coord_pattern, search_term.strip())
        
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            return [{
                "name": f"Coordinates: {lat}, {lon}",
                "provider": provider.get("name", "Coordinate Search"),
                "type": "coordinate",
                "geometry": {
                    "lat": lat,
                    "lon": lon
                },
                "data": {
                    "lat": lat,
                    "lon": lon,
                    "search_term": search_term
                }
            }]
        return []
    
    def _parse_coordinates(self, coord_text):
        """Parse coordinates from various formats and separators."""
        # Remove any extra whitespace and handle explicit CRS specification
        clean_text = coord_text.strip()
        
        # Check for explicit CRS specification: "EPSG:3857: 583960, 4507523"
        crs_pattern = r'^(EPSG:\d+|CRS:\d+)\s*:\s*(.+)$'
        match = re.match(crs_pattern, clean_text, re.IGNORECASE)
        if match:
            # Extract coordinates part only, store CRS info for later use
            clean_text = match.group(2).strip()
            self._explicit_crs = match.group(1).upper()
        else:
            self._explicit_crs = None
        
        # Try different separators: comma, space, tab, semicolon
        separators = [',', ' ', '\t', ';']
        
        for sep in separators:
            if sep in clean_text:
                parts = [p.strip() for p in clean_text.split(sep) if p.strip()]
                if len(parts) == 2:
                    try:
                        x = float(parts[0])
                        y = float(parts[1])
                        return x, y
                    except ValueError:
                        continue
        
        # Try space-separated without explicit separator
        parts = clean_text.split()
        if len(parts) == 2:
            try:
                x = float(parts[0])
                y = float(parts[1])
                return x, y
            except ValueError:
                pass
        
        return None
    
    def _detect_coordinate_system(self, x, y, current_crs, search_term):
        """Detect what coordinate system the input coordinates are in."""
        # Check if CRS was explicitly specified
        if hasattr(self, '_explicit_crs') and self._explicit_crs:
            return QgsCoordinateReferenceSystem(self._explicit_crs)
        
        # Auto-detect based on coordinate values and current CRS
        
        # If current CRS is geographic and values look like lat/lon
        if current_crs.isGeographic():
            if -180 <= x <= 180 and -90 <= y <= 90:
                return current_crs
        
        # If current CRS is projected and values are large (not lat/lon)
        elif not current_crs.isGeographic():
            if abs(x) > 180 or abs(y) > 90:  # Too large for lat/lon
                return current_crs
        
        # Fallback: assume WGS84 if it looks like lat/lon
        if -180 <= x <= 180 and -90 <= y <= 90:
            return QgsCoordinateReferenceSystem("EPSG:4326")
        
        # If coordinates are too large for lat/lon but current CRS is geographic,
        # we can't auto-detect - return None to indicate failure
        return None
        
    def _search_api(self, provider, search_term):
        """Search using an API provider."""
        url_template = provider.get("url_template", "")
        if not url_template:
            return []
            
        # Replace placeholder with search term
        url = url_template.replace("{search_term}", requests.utils.quote(search_term))
        
        # Process POST body template if provided
        post_body_template = provider.get("post_body", "")
        post_body = ""
        if post_body_template:
            # For POST body, don't URL-encode the search term since it will be in JSON/XML
            post_body = post_body_template.replace("{search_term}", search_term)
        
        try:
            # Check if authentication configuration is specified
            auth_config_id = provider.get("auth_config_id", "")
            
            if auth_config_id:
                # Use QGIS authentication system
                response_data = self._make_authenticated_request(url, provider, auth_config_id, post_body)
            else:
                # Use regular requests with manual headers
                response_data = self._make_regular_request(url, provider, post_body)
                
            if response_data:
                return self._parse_api_results(response_data, provider, search_term)
                
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error parsing response from {provider.get('name', 'API')}: {str(e)}", 
                "Advanced Search Panel", 
                Qgis.Warning
            )
            
        return []
        
    def _make_authenticated_request(self, url, provider, auth_config_id, post_body=""):
        """Make an authenticated request using QGIS authentication system."""
        try:
            # Get QGIS network access manager
            nam = QgsNetworkAccessManager.instance()
            
            # Create network request
            request = QNetworkRequest(QUrl(url))
            
            # Apply authentication
            auth_manager = QgsApplication.authManager()
            if not auth_manager.updateNetworkRequest(request, auth_config_id):
                QgsMessageLog.logMessage(
                    f"Failed to apply authentication config {auth_config_id}", 
                    "Advanced Search Panel", 
                    Qgis.Warning
                )
                return None
            
            # Add manual headers if any (they will be merged with auth headers)
            manual_headers = provider.get("headers", {})
            for key, value in manual_headers.items():
                request.setRawHeader(key.encode(), str(value).encode())
            
            # Set timeout
            timeout = self.config_manager.get_setting("search_timeout", 30) * 1000  # Convert to ms
            
            # Make request based on method
            method = provider.get("request_method", "GET").upper()
            if method == "GET":
                reply = nam.get(request)
            elif method == "POST":
                # Use POST body if provided, otherwise empty
                post_data = post_body.encode('utf-8') if post_body else b""
                reply = nam.post(request, post_data)
            else:
                QgsMessageLog.logMessage(
                    f"Unsupported HTTP method for authenticated requests: {method}", 
                    "Advanced Search Panel", 
                    Qgis.Warning
                )
                return None
            
            # Wait for response
            loop = QEventLoop()
            reply.finished.connect(loop.quit)
            loop.exec_()
            
            # Check for errors
            if reply.error() != QNetworkReply.NoError:
                QgsMessageLog.logMessage(
                    f"Network error for {provider.get('name', 'API')}: {reply.errorString()}", 
                    "Advanced Search Panel", 
                    Qgis.Warning
                )
                reply.deleteLater()
                return None
            
            # Read response
            response_data = reply.readAll().data().decode('utf-8')
            reply.deleteLater()
            
            # Parse JSON response
            return json.loads(response_data)
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error in authenticated request for {provider.get('name', 'API')}: {str(e)}", 
                "Advanced Search Panel", 
                Qgis.Warning
            )
            return None
    
    def _make_regular_request(self, url, provider, post_body=""):
        """Make a regular request using the requests library."""
        try:
            # Make request
            headers = provider.get("headers", {})
            method = provider.get("request_method", "GET").upper()
            timeout = self.config_manager.get_setting("search_timeout", 30)
            QgsMessageLog.logMessage(
                    f"Making request to {url}", 
                    "Advanced Search Panel", 
                    Qgis.Info
                )
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                # Use POST body if provided
                data = post_body.encode('utf-8') if post_body else None
                response = requests.post(url, headers=headers, data=data, timeout=timeout)
            else:
                QgsMessageLog.logMessage(
                    f"Unsupported HTTP method: {method}", 
                    "Advanced Search Panel", 
                    Qgis.Warning
                )
                return None
                
            response.raise_for_status()
            
            QgsMessageLog.logMessage(
                f"{response.status_code} response from {provider.get('name', 'API')}", 
                "Advanced Search Panel", 
                Qgis.Warning
            )

            QgsMessageLog.logMessage(
                f"{response.content}", 
                "Advanced Search Panel", 
                Qgis.Warning
            )

            # Parse response
            content_type = response.headers.get('content-type', '')
            if (content_type.startswith('application/json') or 
                content_type.startswith('application/vnd.geo+json')):
                return response.json()
            else:
                QgsMessageLog.logMessage(
                    f"Non-JSON response from {provider.get('name', 'API')}: {content_type}", 
                    "Advanced Search Panel", 
                    Qgis.Warning
                )
                return None
                
        except requests.RequestException as e:
            QgsMessageLog.logMessage(
                f"Request error for {provider.get('name', 'API')}: {str(e)}", 
                "Advanced Search Panel", 
                Qgis.Warning
            )
            return None
        
    def _parse_api_results(self, data, provider, search_term):
        """Parse API results based on provider configuration."""
        results = []
        parser = provider.get("result_parser", {})
        
        # Get the results array using configurable path
        items = self._extract_results_array(data, parser)
        
        if not isinstance(items, list):
            items = [items] if items else []
            
        max_results = self.config_manager.get_setting("max_results_per_provider", 10)
        
        for item in items[:max_results]:
            if not isinstance(item, dict):
                continue
                
            # Extract fields based on parser configuration
            name = self._extract_field(item, parser.get("name_field", "name"))
            lat = self._extract_field(item, parser.get("lat_field", "lat"))
            lon = self._extract_field(item, parser.get("lon_field", "lon"))
            bbox = self._extract_bbox(item, parser.get("bbox_field", "bbox"))
            
            if name:
                result = {
                    "name": str(name),
                    "provider": provider.get("name", "API"),
                    "type": "api_result",
                    "data": item,
                    "search_term": search_term
                }
                
                # Add geometry if coordinates are available
                if lat is not None and lon is not None:
                    try:
                        result["geometry"] = {
                            "lat": float(lat),
                            "lon": float(lon)
                        }
                    except (ValueError, TypeError):
                        pass
                        
                # Add bounding box if available
                if bbox:
                    try:
                        if isinstance(bbox, list) and len(bbox) >= 4:
                            result["bbox"] = [float(x) for x in bbox[:4]]
                    except (ValueError, TypeError):
                        pass
                        
                results.append(result)
                
        return results
        
    def _extract_results_array(self, data, parser):
        """Extract the results array using configurable path or fallback logic."""
        # Check if a custom results path is specified
        results_path = parser.get("results_path", "")
        
        if results_path:
            # Use the specified path to extract results array
            return self._extract_field(data, results_path)
        else:
            # Fallback to automatic detection
            items = data
            if isinstance(data, dict):
                # Look for common array keys
                for key in ["results", "features", "items", "data", "places"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break
            return items
        
    def _extract_field(self, data, field_path):
        """Extract a field from nested data using dot notation with array index support."""
        if not field_path or not data:
            return None
            
        parts = field_path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                # Handle array indexing
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
                
        return current
        
    def _extract_bbox(self, data, bbox_config):
        """Extract bounding box using either field name or template with placeholders.
        
        Always returns bbox in format: [west, south, east, north] (standard GIS format)
        Template format should be: {west},{south},{east},{north}
        """
        if not bbox_config or not data:
            return None
            
        # Check if it's a template (contains curly braces)
        if '{' in bbox_config and '}' in bbox_config:
            # Template approach: extract values and create bbox array
            try:
                # Split by comma and extract field names from placeholders
                template_parts = bbox_config.split(',')
                bbox_values = []
                
                for part in template_parts:
                    part = part.strip()
                    if part.startswith('{') and part.endswith('}'):
                        # Extract field name from {fieldName}
                        field_name = part[1:-1].strip()
                        value = self._extract_field(data, field_name)
                        if value is not None:
                            bbox_values.append(float(value))
                        else:
                            return None  # Missing required field
                    else:
                        # Direct value (though this would be unusual)
                        try:
                            bbox_values.append(float(part))
                        except ValueError:
                            return None
                            
                # Return as array if we have 4 values
                # Template is expected to be in format: {west},{south},{east},{north}
                if len(bbox_values) == 4:
                    return bbox_values  # Already in [west, south, east, north] format
                else:
                    return None
                    
            except (ValueError, TypeError):
                return None
        else:
            # Single field approach - assume standard [west, south, east, north] format
            raw_bbox = self._extract_field(data, bbox_config)
            if raw_bbox and isinstance(raw_bbox, list) and len(raw_bbox) >= 4:
                # Assume bbox is already in standard [west, south, east, north] format
                return [float(x) for x in raw_bbox[:4]]
            return raw_bbox
        
    def _search_layer_features(self, layer, search_term, provider):
        """Search features within a layer using efficient QGIS expressions."""
        results = []
        max_features = 50  # Default max features
        
        print(f"DEBUG: Starting layer search in {layer.name()}")
        QgsMessageLog.logMessage(
            f"Searching layer {layer.name()} with optimized expression", 
            "Advanced Search Panel", 
            Qgis.Info
        )
        
        # Force UI update to ensure loading message is visible
        QApplication.processEvents()
        
        try:
            # Get search configuration from provider
            search_fields = provider.get("search_fields", "").strip()
            search_mode = provider.get("search_mode", "wildcard")
            
            print(f"DEBUG: Search fields: {search_fields}, Search mode: {search_mode}")
            
            # Determine which fields to search
            if search_fields:
                # Use specified fields
                field_names = [field.strip() for field in search_fields.split(",") if field.strip()]
                # Validate that fields exist in layer
                layer_field_names = [field.name() for field in layer.fields()]
                field_names = [name for name in field_names if name in layer_field_names]
            else:
                # Use all string/text fields
                field_names = []
                for field in layer.fields():
                    if field.type() in (QVariant.String, QVariant.Char):
                        field_names.append(field.name())
            
            if not field_names:
                QgsMessageLog.logMessage(
                    f"No searchable fields found in layer {layer.name()}", 
                    "Advanced Search Panel", 
                    Qgis.Warning
                )
                return results
            
            print(f"DEBUG: Searching fields: {field_names}")
            
            # Build search expression based on mode
            expression_parts = []
            escaped_search_term = search_term.replace("'", "''")  # Escape single quotes
            
            if search_mode == "exact":
                # Exact match (case insensitive)
                for field_name in field_names:
                    expression_parts.append(f'upper("{field_name}") = upper(\'{escaped_search_term}\')')
            else:
                # Wildcard/contains match (case insensitive)
                for field_name in field_names:
                    expression_parts.append(f'"{field_name}" ILIKE \'%{escaped_search_term}%\'')
            
            # Combine expressions with OR
            if expression_parts:
                filter_expression = ' OR '.join(expression_parts)
                
                QgsMessageLog.logMessage(
                    f"Using expression: {filter_expression}", 
                    "Advanced Search Panel", 
                    Qgis.Info
                )
                
                # Create feature request with expression filter
                request = QgsFeatureRequest()
                request.setFilterExpression(filter_expression)
                request.setLimit(max_features)
                
                # Execute the filtered query
                features = layer.getFeatures(request)
                count = 0
                
                for feature in features:
                    if count >= max_features:
                        break
                    
                    # Find which field matched for display purposes
                    matched_field = None
                    matched_value = None
                    
                    for field_name in field_names:
                        field_value = feature[field_name]
                        if field_value and isinstance(field_value, str):
                            if search_mode == "exact":
                                if field_value.lower() == search_term.lower():
                                    matched_field = field_name
                                    matched_value = field_value
                                    break
                            else:
                                if search_term.lower() in field_value.lower():
                                    matched_field = field_name
                                    matched_value = field_value
                                    break
                    
                    if matched_field and matched_value:
                        results.append({
                            "name": f"Feature: {matched_value[:50]}{'...' if len(str(matched_value)) > 50 else ''}",
                            "provider": f"Layer: {layer.name()}",
                            "type": "feature",
                            "geometry": feature.geometry(),
                            "data": {
                                "layer_id": layer.id(),
                                "layer_name": layer.name(),
                                "feature_id": feature.id(),
                                "attributes": feature.attributes(),
                                "search_term": search_term,
                                "matched_field": matched_field,
                                "matched_value": matched_value,
                                "search_mode": search_mode,
                                "search_fields": field_names
                            }
                        })
                        count += 1
                
                QgsMessageLog.logMessage(
                    f"Found {count} matching features in layer {layer.name()}", 
                    "Advanced Search Panel", 
                    Qgis.Info
                )
                print(f"DEBUG: Layer search completed, returning {count} results")
                
        except Exception as e:
            error_msg = f"Error searching features in layer {layer.name()}: {str(e)}"
            print(f"DEBUG: Layer search error: {error_msg}")
            QgsMessageLog.logMessage(
                error_msg, 
                "Advanced Search Panel", 
                Qgis.Warning
            )
            
        return results
        
    def _search_layer(self, provider, search_term, iface):
        """Search a specific layer provider."""
        layer_id = provider.get("layer_id")
        if not layer_id:
            QgsMessageLog.logMessage(
                f"Layer provider '{provider.get('name', 'Unknown')}' has no layer_id configured", 
                "Advanced Search Panel", 
                Qgis.Warning
            )
            return []
            
        project = QgsProject.instance()
        layer = project.mapLayer(layer_id)
        
        if not layer:
            QgsMessageLog.logMessage(
                f"Layer provider '{provider.get('name', 'Unknown')}' references layer ID '{layer_id}' which doesn't exist in current project", 
                "Advanced Search Panel", 
                Qgis.Warning
            )
            return []
            
        if not isinstance(layer, QgsVectorLayer):
            QgsMessageLog.logMessage(
                f"Layer provider '{provider.get('name', 'Unknown')}' references layer '{layer.name()}' which is not a vector layer", 
                "Advanced Search Panel", 
                Qgis.Warning
            )
            return []
            
        return self._search_layer_features(
            layer, 
            search_term, 
            provider  # Pass the full provider configuration
        )
        
    def validate_layer_providers(self):
        """Validate that all layer providers reference existing layers.
        
        Returns:
            list: List of validation warnings for missing/invalid layers
        """
        warnings = []
        providers = self.config_manager.get_search_providers()
        project = QgsProject.instance()
        
        for provider in providers:
            if provider.get("provider_type") == "layer" and provider.get("enabled", True):
                layer_id = provider.get("layer_id")
                provider_name = provider.get("name", "Unknown")
                
                if not layer_id:
                    warnings.append(f"Layer provider '{provider_name}' has no layer configured")
                    continue
                    
                layer = project.mapLayer(layer_id)
                if not layer:
                    warnings.append(f"Layer provider '{provider_name}' references missing layer (ID: {layer_id})")
                elif not isinstance(layer, QgsVectorLayer):
                    warnings.append(f"Layer provider '{provider_name}' references non-vector layer '{layer.name()}'")
                    
        return warnings
        
    def _process_results(self, results, iface):
        """Process search results without automatic zooming."""
        if not results:
            QgsMessageLog.logMessage(
                "No search results found", 
                "Advanced Search Panel", 
                Qgis.Info
            )
        else:
            # Log results
            QgsMessageLog.logMessage(
                f"Found {len(results)} search results", 
                "Advanced Search Panel", 
                Qgis.Info
            )
        
        # Results are now handled by the SearchWidget's results list
