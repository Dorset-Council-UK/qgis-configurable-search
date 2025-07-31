import os
import sys
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QThread, pyqtSignal, QTimer
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QComboBox, QLineEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame, QSizePolicy, QDockWidget
from qgis.core import QgsProject, QgsMessageLog, Qgis, QgsGeometry, QgsRectangle, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY
from qgis.gui import QgsGui

# Initialize Qt resources from file resources.py
from .resources import *
from .configurable_search_dialog import ConfigurableSearchDialog
from .search_engine import SearchEngine
from .config_manager import ConfigManager


class ConfigurableSearch:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale_setting = QSettings().value('locale/userLocale', 'en')
        # Convert QVariant to string and get first 2 characters, fallback to 'en'
        if locale_setting:
            locale = str(locale_setting)[:2]
        else:
            locale = 'en'
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ConfigurableSearch_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Configurable Search')
        self.toolbar = None
        self.search_widget = None
        self.config_manager = ConfigManager()
        self.search_engine = SearchEngine(self.config_manager)
        
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ConfigurableSearch', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = os.path.join(self.plugin_dir, 'icon.svg')
        
        # Add configuration action
        self.add_action(
            icon_path,
            text=self.tr(u'Configure Search'),
            callback=self.show_config_dialog,
            parent=self.iface.mainWindow())
        
        # Add toggle panel action
        self.add_action(
            icon_path,
            text=self.tr(u'Toggle Search Panel'),
            callback=self.toggle_search_panel,
            parent=self.iface.mainWindow())

        # Create search dock widget
        self.create_search_widget()
        
        # will be set False in run()
        self.first_start = True

    def create_search_widget(self):
        """Create the search dock widget panel."""
        # Create search widget
        self.search_widget = SearchWidget(self.search_engine, self.config_manager, self.iface)
        
        # Create dock widget
        self.dock_widget = QDockWidget("Configurable Search", self.iface.mainWindow())
        self.dock_widget.setObjectName("ConfigurableSearchDock")
        self.dock_widget.setWidget(self.search_widget)
        
        # Set dock widget properties
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        
        # Add dock widget to QGIS interface
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)
        
    def toggle_search_panel(self):
        """Toggle the visibility of the search panel."""
        if hasattr(self, 'dock_widget') and self.dock_widget:
            if self.dock_widget.isVisible():
                self.dock_widget.hide()
            else:
                self.dock_widget.show()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Configurable Search'),
                action)
            self.iface.removeToolBarIcon(action)
        
        # Remove the dock widget
        if hasattr(self, 'dock_widget') and self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget = None

    def show_config_dialog(self):
        """Show the configuration dialog."""
        if self.first_start == True:
            self.first_start = False
            
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if hasattr(self, 'dlg') and self.dlg:
            pass
        else:
            self.dlg = ConfigurableSearchDialog(self.config_manager)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Refresh search engine configuration
            self.search_engine.refresh_config()
            # Update search widget
            if self.search_widget:
                self.search_widget.refresh_config()


