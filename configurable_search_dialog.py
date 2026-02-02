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
from qgis.core import QgsProject, QgsVectorLayer, QgsApplication
from qgis.gui import QgsAuthConfigSelect
from .provider_templates import get_template_display_names, get_template_by_display_name, apply_template_to_provider
from . import help as help_module


class AdvancedSearchPanelDialog(QDialog):
    """Configuration dialog for the Advanced Search Panel plugin."""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Advanced Search Panel Settings")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Search Providers tab
        self.providers_tab = self.create_providers_tab()
        self.tab_widget.addTab(self.providers_tab, "Search Providers")
        
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
        
        # Connect double-click to edit provider
        self.providers_table.doubleClicked.connect(self.edit_provider)
        
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
        
        # Import/Export buttons
        self.export_providers_button = QPushButton("Export...")
        self.export_providers_button.clicked.connect(self.export_providers)
        self.export_providers_button.setToolTip("Export search providers to a file for backup or sharing")
        
        self.import_providers_button = QPushButton("Import...")
        self.import_providers_button.clicked.connect(self.import_providers)
        self.import_providers_button.setToolTip("Import search providers from a file")
        
        button_layout.addWidget(self.add_provider_button)
        button_layout.addWidget(self.edit_provider_button)
        button_layout.addWidget(self.remove_provider_button)
        button_layout.addStretch()
        button_layout.addWidget(self.export_providers_button)
        button_layout.addWidget(self.import_providers_button)
        button_layout.addStretch()
        button_layout.addWidget(self.move_up_button)
        button_layout.addWidget(self.move_down_button)
        
        layout.addLayout(button_layout)
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
        self.load_providers()
        
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
    
    def load_providers(self):
        """Load providers from config into the UI."""
        # Refresh config from config manager
        self.config = self.config_manager.get_config()
        providers = self.config.get("search_providers", [])
        self.providers_model.set_providers(providers)
        
        
    def save_config(self):
        """Save configuration from the UI."""
        # Save providers
        self.config["search_providers"] = self.providers_model.get_providers()
        
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
            
    def edit_provider(self, index=None):
        """Edit the selected provider.
        
        Args:
            index: QModelIndex from double-click signal (optional)
        """
        # Handle different types of index parameter
        if index is not None and hasattr(index, 'isValid') and index.isValid():
            # Called from double-click with valid QModelIndex
            row = index.row()
        else:
            # Called from button or with invalid/unexpected parameter, get selected row
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
    
    def export_providers(self):
        """Export search providers to a file."""
        if self.config_manager.export_providers(parent_widget=self):
            # The export was successful, config_manager already shows success message
            pass
    
    def import_providers(self):
        """Import search providers from a file."""
        # Create a custom message box with clear button options
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Import Providers")
        msg_box.setText("How would you like to import the providers?")
        msg_box.setInformativeText(
            "Replace All: Remove existing providers and replace with imported ones\n\n"
            "Merge: Add imported providers alongside existing ones (skip duplicates)"
        )
        
        # Add custom buttons with clear labels
        replace_button = msg_box.addButton("Replace All", QMessageBox.AcceptRole)
        merge_button = msg_box.addButton("Merge", QMessageBox.AcceptRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        
        msg_box.setDefaultButton(merge_button)
        msg_box.exec_()
        
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == cancel_button:
            return
        elif clicked_button == replace_button:
            merge_mode = False
        elif clicked_button == merge_button:
            merge_mode = True
        else:
            return  # Shouldn't happen, but just in case
        
        if self.config_manager.import_providers(parent_widget=self, merge_mode=merge_mode):
            # Reload the providers in the UI
            self.load_providers()
            
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
        # Add basic types
        basic_types = ["API", "Coordinate", "Layer"]
        # Add separator
        separator_items = ["--- API Templates ---"]
        # Add template types
        template_types = get_template_display_names()
        
        all_items = basic_types + separator_items + template_types
        self.type_combo.addItems(all_items)
        
        # Disable the separator item
        separator_index = basic_types.index("Layer") + 1  # Index after "Layer"
        model = self.type_combo.model()
        item = model.item(separator_index)
        item.setEnabled(False)
        
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addRow("Type:", self.type_combo)
        
        self.enabled_checkbox = QCheckBox()
        form_layout.addRow("Enabled:", self.enabled_checkbox)
        
        # Layer selection (for Layer providers)
        self.layer_combo = QComboBox()
        self.layer_combo.currentTextChanged.connect(self.on_layer_changed)
        self.layer_label = QLabel("Layer:")
        form_layout.addRow(self.layer_label, self.layer_combo)
        
        # Populate layer combo with project layers
        self._populate_layer_combo()
        
        # Layer search configuration
        self.search_fields_edit = QLineEdit()
        self.search_fields_label = QLabel("Search Fields:")
        self.search_fields_edit.setPlaceholderText("Leave empty for all text fields, or specify: field1,field2,field3")
        form_layout.addRow(self.search_fields_label, self.search_fields_edit)
        
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems(["Wildcard (contains)", "Exact match"])
        self.search_mode_label = QLabel("Search Mode:")
        form_layout.addRow(self.search_mode_label, self.search_mode_combo)
        
        # URL template (for API providers)
        self.url_edit = QLineEdit()
        self.url_label = QLabel("URL Template:")
        form_layout.addRow(self.url_label, self.url_edit)
        
        # URL help text
        self.url_help_label = QLabel("Use {search_term} as placeholder for the search query")
        self.url_help_label.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        self.url_help_label.setWordWrap(True)
        form_layout.addRow("", self.url_help_label)
        
        # HTTP method
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST"])
        self.method_combo.currentTextChanged.connect(self.on_method_changed)
        self.method_label = QLabel("HTTP Method:")
        form_layout.addRow(self.method_label, self.method_combo)
        
        # POST body (for POST requests)
        self.post_body_edit = QTextEdit()
        self.post_body_edit.setMinimumHeight(80)
        self.post_body_edit.setMaximumHeight(120)
        self.post_body_edit.setPlaceholderText("Enter POST body template. Use {search_term} as placeholder.\nExample: {\"query\": \"{search_term}\", \"limit\": 10}")
        self.post_body_label = QLabel("POST Body Template:")
        form_layout.addRow(self.post_body_label, self.post_body_edit)
        
        # POST body help text
        self.post_body_help_label = QLabel("Use {search_term} as placeholder for the search query in JSON, XML, or other formats")
        self.post_body_help_label.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        self.post_body_help_label.setWordWrap(True)
        form_layout.addRow("", self.post_body_help_label)
        
        # Add some spacing
        spacer_label = QLabel("")
        spacer_label.setMaximumHeight(10)
        form_layout.addRow("", spacer_label)
        
        # Regex filter
        self.regex_edit = QLineEdit()
        form_layout.addRow("Regex Filter:", self.regex_edit)
        
        # Stop on result
        self.stop_checkbox = QCheckBox()
        form_layout.addRow("Stop search on result:", self.stop_checkbox)
        
        layout.addLayout(form_layout)
        
        # Headers section (for API providers)
        self.headers_group = QGroupBox("HTTP Headers & Authentication")
        headers_layout = QVBoxLayout()
        
        # Authentication configuration
        auth_layout = QFormLayout()
        self.auth_config_select = QgsAuthConfigSelect()
        self.auth_config_select.setToolTip("Select a QGIS authentication configuration to use for this API")
        auth_layout.addRow("Authentication Config:", self.auth_config_select)
        
        auth_info_label = QLabel("Note: Authentication config will override manual headers for authentication")
        auth_info_label.setStyleSheet("color: #666; font-style: italic;")
        auth_layout.addRow(auth_info_label)
        
        headers_layout.addLayout(auth_layout)
        
        # Manual headers
        manual_headers_label = QLabel("Manual Headers (optional):")
        manual_headers_label.setStyleSheet("font-weight: bold;")
        headers_layout.addWidget(manual_headers_label)
        
        self.headers_edit = QTextEdit()
        self.headers_edit.setMaximumHeight(100)
        self.headers_edit.setPlaceholderText("Enter headers as JSON, e.g.:\n{\"Authorization\": \"Bearer token\", \"Content-Type\": \"application/json\"}")
        headers_layout.addWidget(self.headers_edit)
        
        self.headers_group.setLayout(headers_layout)
        layout.addWidget(self.headers_group)
        
        # Result parser section (for API providers)
        self.parser_group = QGroupBox("Result Parser")
        parser_layout = QFormLayout()
        
        self.results_path_edit = QLineEdit()
        self.results_path_edit.setPlaceholderText("places (leave empty for auto-detection)")
        parser_layout.addRow("Results Array Path:", self.results_path_edit)
        
        # Help text for results path
        results_path_help = QLabel("Specify the path to the results array using dot notation.\nExamples: 'places', 'data.results', 'response.items'\nLeave empty to auto-detect common array keys.")
        results_path_help.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        results_path_help.setWordWrap(True)
        parser_layout.addRow("", results_path_help)
        
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
        self.bbox_field_edit.setPlaceholderText("bbox or {west},{south},{east},{north}")
        parser_layout.addRow("Bounding Box Field/Template:", self.bbox_field_edit)
        
        # Help text for bbox template
        bbox_help = QLabel("Expected format: [west, south, east, north] in WGS84\n• Single field: 'bbox' (if API returns [west,south,east,north])\n• Template: '{west},{south},{east},{north}' or '{minX},{minY},{maxX},{maxY}'\n• Nominatim: '{boundingbox.2},{boundingbox.0},{boundingbox.3},{boundingbox.1}' (converts [south,north,west,east] to standard format)")
        bbox_help.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        bbox_help.setWordWrap(True)
        parser_layout.addRow("", bbox_help)
        
        self.parser_group.setLayout(parser_layout)
        layout.addWidget(self.parser_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Help button on the left
        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)
        self.help_button.setToolTip("Open help documentation for Layer-Based Providers")
        button_layout.addWidget(self.help_button)
        
        button_layout.addStretch()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Initial visibility update
        self.on_type_changed()
        self.on_method_changed()
        
    def on_method_changed(self):
        """Handle HTTP method change to show/hide POST body fields."""
        is_post = self.method_combo.currentText() == "POST"
        self.post_body_label.setVisible(is_post)
        self.post_body_edit.setVisible(is_post)
        self.post_body_help_label.setVisible(is_post)
        
    def _populate_layer_combo(self):
        """Populate the layer combo with available vector layers."""
        self.layer_combo.clear()
        self.layer_combo.addItem("Select a layer...", "")
        
        project = QgsProject.instance()
        for layer_id, layer in project.mapLayers().items():
            if isinstance(layer, QgsVectorLayer):
                self.layer_combo.addItem(layer.name(), layer_id)
                
    def validate_layer_selection(self):
        """Check if the currently selected layer still exists and show status."""
        if not hasattr(self, 'layer_combo'):
            return True
            
        layer_id = self.layer_combo.currentData()
        if not layer_id:
            return True
            
        project = QgsProject.instance()
        layer = project.mapLayer(layer_id)
        
        if not layer:
            # Layer doesn't exist - could update UI to show warning
            return False
        elif not isinstance(layer, QgsVectorLayer):
            # Not a vector layer
            return False
            
        return True
        
    def on_type_changed(self):
        """Handle provider type change."""
        selected_type = self.type_combo.currentText()
        
        # Check if this is a template selection
        template = get_template_by_display_name(selected_type)
        if template:
            # This is a template - apply it and show API controls
            self._apply_template(template)
            provider_type = "api"  # All templates are API-based
        else:
            # This is a basic type
            provider_type = selected_type.lower()
        
        # Show/hide API-specific controls
        api_visible = provider_type == "api"
        self.url_label.setVisible(api_visible)
        self.url_edit.setVisible(api_visible)
        self.url_help_label.setVisible(api_visible)
        self.method_label.setVisible(api_visible)
        self.method_combo.setVisible(api_visible)
        self.headers_group.setVisible(api_visible)
        self.parser_group.setVisible(api_visible)
        
        # Handle POST body visibility (only for API providers and POST method)
        if api_visible:
            self.on_method_changed()
        else:
            self.post_body_label.setVisible(False)
            self.post_body_edit.setVisible(False)
            self.post_body_help_label.setVisible(False)
        
        # Show/hide Layer-specific controls
        layer_visible = provider_type == "layer"
        self.layer_label.setVisible(layer_visible)
        self.layer_combo.setVisible(layer_visible)
        self.search_fields_label.setVisible(layer_visible)
        self.search_fields_edit.setVisible(layer_visible)
        self.search_mode_label.setVisible(layer_visible)
        self.search_mode_combo.setVisible(layer_visible)
        
    def _apply_template(self, template):
        """Apply a template configuration to populate the form fields."""
        # Don't auto-fill name - let user set it
        # self.name_edit.setText(template.get("name", ""))
        
        # Fill URL template
        self.url_edit.setText(template.get("url_template", ""))
        
        # Set HTTP method
        method = template.get("request_method", "GET")
        method_index = {"GET": 0, "POST": 1}.get(method, 0)
        self.method_combo.setCurrentIndex(method_index)
        
        # Fill POST body
        self.post_body_edit.setPlainText(template.get("post_body", ""))
        
        # Fill headers
        headers = template.get("headers", {})
        if headers:
            import json
            self.headers_edit.setPlainText(json.dumps(headers, indent=2))
        
        # Fill parser settings
        parser = template.get("result_parser", {})
        self.results_path_edit.setText(parser.get("results_path", ""))
        self.name_field_edit.setText(parser.get("name_field", ""))
        self.lat_field_edit.setText(parser.get("lat_field", ""))
        self.lon_field_edit.setText(parser.get("lon_field", ""))
        self.bbox_field_edit.setText(parser.get("bbox_field", ""))
        
        # Fill other settings
        self.enabled_checkbox.setChecked(template.get("enabled", True))
        self.regex_edit.setText(template.get("regex_filter", ""))
        self.stop_checkbox.setChecked(template.get("stop_on_result", False))
        
        # Show setup instructions if available
        instructions = template.get("setup_instructions", [])
        if instructions:
            self._show_setup_instructions(template.get("display_name", "Template"), instructions)
    
    def _show_setup_instructions(self, template_name, instructions):
        """Show setup instructions for the selected template."""
        instruction_text = f"<h3>Setup Instructions for {template_name}</h3>"
        instruction_text += "<ul>"
        for instruction in instructions:
            instruction_text += f"<li>{instruction}</li>"
        instruction_text += "</ul>"
        instruction_text += "<p><b>Note:</b> You can customize all settings after applying the template.</p>"
        
        msg = QMessageBox()
        msg.setWindowTitle("Template Applied")
        msg.setText(f"Template '{template_name}' has been applied to the form.")
        msg.setDetailedText("Setup Instructions:\n" + "\n".join(instructions))
        msg.setInformativeText("Please review the configuration and add your API credentials where needed.")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
        
    def on_layer_changed(self):
        """Handle layer selection change to update search fields placeholder."""
        # Check if search_fields_edit exists (may not during initial setup)
        if not hasattr(self, 'search_fields_edit'):
            return
            
        layer_id = self.layer_combo.currentData()
        if layer_id:
            project = QgsProject.instance()
            layer = project.mapLayer(layer_id)
            if layer and isinstance(layer, QgsVectorLayer):
                # Get text fields from the layer
                text_fields = []
                for field in layer.fields():
                    if field.type() in (QVariant.String, QVariant.Char):
                        text_fields.append(field.name())
                
                if text_fields:
                    placeholder = f"Available text fields: {', '.join(text_fields)}"
                    self.search_fields_edit.setPlaceholderText(placeholder)
                else:
                    self.search_fields_edit.setPlaceholderText("No text fields found in this layer")
            else:
                self.search_fields_edit.setPlaceholderText("Select a layer to see available fields")
        else:
            self.search_fields_edit.setPlaceholderText("Leave empty for all text fields, or specify: field1,field2,field3")
        
    def load_provider(self):
        """Load provider data into the form."""
        self.name_edit.setText(self.provider.get("name", ""))
        
        provider_type = self.provider.get("provider_type", "api")
        type_index = {"api": 0, "coordinate": 1, "layer": 2}.get(provider_type, 0)
        self.type_combo.setCurrentIndex(type_index)
        
        self.enabled_checkbox.setChecked(self.provider.get("enabled", True))
        self.url_edit.setText(self.provider.get("url_template", ""))
        
        # Load layer selection
        layer_id = self.provider.get("layer_id", "")
        layer_index = self.layer_combo.findData(layer_id)
        if layer_index >= 0:
            self.layer_combo.setCurrentIndex(layer_index)
            
        # Load layer search configuration
        search_fields = self.provider.get("search_fields", "")
        self.search_fields_edit.setText(search_fields)
        
        search_mode = self.provider.get("search_mode", "wildcard")
        mode_index = 0 if search_mode == "wildcard" else 1
        self.search_mode_combo.setCurrentIndex(mode_index)
        
        method = self.provider.get("request_method", "GET")
        method_index = {"GET": 0, "POST": 1}.get(method, 0)
        self.method_combo.setCurrentIndex(method_index)
        
        # Load POST body
        self.post_body_edit.setPlainText(self.provider.get("post_body", ""))
        
        self.regex_edit.setText(self.provider.get("regex_filter", ""))
        self.stop_checkbox.setChecked(self.provider.get("stop_on_result", False))
        
        # Load headers
        headers = self.provider.get("headers", {})
        if headers:
            import json
            self.headers_edit.setPlainText(json.dumps(headers, indent=2))
            
        # Load authentication configuration
        auth_config_id = self.provider.get("auth_config_id", "")
        self.auth_config_select.setConfigId(auth_config_id)
            
        # Load parser settings
        parser = self.provider.get("result_parser", {})
        self.results_path_edit.setText(parser.get("results_path", ""))
        self.name_field_edit.setText(parser.get("name_field", ""))
        self.lat_field_edit.setText(parser.get("lat_field", ""))
        self.lon_field_edit.setText(parser.get("lon_field", ""))
        self.bbox_field_edit.setText(parser.get("bbox_field", ""))
        
    def get_provider(self):
        """Get provider data from the form."""
        selected_type = self.type_combo.currentText()
        
        # Determine the actual provider type
        template = get_template_by_display_name(selected_type)
        if template:
            # This is a template - use "api" as the provider type
            provider_type = "api"
        else:
            # This is a basic type
            provider_type = selected_type.lower()
        
        provider = {
            "name": self.name_edit.text(),
            "provider_type": provider_type,
            "enabled": self.enabled_checkbox.isChecked(),
            "url_template": self.url_edit.text(),
            "request_method": self.method_combo.currentText(),
            "post_body": self.post_body_edit.toPlainText().strip(),
            "regex_filter": self.regex_edit.text(),
            "stop_on_result": self.stop_checkbox.isChecked(),
            "headers": {},
            "auth_config_id": self.auth_config_select.configId(),
            "result_parser": {}
        }
        
        # Add layer configuration for layer providers
        if self.type_combo.currentText().lower() == "layer":
            provider["layer_id"] = self.layer_combo.currentData()
            provider["search_fields"] = self.search_fields_edit.text().strip()
            provider["search_mode"] = "wildcard" if self.search_mode_combo.currentIndex() == 0 else "exact"
        
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
        if self.results_path_edit.text():
            parser["results_path"] = self.results_path_edit.text()
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
    
    def show_help(self):
        """Open the help documentation."""
        help_module.show_help()
