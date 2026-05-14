import json
import os
from datetime import datetime
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsMessageLog, Qgis, QgsExpressionContextUtils, QgsSettings


class ConfigManager:
    """Manages plugin configuration and settings."""
    
    def __init__(self):
        self.settings = QgsSettings()
        self.plugin_key = "configurable_search"
        self.default_config = {
            "search_providers": [],
            "stop_on_first_result": False,
            "max_results_per_provider": 100,
            "search_timeout": 30,
            "zoom_buffer_geographic": 0.001,  # Buffer for geographic CRS (degrees)
            "zoom_buffer_projected": 100      # Buffer for projected CRS (meters/feet)
        }
        self.project_providers = None  # To hold project-specific providers if imported
        
    def get_config(self):
        """Get the complete configuration.

        Merges stored settings with defaults so that:
        - Pre-seeded values in qgis3.ini (enterprise deployments) are respected.
        - Keys added in newer plugin versions always have a fallback value.
        """
        config_str = self.settings.value(f"{self.plugin_key}/config", "")
        if config_str:
            try:
                stored = json.loads(config_str)
                # Merge: defaults first, then stored values override them.
                # This ensures missing keys always resolve to their default.
                merged = self.default_config.copy()
                merged.update(stored)
                return merged
            except (json.JSONDecodeError, TypeError):
                pass
        return self.default_config.copy()
    
    def save_config(self, config):
        """Save the complete configuration."""
        config_str = json.dumps(config, indent=2)
        self.settings.setValue(f"{self.plugin_key}/config", config_str)
        
    def get_search_providers(self):
        """Get the list of search providers.
        
        Returns project-specific providers merged with global providers.
        Each provider will have a '_source' field indicating 'project' or 'global'.
        """
        # Get global providers from settings
        config = self.get_config()
        global_providers = config.get("search_providers", [])
        
        # Mark global providers with source
        for provider in global_providers:
            provider["_source"] = "global"
        
        # If no project providers, return global only
        if self.project_providers is None:
            return global_providers
        
        # Mark project providers with source
        project_providers_marked = []
        for provider in self.project_providers:
            marked_provider = provider.copy()
            marked_provider["_source"] = "project"
            project_providers_marked.append(marked_provider)
        
        # Merge project-specific providers with global ones
        return project_providers_marked + global_providers
    
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

    def get_toolbar_name(self):
        """Get the configured toolbar name.

        Stored as a standalone QSettings key, not in the exported JSON config,
        so it is local to this machine and never committed to source control.
        """
        return self.settings.value(f"{self.plugin_key}/toolbar_name", "")

    def set_toolbar_name(self, toolbar_name):
        """Set the configured toolbar name.

        Stored as a standalone QSettings key, not in the exported JSON config,
        so it is local to this machine and never committed to source control.
        """
        self.settings.setValue(f"{self.plugin_key}/toolbar_name", toolbar_name)

    def get_toolbar_buttons(self):
        """Get which action buttons are shown in the toolbar.

        Returns a (show_configure, show_toggle) tuple of bools.
        Stored in QSettings, local to this machine.
        """
        show_configure = self.settings.value(
            f"{self.plugin_key}/toolbar_show_configure", True, type=bool)
        show_toggle = self.settings.value(
            f"{self.plugin_key}/toolbar_show_toggle", True, type=bool)
        return show_configure, show_toggle

    def set_toolbar_buttons(self, show_configure, show_toggle):
        """Set which action buttons are shown in the toolbar.

        Stored in QSettings, local to this machine.
        """
        self.settings.setValue(f"{self.plugin_key}/toolbar_show_configure", show_configure)
        self.settings.setValue(f"{self.plugin_key}/toolbar_show_toggle", show_toggle)

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
                    "bbox_field": "{boundingbox.2},{boundingbox.0},{boundingbox.3},{boundingbox.1}"
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

    def import_project_providers(self):
        """Import search providers from the current QGIS project properties.
        
        Reads the 'search_providers' custom property from the project and loads it
        into the project_providers instance variable without saving to global settings.
        """
        try:
            project = QgsProject.instance()
            
            # Read the custom property from the project
            # readEntry returns a tuple: (value, ok)
            search_providers_json = QgsExpressionContextUtils.projectScope(project).variable("search_providers")
            
            if search_providers_json is None or not search_providers_json:
                # Setting not found or empty, set to None
                QgsMessageLog.logMessage(
                    "No search_providers found in project properties",
                    "Advanced Search Panel",
                    Qgis.Info
                )
                self.project_providers = None
                return False
            
            # Validate that the variable is a string (expected for JSON data)
            if not isinstance(search_providers_json, str):
                error_msg = f"Invalid search_providers variable type: expected string, got {type(search_providers_json).__name__}"
                QgsMessageLog.logMessage(error_msg, "Advanced Search Panel", Qgis.Warning)
                self.project_providers = None
                return False
            
            # Parse the JSON array
            import_data = json.loads(search_providers_json)
            
            # Validate import data structure
            if not isinstance(import_data, list):
                # Check if it's a dict with search_providers key (exported format)
                if isinstance(import_data, dict) and "search_providers" in import_data:
                    providers_to_import = import_data["search_providers"]
                else:
                    raise ValueError("Invalid format: expected JSON array or export format")
            else:
                providers_to_import = import_data
            
            if not isinstance(providers_to_import, list):
                raise ValueError("Invalid providers data: expected list of provider configurations")
            
            # Validate each provider
            for i, provider in enumerate(providers_to_import):
                if not isinstance(provider, dict):
                    raise ValueError(f"Invalid provider at index {i}: expected object")
                if "name" not in provider:
                    raise ValueError(f"Invalid provider at index {i}: missing 'name' field")
            
            # Store in instance variable without merging or replacing global config
            final_providers = providers_to_import
            self.project_providers = final_providers

            QgsMessageLog.logMessage(
                f"Found {len(final_providers)} search provider(s) from project properties",
                "Advanced Search Panel",
                Qgis.Info
            )
            
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse project search_providers JSON: {str(e)}"
            QgsMessageLog.logMessage(error_msg, "Advanced Search Panel", Qgis.Warning)
            self.project_providers = None
            return False
        
        except TypeError as e:
            error_msg = f"Type error when processing project search_providers: {str(e)}"
            QgsMessageLog.logMessage(error_msg, "Advanced Search Panel", Qgis.Warning)
            self.project_providers = None
            return False
        
        except ValueError as e:
            error_msg = f"Invalid data format in project search_providers: {str(e)}"
            QgsMessageLog.logMessage(error_msg, "Advanced Search Panel", Qgis.Warning)
            self.project_providers = None
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error importing project search providers: {str(e)}"
            QgsMessageLog.logMessage(error_msg, "Advanced Search Panel", Qgis.Warning)
            self.project_providers = None
            return False

    def clear_project_providers(self):
        """Handle project cleared event - clear project-specific search providers."""
        self.project_providers = None
        QgsMessageLog.logMessage(
            "Project cleared - removed project-specific search providers",
            "Advanced Search Panel",
            Qgis.Info
        )

    def save_project_providers(self, providers, parent_widget=None):
        """Save a list of providers to the current QGIS project as a project variable.

        Writes a JSON array to the 'search_providers' project variable so that
        the providers travel with the .qgs/.qgz file and are loaded automatically
        when the project is opened.

        Args:
            providers: List of provider dicts to save (must not contain _source keys).
            parent_widget: Parent widget for error dialogs.

        Returns:
            True on success, False on failure.
        """
        try:
            project = QgsProject.instance()
            if not project.fileName():
                from qgis.PyQt.QtWidgets import QMessageBox
                QMessageBox.warning(
                    parent_widget,
                    "No Project Open",
                    "There is no saved QGIS project open.\n\n"
                    "Please save your project first, then try again."
                )
                return False

            # Strip internal _source markers before saving
            clean_providers = []
            for p in providers:
                clean = p.copy()
                clean.pop("_source", None)
                clean_providers.append(clean)

            providers_json = json.dumps(clean_providers, indent=2, ensure_ascii=False)
            QgsExpressionContextUtils.setProjectVariable(project, "search_providers", providers_json)

            # Refresh in-memory project providers so they are visible immediately
            self.project_providers = clean_providers

            QgsMessageLog.logMessage(
                f"Saved {len(clean_providers)} provider(s) to project variable 'search_providers'",
                "Advanced Search Panel",
                Qgis.Info
            )
            return True

        except Exception as e:
            error_msg = f"Failed to save providers to project: {str(e)}"
            QgsMessageLog.logMessage(error_msg, "Advanced Search Panel", Qgis.Critical)
            if parent_widget:
                from qgis.PyQt.QtWidgets import QMessageBox
                QMessageBox.critical(parent_widget, "Save to Project Failed", error_msg)
            return False

    def export_providers(self, file_path=None, parent_widget=None):
        """Export search providers to a JSON file."""
        try:
            if not file_path:
                file_path, _ = QFileDialog.getSaveFileName(
                    parent_widget,
                    "Export Search Providers",
                    f"search_providers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "JSON Files (*.json);;All Files (*)"
                )
                
            if not file_path:
                return False
                
            providers = self.get_search_providers()
            config = self.get_config()
            
            export_data = {
                "export_info": {
                    "plugin": "Advanced Search Panel",
                    "version": "1.0.0",
                    "exported_at": datetime.now().isoformat(),
                    "provider_count": len(providers)
                },
                "search_providers": providers,
                "plugin_settings": {
                    "stop_on_first_result": config.get("stop_on_first_result", False),
                    "max_results_per_provider": config.get("max_results_per_provider", 100),
                    "search_timeout": config.get("search_timeout", 30),
                    "zoom_buffer_geographic": config.get("zoom_buffer_geographic", 0.001),
                    "zoom_buffer_projected": config.get("zoom_buffer_projected", 100)
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            QgsMessageLog.logMessage(
                f"Search providers exported successfully to: {file_path}",
                "Advanced Search Panel",
                Qgis.Info
            )
            
            if parent_widget:
                QMessageBox.information(
                    parent_widget,
                    "Export Successful",
                    f"Search providers exported successfully to:\n{file_path}"
                )
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to export search providers: {str(e)}"
            QgsMessageLog.logMessage(error_msg, "Advanced Search Panel", Qgis.Critical)
            
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Export Failed",
                    error_msg
                )
            
            return False
    
    def import_providers(self, file_path=None, parent_widget=None, merge_mode=False):
        """Import search providers from a JSON file.
        
        Args:
            file_path: Path to the JSON file to import
            parent_widget: Parent widget for dialogs
            merge_mode: If True, merge with existing providers; if False, replace all
        """
        try:
            if not file_path:
                file_path, _ = QFileDialog.getOpenFileName(
                    parent_widget,
                    "Import Search Providers",
                    "",
                    "JSON Files (*.json);;All Files (*)"
                )
                
            if not file_path:
                return False
                
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data structure
            if not isinstance(import_data, dict):
                raise ValueError("Invalid file format: expected JSON object")
            
            # Check if it's our export format or legacy format
            if "search_providers" in import_data:
                # New export format
                providers_to_import = import_data["search_providers"]
                plugin_settings = import_data.get("plugin_settings", {})
                export_info = import_data.get("export_info", {})
            elif isinstance(import_data, list):
                # Legacy format - just a list of providers
                providers_to_import = import_data
                plugin_settings = {}
                export_info = {}
            else:
                # Try to treat the whole thing as providers if it has the right structure
                if "name" in import_data or (isinstance(import_data, list) and 
                                           len(import_data) > 0 and 
                                           isinstance(import_data[0], dict) and 
                                           "name" in import_data[0]):
                    providers_to_import = import_data if isinstance(import_data, list) else [import_data]
                    plugin_settings = {}
                    export_info = {}
                else:
                    raise ValueError("Invalid file format: no recognizable provider data found")
            
            if not isinstance(providers_to_import, list):
                raise ValueError("Invalid providers data: expected list of provider configurations")
            
            # Validate each provider
            for i, provider in enumerate(providers_to_import):
                if not isinstance(provider, dict):
                    raise ValueError(f"Invalid provider at index {i}: expected object")
                if "name" not in provider:
                    raise ValueError(f"Invalid provider at index {i}: missing 'name' field")
            
            # Handle import mode
            if merge_mode:
                existing_providers = self.get_search_providers()
                existing_names = {p.get("name", "") for p in existing_providers}
                
                # Only add providers that don't already exist
                new_providers = []
                duplicates = []
                
                for provider in providers_to_import:
                    if provider.get("name", "") in existing_names:
                        duplicates.append(provider.get("name", ""))
                    else:
                        new_providers.append(provider)
                
                if duplicates and parent_widget:
                    duplicate_list = "\n".join(duplicates)
                    QMessageBox.information(
                        parent_widget,
                        "Duplicate Providers Skipped",
                        f"The following providers already exist and were skipped:\n\n{duplicate_list}"
                    )
                
                final_providers = existing_providers + new_providers
                imported_count = len(new_providers)
            else:
                # Replace mode - confirm with user
                existing_count = len(self.get_search_providers())
                if existing_count > 0 and parent_widget:
                    reply = QMessageBox.question(
                        parent_widget,
                        "Replace Existing Providers",
                        f"This will replace all {existing_count} existing search providers.\n\nAre you sure you want to continue?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return False
                
                final_providers = providers_to_import
                imported_count = len(providers_to_import)
            
            # Save the providers
            self.save_search_providers(final_providers)
            
            # Import plugin settings if available
            if plugin_settings:
                config = self.get_config()
                for key, value in plugin_settings.items():
                    if key in self.default_config:  # Only import known settings
                        config[key] = value
                self.save_config(config)
            
            # Log success
            mode_text = "merged with" if merge_mode else "replaced"
            QgsMessageLog.logMessage(
                f"Successfully imported {imported_count} search providers ({mode_text} existing configuration)",
                "Advanced Search Panel",
                Qgis.Info
            )
            
            if parent_widget:
                export_info_text = ""
                if export_info:
                    export_info_text = f"\n\nImported from: {export_info.get('plugin', 'Unknown')} export created {export_info.get('exported_at', 'Unknown date')}"
                
                QMessageBox.information(
                    parent_widget,
                    "Import Successful",
                    f"Successfully imported {imported_count} search providers.{export_info_text}"
                )
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to import search providers: {str(e)}"
            QgsMessageLog.logMessage(error_msg, "Advanced Search Panel", Qgis.Critical)
            
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Import Failed",
                    error_msg
                )
            
            return False
    
    def get_export_file_path(self, parent_widget=None):
        """Get a file path for exporting configuration."""
        default_name = f"search_providers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Export Search Providers",
            default_name,
            "JSON Files (*.json);;All Files (*)"
        )
        return file_path
    
    def get_import_file_path(self, parent_widget=None):
        """Get a file path for importing configuration."""
        file_path, _ = QFileDialog.getOpenFileName(
            parent_widget,
            "Import Search Providers", 
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        return file_path
