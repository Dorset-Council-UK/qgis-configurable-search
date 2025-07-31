import re
import json
import requests
from qgis.PyQt.QtCore import QThread, pyqtSignal, QObject
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeatureRequest, QgsGeometry, 
    QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsRectangle, QgsMessageLog, Qgis, QgsApplication, QgsNetworkAccessManager
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
            
        self.search_started.emit(search_term)
        
        # Get configuration
        providers = self.config_manager.get_search_providers()
        stop_on_first = self.config_manager.get_setting("stop_on_first_result", False)
        
        # Sort providers by priority
        providers = sorted([p for p in providers if p.get("enabled", True)], 
                         key=lambda x: x.get("priority", 999))
        
        results = []
        search_stopped = False
        
        # Search through providers in priority order
        # Two ways to stop searching:
        # 1. Individual provider has "stop_on_result" enabled and returns results
        # 2. Global "stop_on_first_result" setting is enabled and any provider returns results
        for provider in providers:
            provider_results = self._search_provider(provider, search_term, iface)
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
                return self._search_coordinates(search_term, provider)
            elif provider_type == "api":
                return self._search_api(provider, search_term)
            elif provider_type == "layer":
                return self._search_layer(provider, search_term, iface)
                
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error searching provider {provider.get('name', 'Unknown')}: {str(e)}", 
                "Configurable Search", 
                Qgis.Warning
            )
            
        return []
        
    def _search_coordinates(self, search_term, provider):
        """Search for coordinates in the search term."""
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
        
    def _search_api(self, provider, search_term):
        """Search using an API provider."""
        url_template = provider.get("url_template", "")
        if not url_template:
            return []
            
        # Replace placeholder with search term
        url = url_template.replace("{search_term}", requests.utils.quote(search_term))
        
        try:
            # Check if authentication configuration is specified
            auth_config_id = provider.get("auth_config_id", "")
            
            if auth_config_id:
                # Use QGIS authentication system
                response_data = self._make_authenticated_request(url, provider, auth_config_id)
            else:
                # Use regular requests with manual headers
                response_data = self._make_regular_request(url, provider)
                
            if response_data:
                return self._parse_api_results(response_data, provider, search_term)
                
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error parsing response from {provider.get('name', 'API')}: {str(e)}", 
                "Configurable Search", 
                Qgis.Warning
            )
            
        return []
        
    def _make_authenticated_request(self, url, provider, auth_config_id):
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
                    "Configurable Search", 
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
                reply = nam.post(request, b"")  # Empty POST data for now
            else:
                QgsMessageLog.logMessage(
                    f"Unsupported HTTP method for authenticated requests: {method}", 
                    "Configurable Search", 
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
                    "Configurable Search", 
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
                "Configurable Search", 
                Qgis.Warning
            )
            return None
    
    def _make_regular_request(self, url, provider):
        """Make a regular request using the requests library."""
        try:
            # Make request
            headers = provider.get("headers", {})
            method = provider.get("request_method", "GET").upper()
            timeout = self.config_manager.get_setting("search_timeout", 30)
            QgsMessageLog.logMessage(
                    f"Making request to {url}", 
                    "Configurable Search", 
                    Qgis.Info
                )
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, headers=headers, timeout=timeout)
            else:
                QgsMessageLog.logMessage(
                    f"Unsupported HTTP method: {method}", 
                    "Configurable Search", 
                    Qgis.Warning
                )
                return None
                
            response.raise_for_status()
            
            # Parse response
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                QgsMessageLog.logMessage(
                    f"Non-JSON response from {provider.get('name', 'API')}", 
                    "Configurable Search", 
                    Qgis.Warning
                )
                return None
                
        except requests.RequestException as e:
            QgsMessageLog.logMessage(
                f"Request error for {provider.get('name', 'API')}: {str(e)}", 
                "Configurable Search", 
                Qgis.Warning
            )
            return None
        
    def _parse_api_results(self, data, provider, search_term):
        """Parse API results based on provider configuration."""
        results = []
        parser = provider.get("result_parser", {})
        
        # Handle different data structures
        items = data
        if isinstance(data, dict):
            # Look for common array keys
            for key in ["results", "features", "items", "data"]:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
                    
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
        
    def _search_layer_features(self, layer, search_term, config):
        """Search features within a layer."""
        results = []
        max_features = config.get("max_features_per_layer", 50)
        
        try:
            # Build feature request with text search
            request = QgsFeatureRequest()
            request.setLimit(max_features)
            
            # Search in all string fields
            features = layer.getFeatures(request)
            count = 0
            
            for feature in features:
                if count >= max_features:
                    break
                    
                # Check if any attribute contains the search term
                for field_name in layer.fields().names():
                    field_value = feature[field_name]
                    if field_value and isinstance(field_value, str):
                        if search_term.lower() in field_value.lower():
                            results.append({
                                "name": f"Feature: {field_value[:50]}{'...' if len(str(field_value)) > 50 else ''}",
                                "provider": f"Layer: {layer.name()}",
                                "type": "feature",
                                "geometry": feature.geometry(),
                                "data": {
                                    "layer_id": layer.id(),
                                    "layer_name": layer.name(),
                                    "feature_id": feature.id(),
                                    "attributes": feature.attributes(),
                                    "search_term": search_term,
                                    "matched_field": field_name,
                                    "matched_value": field_value
                                }
                            })
                            count += 1
                            break
                            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error searching features in layer {layer.name()}: {str(e)}", 
                "Configurable Search", 
                Qgis.Warning
            )
            
        return results
        
    def _search_layer(self, provider, search_term, iface):
        """Search a specific layer provider."""
        layer_id = provider.get("layer_id")
        if not layer_id:
            return []
            
        project = QgsProject.instance()
        layer = project.mapLayer(layer_id)
        
        if not layer or not isinstance(layer, QgsVectorLayer):
            return []
            
        return self._search_layer_features(
            layer, 
            search_term, 
            {"max_features_per_layer": 50}  # Simple default config
        )
        
    def _process_results(self, results, iface):
        """Process search results without automatic zooming."""
        if not results:
            QgsMessageLog.logMessage(
                "No search results found", 
                "Configurable Search", 
                Qgis.Info
            )
        else:
            # Log results
            QgsMessageLog.logMessage(
                f"Found {len(results)} search results", 
                "Configurable Search", 
                Qgis.Info
            )
        
        # Results are now handled by the SearchWidget's results list
        
    def _zoom_to_result(self, result, iface):
        """Zoom to a search result."""
        try:
            canvas = iface.mapCanvas()
            
            if "bbox" in result:
                # Use bounding box if available
                # Expected bbox format: [west, south, east, north] in WGS84
                bbox = result["bbox"]
                if len(bbox) >= 4:
                    rect = QgsRectangle(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
                    
                    # Transform bbox if needed
                    source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
                    dest_crs = canvas.mapSettings().destinationCrs()
                    
                    if source_crs != dest_crs:
                        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
                        rect = transform.transformBoundingBox(rect)
                    
                    canvas.setExtent(rect)
                    canvas.refresh()
                    return
                    
            if "geometry" in result and "lat" in result["geometry"] and "lon" in result["geometry"]:
                # Use point coordinates
                lat = float(result["geometry"]["lat"])
                lon = float(result["geometry"]["lon"])
                
                point = QgsPointXY(lon, lat)
                
                # Transform if needed (assuming WGS84 input)
                source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
                dest_crs = canvas.mapSettings().destinationCrs()
                
                if source_crs != dest_crs:
                    transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
                    point = transform.transform(point)
                    
                # Create an appropriate extent based on CRS type
                if dest_crs.isGeographic():
                    # For geographic CRS (degrees), use configurable buffer
                    buffer = self.config_manager.get_setting("zoom_buffer_geographic", 0.001)
                else:
                    # For projected CRS (meters/feet), use configurable buffer
                    buffer = self.config_manager.get_setting("zoom_buffer_projected", 500)
                    
                extent = QgsRectangle(point.x() - buffer, point.y() - buffer, point.x() + buffer, point.y() + buffer)
                canvas.setExtent(extent)
                canvas.refresh()
                
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error zooming to result: {str(e)}", 
                "Configurable Search", 
                Qgis.Warning
            )
            
    def _zoom_to_feature_result(self, result, iface):
        """Zoom to a feature search result."""
        try:
            geometry = result.get("geometry")
            if geometry and isinstance(geometry, QgsGeometry):
                canvas = iface.mapCanvas()
                bbox = geometry.boundingBox()
                
                # Expand bbox slightly
                bbox = bbox.buffered(bbox.width() * 0.1 if bbox.width() > 0 else 1000)
                
                canvas.setExtent(bbox)
                canvas.refresh()
                
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error zooming to feature result: {str(e)}", 
                "Configurable Search", 
                Qgis.Warning
            )
