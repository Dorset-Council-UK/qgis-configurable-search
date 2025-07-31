#!/usr/bin/env python3
"""
Setup script for Advanced Search Panel QGIS Plugin development.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def get_qgis_plugin_dir():
    """Get the QGIS plugins directory for the current OS."""
    if sys.platform.startswith('win'):
        # Windows
        appdata = os.environ.get('APPDATA', '')
        return Path(appdata) / 'QGIS' / 'QGIS3' / 'profiles' / 'default' / 'python' / 'plugins'
    elif sys.platform.startswith('darwin'):
        # macOS
        return Path.home() / 'Library' / 'Application Support' / 'QGIS' / 'QGIS3' / 'profiles' / 'default' / 'python' / 'plugins'
    else:
        # Linux
        return Path.home() / '.local' / 'share' / 'QGIS' / 'QGIS3' / 'profiles' / 'default' / 'python' / 'plugins'


def build_resources():
    """Build the Qt resources file."""
    print("Building Qt resources...")
    try:
        subprocess.run(['pyrcc5', '-o', 'resources.py', 'resources.qrc'], check=True)
        print("✓ Resources built successfully")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Warning: Could not build resources. pyrcc5 not found.")
        print("  Install with: pip install PyQt5-tools")
        return False


def install_plugin():
    """Install the plugin to QGIS plugins directory."""
    plugin_dir = get_qgis_plugin_dir() / 'advanced_search_panel'
    
    print(f"Installing plugin to: {plugin_dir}")
    
    # Create plugin directory
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy plugin files
    files_to_copy = [
        '*.py',
        '*.svg',
        'metadata.txt',
        'README.md',
        'requirements.txt',
        'resources.qrc'
    ]
    
    import glob
    copied_files = 0
    
    for pattern in files_to_copy:
        for file_path in glob.glob(pattern):
            if os.path.isfile(file_path):
                shutil.copy2(file_path, plugin_dir)
                copied_files += 1
                print(f"  Copied: {file_path}")
    
    print(f"✓ Plugin installed ({copied_files} files copied)")
    print(f"  Location: {plugin_dir}")
    return True


def create_development_link():
    """Create a symbolic link for development."""
    plugin_dir = get_qgis_plugin_dir() / 'advanced_search_panel'
    current_dir = Path.cwd()
    
    if plugin_dir.exists():
        if plugin_dir.is_symlink():
            print(f"Development link already exists: {plugin_dir}")
            return True
        else:
            print(f"Removing existing plugin directory: {plugin_dir}")
            shutil.rmtree(plugin_dir)
    
    try:
        plugin_dir.parent.mkdir(parents=True, exist_ok=True)
        plugin_dir.symlink_to(current_dir)
        print(f"✓ Development link created: {plugin_dir} -> {current_dir}")
        return True
    except OSError as e:
        print(f"✗ Could not create symbolic link: {e}")
        print("  Falling back to file copy...")
        return install_plugin()


def main():
    """Main setup function."""
    if len(sys.argv) < 2:
        print("Advanced Search Panel QGIS Plugin Setup")
        print("")
        print("Usage:")
        print("  python setup.py build       - Build resources")
        print("  python setup.py install     - Install plugin")
        print("  python setup.py dev         - Setup development environment")
        print("  python setup.py info        - Show plugin information")
        return
    
    command = sys.argv[1]
    
    if command == 'build':
        build_resources()
    
    elif command == 'install':
        build_resources()
        install_plugin()
        print("")
        print("Plugin installed successfully!")
        print("Restart QGIS and enable the plugin in the Plugin Manager.")
    
    elif command == 'dev':
        build_resources()
        create_development_link()
        print("")
        print("Development environment setup complete!")
        print("Changes to the plugin files will be reflected immediately in QGIS.")
        print("Restart QGIS to load the plugin.")
    
    elif command == 'info':
        plugin_dir = get_qgis_plugin_dir()
        print("Advanced Search Panel QGIS Plugin")
        print("=" * 40)
        print(f"Current directory: {Path.cwd()}")
        print(f"QGIS plugins directory: {plugin_dir}")
        print(f"Plugin directory: {plugin_dir / 'advanced_search_panel'}")
        print(f"Plugin exists: {(plugin_dir / 'advanced_search_panel').exists()}")
        
        # Count files
        import glob
        py_files = len(glob.glob('*.py'))
        total_files = len(glob.glob('*.*'))
        print(f"Python files: {py_files}")
        print(f"Total files: {total_files}")
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python setup.py' for usage information.")


if __name__ == '__main__':
    main()
