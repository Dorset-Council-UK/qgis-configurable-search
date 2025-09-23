"""
Help system integration for Advanced Search Panel plugin.

This module provides functions to open help documentation from within QGIS.
"""

import os
import webbrowser
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsMessageLog, Qgis


def show_help():
    """Show the plugin help documentation."""
    help_file = get_help_file()
        
    if help_file and os.path.exists(help_file):
        # Try to open with QDesktopServices first (integrates better with QGIS)
        url = QUrl.fromLocalFile(help_file)
        if not QDesktopServices.openUrl(url):
            # Fallback to webbrowser module
            webbrowser.open(f"file://{help_file}")
    else:
        # Fallback to online documentation or show error
        show_help_not_found()


def get_help_file():
    """Get the path to the main help file."""
    plugin_dir = os.path.dirname(__file__)
    help_file = os.path.join(plugin_dir, "help", "source", "index.html")
    return help_file


def show_help_not_found():
    """Show message when help file is not found."""
    
    help_file = get_help_file()
    plugin_dir = os.path.dirname(__file__)
    
    msg = (
        f"Help documentation not found at expected location:\n"
        f"{help_file}\n\n"
        f"Plugin directory: {plugin_dir}\n\n"
        f"Please check the plugin installation or visit the online documentation:\n"
        f"https://github.com/Dorset-Council-UK/qgis-configurable-search"
    )
    
    QMessageBox.information(None, "Help Not Found", msg)
    QgsMessageLog.logMessage(
        f"Help documentation not found at: {help_file}",
        "Advanced Search Panel",
        Qgis.Warning
    )