class SearchWidget(QWidget):
    """Custom search widget for the toolbar with results dropdown."""
    
    def __init__(self, search_engine, config_manager, iface):
        super().__init__()
        self.search_engine = search_engine
        self.config_manager = config_manager
        self.iface = iface
        self.current_results = []
        
        # Set size policy for panel (allow expansion)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Setup the UI components for panel layout."""
        # Main layout - vertical to stack search box and results
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # More padding for panel
        main_layout.setSpacing(5)
        main_layout.setAlignment(Qt.AlignTop)  # Align contents to top
        
        # Search box layout
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # Panel title/header
        panel_title = QLabel("🔍 Configurable Search")
        panel_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-bottom: 5px;")
        main_layout.addWidget(panel_title)
        
        # Search label
        self.label = QLabel("Search:")
        search_layout.addWidget(self.label)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term...")
        self.search_input.setMinimumWidth(200)  # Reduced min width for panel
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        
        # Loading indicator (initially hidden)
        self.loading_label = QLabel("🔍 Searching...")
        self.loading_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        self.loading_label.hide()
        search_layout.addWidget(self.loading_label)
        
        # Add search layout to main layout
        main_layout.addLayout(search_layout)
        
        # Results list (initially hidden)
        self.results_frame = QFrame()
        self.results_frame.setFrameStyle(QFrame.StyledPanel)
        self.results_frame.setLineWidth(1)
        self.results_frame.hide()
        
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(2, 2, 2, 2)
        
        # Results header
        self.results_label = QLabel("Search Results:")
        self.results_label.setStyleSheet("font-weight: bold; padding: 2px;")
        results_layout.addWidget(self.results_label)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(100)  # Minimum height for panel
        self.results_list.itemClicked.connect(self.on_result_clicked)
        results_layout.addWidget(self.results_list)
        
        # Close button for results
        close_layout = QHBoxLayout()
        self.close_results_label = QLabel('<a href="#" style="text-decoration: none; color: #666;">✕ Close</a>')
        self.close_results_label.setAlignment(Qt.AlignRight)
        self.close_results_label.linkActivated.connect(self.hide_results)
        close_layout.addStretch()
        close_layout.addWidget(self.close_results_label)
        results_layout.addLayout(close_layout)
        
        self.results_frame.setLayout(results_layout)
        main_layout.addWidget(self.results_frame)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
    def connect_signals(self):
        """Connect search engine signals."""
        self.search_engine.search_completed.connect(self.on_search_completed)
        self.search_engine.search_started.connect(self.on_search_started)
        self.search_engine.search_error.connect(self.on_search_error)
        self.search_engine.provider_search_started.connect(self.on_provider_search_started)
        
    def perform_search(self):
        """Perform search when Enter is pressed."""
        search_term = self.search_input.text().strip()
        if search_term:
            self.search_engine.search(search_term, self.iface)
        else:
            self.hide_results()
            
    def on_search_started(self, search_term):
        """Handle search started."""
        self.search_input.setStyleSheet("QLineEdit { background-color: #fff3cd; }")
        self.loading_label.setText(f"🔍 Searching for '{search_term}'...")
        self.loading_label.show()
        self.hide_results()
        
    def on_provider_search_started(self, provider_name, search_term):
        """Handle individual provider search started."""
        self.loading_label.setText(f"🔍 Searching {provider_name} for '{search_term}'...")
        self.loading_label.show()
        
    def on_search_completed(self, results):
        """Handle search completion and show results."""
        self.search_input.setStyleSheet("")  # Reset style
        self.loading_label.hide()
        self.current_results = results
        self.show_results(results)
        
    def on_search_error(self, error_message):
        """Handle search error."""
        self.search_input.setStyleSheet("QLineEdit { background-color: #f8d7da; }")
        self.loading_label.setText("❌ Search failed")
        # Hide loading after a delay to show error message briefly
        QTimer.singleShot(2000, self.loading_label.hide)
        self.hide_results()
        
    def show_results(self, results):
        """Show the results dropdown."""
        self.results_list.clear()
        
        if not results:
            # Show "No results" message
            item = QListWidgetItem("No results found")
            item.setData(Qt.UserRole, None)
            self.results_list.addItem(item)
            self.results_label.setText("Search Results: No matches")
        else:
            # Add results to list
            for i, result in enumerate(results):
                result_text = self.format_result_text(result)
                item = QListWidgetItem(result_text)
                item.setData(Qt.UserRole, i)  # Store result index
                item.setToolTip(self.format_result_tooltip(result))
                self.results_list.addItem(item)
            
            self.results_label.setText(f"Search Results: {len(results)} found")
        
        self.results_frame.show()
        
    def hide_results(self):
        """Hide the results dropdown."""
        self.results_frame.hide()
        self.current_results = []
        
    def format_result_text(self, result):
        """Format result text for display in list."""
        name = result.get("name", "Unknown")
        provider = result.get("provider", "")
        result_type = result.get("type", "")
        
        # Truncate long names
        if len(name) > 60:
            name = name[:57] + "..."
            
        if provider:
            return f"{name} ({provider})"
        else:
            return name
            
    def format_result_tooltip(self, result):
        """Format detailed tooltip for result."""
        lines = []
        lines.append(f"Name: {result.get('name', 'Unknown')}")
        lines.append(f"Provider: {result.get('provider', 'Unknown')}")
        lines.append(f"Type: {result.get('type', 'Unknown')}")
        
        # Add coordinate info if available
        if "geometry" in result:
            geom = result["geometry"]
            if isinstance(geom, dict) and "lat" in geom and "lon" in geom:
                # API-style geometry with lat/lon coordinates
                lines.append(f"Coordinates: {geom['lat']:.6f}, {geom['lon']:.6f}")
            elif hasattr(geom, 'centroid'):
                # QgsGeometry object from layer features
                try:
                    if isinstance(geom, QgsGeometry) and not geom.isEmpty():
                        centroid = geom.centroid().asPoint()
                        lines.append(f"Coordinates: {centroid.y():.6f}, {centroid.x():.6f}")
                except Exception:
                    pass  # Skip coordinate display if centroid calculation fails
                
        # Add bounding box info if available
        if "bbox" in result:
            bbox = result["bbox"]
            if len(bbox) >= 4:
                lines.append(f"Bounds: {bbox[0]:.4f}, {bbox[1]:.4f} to {bbox[2]:.4f}, {bbox[3]:.4f}")
                
        return "\n".join(lines)
        
    def on_result_clicked(self, item):
        """Handle result item click."""
        result_index = item.data(Qt.UserRole)
        if result_index is not None and 0 <= result_index < len(self.current_results):
            result = self.current_results[result_index]
            self.zoom_to_result(result)
            
            # Provide visual feedback for the clicked item
            # Highlight the selected item briefly
            item.setSelected(True)
            
            # Optionally, you could add a flash effect or change the item style
            # For now, just keep the selection to show which item was clicked
            
    def zoom_to_result(self, result):
        """Zoom to a specific search result."""
        try:
            canvas = self.iface.mapCanvas()
            
            if "bbox" in result:
                # Use bounding box if available
                # Expected bbox format: [west, south, east, north] in WGS84
                bbox = result["bbox"]
                if len(bbox) >= 4:
                    # Create rectangle from bbox: [west, south, east, north]
                    rect = QgsRectangle(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
                    
                    # Transform bbox if needed (assuming WGS84 input)
                    source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
                    dest_crs = canvas.mapSettings().destinationCrs()
                    
                    if source_crs != dest_crs:
                        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
                        rect = transform.transformBoundingBox(rect)
                    
                    canvas.setExtent(rect)
                    canvas.refresh()
                    return
                    
            if "geometry" in result:
                geometry = result["geometry"]
                if isinstance(geometry, dict) and "lat" in geometry and "lon" in geometry:
                    # Use point coordinates from API results
                    lat = float(geometry["lat"])
                    lon = float(geometry["lon"])
                    
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
                    return
                elif isinstance(geometry, QgsGeometry):
                    # Handle QgsGeometry from layer features  
                    bbox = geometry.boundingBox()
                    # Expand bbox slightly
                    bbox = bbox.buffered(bbox.width() * 0.1 if bbox.width() > 0 else 1000)
                    canvas.setExtent(bbox)
                    canvas.refresh()
                    return
                    
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error zooming to result: {str(e)}", 
                "Configurable Search", 
                Qgis.Warning
            )
            
    def refresh_config(self):
        """Refresh the widget when configuration changes."""
        self.hide_results()
