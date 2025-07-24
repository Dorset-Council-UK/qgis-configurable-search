import os
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QAbstractTableModel, QVariant, QModelIndex
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QPushButton, QTableView, QLineEdit, QSpinBox, QCheckBox, 
    QComboBox, QTextEdit, QLabel, QGroupBox, QFormLayout,
    QHeaderView, QAbstractItemView, QMessageBox, QInputDialog, QDoubleSpinBox
)
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem
from qgis.core import QgsProject, QgsVectorLayer


class ConfigurableSearchDialog(QDialog):
    """Configuration dialog for the Configurable Search plugin."""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Configurable Search Settings")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # API Providers tab
        self.providers_tab = self.create_providers_tab()
        self.tab_widget.addTab(self.providers_tab, "API Providers")
        
        # Layer Search tab
        self.layers_tab = self.create_layers_tab()
        self.tab_widget.addTab(self.layers_tab, "Layer Search")
        
        # General Settings tab
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "General Settings")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_changes)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_providers_tab(self):
        """Create the API providers configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Provider list
        self.providers_model = ProvidersTableModel()
        self.providers_table = QTableView()
        self.providers_table.setModel(self.providers_model)
        self.providers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Make table columns resizable
        header = self.providers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(QLabel("Search Providers:"))
        layout.addWidget(self.providers_table)
        
        # Buttons for provider management
        button_layout = QHBoxLayout()
        
        self.add_provider_button = QPushButton("Add Provider")
        self.add_provider_button.clicked.connect(self.add_provider)
        
        self.edit_provider_button = QPushButton("Edit Provider")
        self.edit_provider_button.clicked.connect(self.edit_provider)
        
        self.remove_provider_button = QPushButton("Remove Provider")
        self.remove_provider_button.clicked.connect(self.remove_provider)
        
        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.clicked.connect(self.move_provider_up)
        
        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.clicked.connect(self.move_provider_down)
        
        button_layout.addWidget(self.add_provider_button)
        button_layout.addWidget(self.edit_provider_button)
        button_layout.addWidget(self.remove_provider_button)
        button_layout.addStretch()
        button_layout.addWidget(self.move_up_button)
        button_layout.addWidget(self.move_down_button)
        
        layout.addLayout(button_layout)
        widget.setLayout(layout)
        return widget
        
    def create_layers_tab(self):
        """Create the layer search configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Layer search settings
        layer_group = QGroupBox("Layer Search Settings")
        layer_layout = QFormLayout()
        
        self.include_layers_checkbox = QCheckBox("Enable layer search")
        layer_layout.addRow(self.include_layers_checkbox)
        
        self.feature_search_checkbox = QCheckBox("Search within layer features")
        layer_layout.addRow(self.feature_search_checkbox)
        
        self.max_features_spinbox = QSpinBox()
        self.max_features_spinbox.setRange(1, 1000)
        self.max_features_spinbox.setValue(50)
        layer_layout.addRow("Max features per layer:", self.max_features_spinbox)
        
        layer_group.setLayout(layer_layout)
        layout.addWidget(layer_group)
        
        # Available layers
        layers_group = QGroupBox("Available Project Layers")
        layers_layout = QVBoxLayout()
        
        self.layers_model = LayersTableModel()
        self.layers_table = QTableView()
        self.layers_table.setModel(self.layers_model)
        
        layers_layout.addWidget(self.layers_table)
        layers_group.setLayout(layers_layout)
        layout.addWidget(layers_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_settings_tab(self):
        """Create the general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Search behavior settings
        behavior_group = QGroupBox("Search Behavior")
        behavior_layout = QFormLayout()
        
        self.stop_on_first_checkbox = QCheckBox("Stop searching when first result is found")
        behavior_layout.addRow(self.stop_on_first_checkbox)
        
        self.max_results_spinbox = QSpinBox()
        self.max_results_spinbox.setRange(1, 100)
        self.max_results_spinbox.setValue(10)
        behavior_layout.addRow("Max results per provider:", self.max_results_spinbox)
        
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(5, 120)
        self.timeout_spinbox.setValue(30)
        self.timeout_spinbox.setSuffix(" seconds")
        behavior_layout.addRow("Search timeout:", self.timeout_spinbox)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        # Zoom settings
        zoom_group = QGroupBox("Zoom Behavior")
        zoom_layout = QFormLayout()
        
        self.zoom_geographic_spinbox = QDoubleSpinBox()
        self.zoom_geographic_spinbox.setRange(0.0001, 1.0)
        self.zoom_geographic_spinbox.setDecimals(4)
        self.zoom_geographic_spinbox.setSingleStep(0.0001)
        self.zoom_geographic_spinbox.setValue(0.001)
        self.zoom_geographic_spinbox.setSuffix(" degrees")
        zoom_layout.addRow("Geographic zoom buffer:", self.zoom_geographic_spinbox)
        
        self.zoom_projected_spinbox = QSpinBox()
        self.zoom_projected_spinbox.setRange(10, 10000)
        self.zoom_projected_spinbox.setValue(500)
        self.zoom_projected_spinbox.setSuffix(" units")
        zoom_layout.addRow("Projected zoom buffer:", self.zoom_projected_spinbox)
        
        zoom_group.setLayout(zoom_layout)
        layout.addWidget(zoom_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def load_config(self):
        """Load configuration into the UI."""
        # Load providers
        providers = self.config.get("search_providers", [])
        self.providers_model.set_providers(providers)
        
        # Load layer settings
        self.include_layers_checkbox.setChecked(
            self.config.get("include_project_layers", True)
        )
        self.feature_search_checkbox.setChecked(
            self.config.get("feature_search_enabled", True)
        )
        self.max_features_spinbox.setValue(
            self.config.get("max_features_per_layer", 50)
        )
        
        # Load general settings
        self.stop_on_first_checkbox.setChecked(
            self.config.get("stop_on_first_result", False)
        )
        self.max_results_spinbox.setValue(
            self.config.get("max_results_per_provider", 10)
        )
        self.timeout_spinbox.setValue(
            self.config.get("search_timeout", 30)
        )
        
        # Load zoom settings
        self.zoom_geographic_spinbox.setValue(
            self.config.get("zoom_buffer_geographic", 0.001)
        )
        self.zoom_projected_spinbox.setValue(
            self.config.get("zoom_buffer_projected", 500)
        )
        
        # Load project layers
        self.layers_model.load_project_layers()
        
    def save_config(self):
        """Save configuration from the UI."""
        # Save providers
        self.config["search_providers"] = self.providers_model.get_providers()
        
        # Save layer settings
        self.config["include_project_layers"] = self.include_layers_checkbox.isChecked()
        self.config["feature_search_enabled"] = self.feature_search_checkbox.isChecked()
        self.config["max_features_per_layer"] = self.max_features_spinbox.value()
        
        # Save general settings
        self.config["stop_on_first_result"] = self.stop_on_first_checkbox.isChecked()
        self.config["max_results_per_provider"] = self.max_results_spinbox.value()
        self.config["search_timeout"] = self.timeout_spinbox.value()
        
        # Save zoom settings
        self.config["zoom_buffer_geographic"] = self.zoom_geographic_spinbox.value()
        self.config["zoom_buffer_projected"] = self.zoom_projected_spinbox.value()
        
        # Save to config manager
        self.config_manager.save_config(self.config)
        
    def add_provider(self):
        """Add a new search provider."""
        dialog = ProviderEditDialog()
        if dialog.exec_() == QDialog.Accepted:
            provider = dialog.get_provider()
            self.providers_model.add_provider(provider)
            
    def edit_provider(self):
        """Edit the selected provider."""
        selected_rows = self.providers_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a provider to edit.")
            return
            
        row = selected_rows[0].row()
        provider = self.providers_model.get_provider(row)
        
        dialog = ProviderEditDialog(provider)
        if dialog.exec_() == QDialog.Accepted:
            updated_provider = dialog.get_provider()
            self.providers_model.update_provider(row, updated_provider)
            
    def remove_provider(self):
        """Remove the selected provider."""
        selected_rows = self.providers_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a provider to remove.")
            return
            
        row = selected_rows[0].row()
        provider = self.providers_model.get_provider(row)
        
        reply = QMessageBox.question(
            self, 
            "Remove Provider", 
            f"Are you sure you want to remove the provider '{provider.get('name', 'Unknown')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.providers_model.remove_provider(row)
            
    def move_provider_up(self):
        """Move the selected provider up in priority."""
        selected_rows = self.providers_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if row > 0:
            self.providers_model.move_provider(row, row - 1)
            # Update selection
            new_index = self.providers_model.index(row - 1, 0)
            self.providers_table.selectRow(row - 1)
            
    def move_provider_down(self):
        """Move the selected provider down in priority."""
        selected_rows = self.providers_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if row < self.providers_model.rowCount() - 1:
            self.providers_model.move_provider(row, row + 1)
            # Update selection
            self.providers_table.selectRow(row + 1)
            
    def apply_changes(self):
        """Apply changes without closing the dialog."""
        self.save_config()
        
    def accept(self):
        """Accept and save changes."""
        self.save_config()
        super().accept()


class ProvidersTableModel(QAbstractTableModel):
    """Table model for search providers."""
    
    def __init__(self):
        super().__init__()
        self.providers = []
        self.headers = ["Name", "Type", "Enabled", "Priority", "Regex Filter"]
        
    def set_providers(self, providers):
        """Set the providers list."""
        self.beginResetModel()
        self.providers = providers.copy()
        # Update priorities based on list order
        for i, provider in enumerate(self.providers):
            provider["priority"] = i + 1
        self.endResetModel()
        
    def get_providers(self):
        """Get the providers list."""
        return self.providers.copy()
        
    def add_provider(self, provider):
        """Add a new provider."""
        self.beginInsertRows(QModelIndex(), len(self.providers), len(self.providers))
        provider["priority"] = len(self.providers) + 1
        self.providers.append(provider)
        self.endInsertRows()
        
    def get_provider(self, row):
        """Get a provider by row."""
        if 0 <= row < len(self.providers):
            return self.providers[row]
        return None
        
    def update_provider(self, row, provider):
        """Update a provider."""
        if 0 <= row < len(self.providers):
            provider["priority"] = self.providers[row]["priority"]
            self.providers[row] = provider
            self.dataChanged.emit(
                self.index(row, 0), 
                self.index(row, self.columnCount() - 1)
            )
            
    def remove_provider(self, row):
        """Remove a provider."""
        if 0 <= row < len(self.providers):
            self.beginRemoveRows(QModelIndex(), row, row)
            self.providers.pop(row)
            # Update priorities
            for i, provider in enumerate(self.providers):
                provider["priority"] = i + 1
            self.endRemoveRows()
            
    def move_provider(self, from_row, to_row):
        """Move a provider from one position to another."""
        if (0 <= from_row < len(self.providers) and 
            0 <= to_row < len(self.providers) and 
            from_row != to_row):
            
            self.beginMoveRows(QModelIndex(), from_row, from_row, QModelIndex(), 
                             to_row + 1 if to_row > from_row else to_row)
            
            provider = self.providers.pop(from_row)
            self.providers.insert(to_row, provider)
            
            # Update priorities
            for i, provider in enumerate(self.providers):
                provider["priority"] = i + 1
                
            self.endMoveRows()
            
    def rowCount(self, parent=QModelIndex()):
        return len(self.providers)
        
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.providers):
            return QVariant()
            
        provider = self.providers[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Name
                return provider.get("name", "")
            elif column == 1:  # Type
                return provider.get("provider_type", "api").title()
            elif column == 2:  # Enabled
                return "Yes" if provider.get("enabled", True) else "No"
            elif column == 3:  # Priority
                return str(provider.get("priority", 1))
            elif column == 4:  # Regex Filter
                return provider.get("regex_filter", "")
                
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return QVariant()


class LayersTableModel(QAbstractTableModel):
    """Table model for project layers."""
    
    def __init__(self):
        super().__init__()
        self.layers = []
        self.headers = ["Layer Name", "Type", "Feature Count"]
        
    def load_project_layers(self):
        """Load layers from the current project."""
        self.beginResetModel()
        self.layers = []
        
        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                self.layers.append({
                    "id": layer.id(),
                    "name": layer.name(),
                    "type": layer.geometryType().name if layer.geometryType() else "No Geometry",
                    "feature_count": layer.featureCount()
                })
                
        self.endResetModel()
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.layers)
        
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.layers):
            return QVariant()
            
        layer = self.layers[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Name
                return layer.get("name", "")
            elif column == 1:  # Type
                return layer.get("type", "")
            elif column == 2:  # Feature Count
                return str(layer.get("feature_count", 0))
                
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return QVariant()


class ProviderEditDialog(QDialog):
    """Dialog for editing search provider settings."""
    
    def __init__(self, provider=None):
        super().__init__()
        self.provider = provider.copy() if provider else {}
        self.setup_ui()
        self.load_provider()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Edit Search Provider")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Basic settings
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["API", "Coordinate", "Layer"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addRow("Type:", self.type_combo)
        
        self.enabled_checkbox = QCheckBox()
        form_layout.addRow("Enabled:", self.enabled_checkbox)
        
        # URL template (for API providers)
        self.url_edit = QLineEdit()
        self.url_label = QLabel("URL Template:")
        form_layout.addRow(self.url_label, self.url_edit)
        
        # HTTP method
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST"])
        self.method_label = QLabel("HTTP Method:")
        form_layout.addRow(self.method_label, self.method_combo)
        
        # Regex filter
        self.regex_edit = QLineEdit()
        form_layout.addRow("Regex Filter:", self.regex_edit)
        
        # Stop on result
        self.stop_checkbox = QCheckBox()
        form_layout.addRow("Stop search on result:", self.stop_checkbox)
        
        layout.addLayout(form_layout)
        
        # Headers section (for API providers)
        self.headers_group = QGroupBox("HTTP Headers")
        headers_layout = QVBoxLayout()
        
        self.headers_edit = QTextEdit()
        self.headers_edit.setMaximumHeight(100)
        self.headers_edit.setPlaceholderText("Enter headers as JSON, e.g.:\n{\"Authorization\": \"Bearer token\"}")
        headers_layout.addWidget(self.headers_edit)
        
        self.headers_group.setLayout(headers_layout)
        layout.addWidget(self.headers_group)
        
        # Result parser section (for API providers)
        self.parser_group = QGroupBox("Result Parser")
        parser_layout = QFormLayout()
        
        self.name_field_edit = QLineEdit()
        self.name_field_edit.setPlaceholderText("name")
        parser_layout.addRow("Name Field:", self.name_field_edit)
        
        self.lat_field_edit = QLineEdit()
        self.lat_field_edit.setPlaceholderText("lat")
        parser_layout.addRow("Latitude Field:", self.lat_field_edit)
        
        self.lon_field_edit = QLineEdit()
        self.lon_field_edit.setPlaceholderText("lon")
        parser_layout.addRow("Longitude Field:", self.lon_field_edit)
        
        self.bbox_field_edit = QLineEdit()
        self.bbox_field_edit.setPlaceholderText("boundingbox")
        parser_layout.addRow("Bounding Box Field:", self.bbox_field_edit)
        
        self.parser_group.setLayout(parser_layout)
        layout.addWidget(self.parser_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Initial visibility update
        self.on_type_changed()
        
    def on_type_changed(self):
        """Handle provider type change."""
        provider_type = self.type_combo.currentText().lower()
        
        # Show/hide API-specific controls
        api_visible = provider_type == "api"
        self.url_label.setVisible(api_visible)
        self.url_edit.setVisible(api_visible)
        self.method_label.setVisible(api_visible)
        self.method_combo.setVisible(api_visible)
        self.headers_group.setVisible(api_visible)
        self.parser_group.setVisible(api_visible)
        
    def load_provider(self):
        """Load provider data into the form."""
        self.name_edit.setText(self.provider.get("name", ""))
        
        provider_type = self.provider.get("provider_type", "api")
        type_index = {"api": 0, "coordinate": 1, "layer": 2}.get(provider_type, 0)
        self.type_combo.setCurrentIndex(type_index)
        
        self.enabled_checkbox.setChecked(self.provider.get("enabled", True))
        self.url_edit.setText(self.provider.get("url_template", ""))
        
        method = self.provider.get("request_method", "GET")
        method_index = {"GET": 0, "POST": 1}.get(method, 0)
        self.method_combo.setCurrentIndex(method_index)
        
        self.regex_edit.setText(self.provider.get("regex_filter", ""))
        self.stop_checkbox.setChecked(self.provider.get("stop_on_result", False))
        
        # Load headers
        headers = self.provider.get("headers", {})
        if headers:
            import json
            self.headers_edit.setPlainText(json.dumps(headers, indent=2))
            
        # Load parser settings
        parser = self.provider.get("result_parser", {})
        self.name_field_edit.setText(parser.get("name_field", ""))
        self.lat_field_edit.setText(parser.get("lat_field", ""))
        self.lon_field_edit.setText(parser.get("lon_field", ""))
        self.bbox_field_edit.setText(parser.get("bbox_field", ""))
        
    def get_provider(self):
        """Get provider data from the form."""
        provider = {
            "name": self.name_edit.text(),
            "provider_type": self.type_combo.currentText().lower(),
            "enabled": self.enabled_checkbox.isChecked(),
            "url_template": self.url_edit.text(),
            "request_method": self.method_combo.currentText(),
            "regex_filter": self.regex_edit.text(),
            "stop_on_result": self.stop_checkbox.isChecked(),
            "headers": {},
            "result_parser": {}
        }
        
        # Parse headers
        headers_text = self.headers_edit.toPlainText().strip()
        if headers_text:
            try:
                import json
                provider["headers"] = json.loads(headers_text)
            except json.JSONDecodeError:
                pass
                
        # Parser settings
        parser = {}
        if self.name_field_edit.text():
            parser["name_field"] = self.name_field_edit.text()
        if self.lat_field_edit.text():
            parser["lat_field"] = self.lat_field_edit.text()
        if self.lon_field_edit.text():
            parser["lon_field"] = self.lon_field_edit.text()
        if self.bbox_field_edit.text():
            parser["bbox_field"] = self.bbox_field_edit.text()
            
        provider["result_parser"] = parser
        
        return provider
