#!/usr/bin/env python3
"""
Setup script for Advanced Search Panel QGIS Plugin development.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def get_qgis_plugin_dir(qgis_profile='QGIS3'):
    """Get the QGIS plugins directory for the current OS.
    
    Args:
        qgis_profile: QGIS profile name (default: 'QGIS3')
    """
    if sys.platform.startswith('win'):
        # Windows
        appdata = os.environ.get('APPDATA', '')
        return Path(appdata) / 'QGIS' / qgis_profile / 'profiles' / 'default' / 'python' / 'plugins'
    elif sys.platform.startswith('darwin'):
        # macOS
        return Path.home() / 'Library' / 'Application Support' / 'QGIS' / qgis_profile / 'profiles' / 'default' / 'python' / 'plugins'
    else:
        # Linux
        return Path.home() / '.local' / 'share' / 'QGIS' / qgis_profile / 'profiles' / 'default' / 'python' / 'plugins'


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


def install_plugin(qgis_profile='QGIS3'):
    """Install the plugin to QGIS plugins directory.
    
    Args:
        qgis_profile: QGIS profile name (default: 'QGIS3')
    """
    plugin_dir = get_qgis_plugin_dir(qgis_profile) / 'advanced_search_panel'
    
    print(f"Installing plugin to: {plugin_dir}")
    print(f"  QGIS Profile: {qgis_profile}")
    
    # Create plugin directory
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy plugin files
    files_to_copy = [
        '*.py',
        '*.svg',
        'metadata.txt',
        'README.md',
        'requirements.txt',
        'resources.qrc',
        'example_export.json'
    ]
    
    # Directories to copy recursively
    dirs_to_copy = [
        'help'
    ]
    
    import glob
    copied_files = 0
    
    # Copy individual files
    for pattern in files_to_copy:
        for file_path in glob.glob(pattern):
            if os.path.isfile(file_path):
                shutil.copy2(file_path, plugin_dir)
                copied_files += 1
                print(f"  Copied: {file_path}")
    
    # Copy directories recursively
    for dir_name in dirs_to_copy:
        source_dir = Path(dir_name)
        if source_dir.exists() and source_dir.is_dir():
            dest_dir = plugin_dir / dir_name
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(source_dir, dest_dir)
            print(f"  Copied directory: {dir_name}/")
            # Count files in directory
            dir_files = sum(1 for _ in dest_dir.rglob('*') if _.is_file())
            copied_files += dir_files
    
    print(f"✓ Plugin installed ({copied_files} files copied)")
    print(f"  Location: {plugin_dir}")
    return True


def verify_installation(qgis_profile='QGIS3'):
    """Verify that the plugin is properly installed.
    
    Args:
        qgis_profile: QGIS profile name (default: 'QGIS3')
    """
    plugin_dir = get_qgis_plugin_dir(qgis_profile) / 'advanced_search_panel'
    
    if not plugin_dir.exists():
        print("✗ Plugin directory not found")
        return False
    
    # Check essential files
    essential_files = [
        '__init__.py',
        'configurable_search.py',
        'metadata.txt'
    ]
    
    missing_files = []
    for file_name in essential_files:
        if not (plugin_dir / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"✗ Missing essential files: {', '.join(missing_files)}")
        return False
    
    # Check help documentation
    help_dir = plugin_dir / 'help'
    if help_dir.exists():
        help_index = help_dir / 'source' / 'index.html'
        if help_index.exists():
            print("✓ Help documentation installed")
        else:
            print("⚠ Help directory exists but index.html missing")
    else:
        print("⚠ Help documentation not installed")
    
    print("✓ Plugin installation verified")
    return True


def create_development_link(qgis_profile='QGIS3'):
    """Create a symbolic link for development.
    
    Args:
        qgis_profile: QGIS profile name (default: 'QGIS3')
    """
    plugin_dir = get_qgis_plugin_dir(qgis_profile) / 'advanced_search_panel'
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
        return install_plugin(qgis_profile)


def parse_arguments():
    """Parse command line arguments."""
    qgis_profile = 'QGIS3'  # Default profile
    
    # Look for --profile argument
    for i, arg in enumerate(sys.argv):
        if arg == '--profile' and i + 1 < len(sys.argv):
            qgis_profile = sys.argv[i + 1]
            # Remove profile arguments from sys.argv
            sys.argv.pop(i + 1)
            sys.argv.pop(i)
            break
    
    return qgis_profile


def main():
    """Main setup function."""
    # Parse profile argument first
    qgis_profile = parse_arguments()
    
    if len(sys.argv) < 2:
        print("Advanced Search Panel QGIS Plugin Setup")
        print("")
        print("Usage:")
        print("  python setup.py build                    - Build resources")
        print("  python setup.py install [--profile NAME] - Install plugin")
        print("  python setup.py dev [--profile NAME]     - Setup development environment")
        print("  python setup.py verify [--profile NAME]  - Verify plugin installation")
        print("  python setup.py info [--profile NAME]    - Show plugin information")
        print("")
        print("Options:")
        print("  --profile NAME   Specify QGIS profile (default: QGIS3)")
        return
    
    command = sys.argv[1]
    
    if command == 'build':
        build_resources()
    
    elif command == 'install':
        build_resources()
        install_plugin(qgis_profile)
        verify_installation(qgis_profile)
        print("")
        print("Plugin installed successfully!")
        print(f"  QGIS Profile: {qgis_profile}")
        print("Restart QGIS and enable the plugin in the Plugin Manager or use the Plugin Reloader plugin to see the changes.")
    
    elif command == 'dev':
        build_resources()
        create_development_link(qgis_profile)
        verify_installation(qgis_profile)
        print("")
        print("Development environment setup complete!")
        print(f"  QGIS Profile: {qgis_profile}")
        print("Changes to the plugin files will be reflected immediately in QGIS.")
        print("Restart QGIS to load the plugin.")
    
    elif command == 'verify':
        verify_installation(qgis_profile)
    
    elif command == 'info':
        plugin_dir = get_qgis_plugin_dir(qgis_profile)
        print("Advanced Search Panel QGIS Plugin")
        print("=" * 40)
        print(f"QGIS Profile: {qgis_profile}")
        print(f"Current directory: {Path.cwd()}")
        print(f"QGIS plugins directory: {plugin_dir}")
        print(f"Plugin directory: {plugin_dir / 'advanced_search_panel'}")
        print(f"Plugin exists: {(plugin_dir / 'advanced_search_panel').exists()}")
        
        # Count files in current directory
        import glob
        py_files = len(glob.glob('*.py'))
        total_files = len(glob.glob('*.*'))
        print(f"Source Python files: {py_files}")
        print(f"Source total files: {total_files}")
        
        # Check help documentation
        help_dir = Path('help')
        if help_dir.exists():
            help_files = sum(1 for _ in help_dir.rglob('*') if _.is_file())
            print(f"Help documentation files: {help_files}")
        else:
            print("Help documentation: Not found")
        
        # Check installed plugin
        installed_plugin = plugin_dir / 'advanced_search_panel'
        if installed_plugin.exists():
            installed_files = sum(1 for _ in installed_plugin.rglob('*') if _.is_file())
            print(f"Installed plugin files: {installed_files}")
            
            # Check if help is installed
            installed_help = installed_plugin / 'help'
            if installed_help.exists():
                installed_help_files = sum(1 for _ in installed_help.rglob('*') if _.is_file())
                print(f"Installed help files: {installed_help_files}")
            else:
                print("Installed help files: 0 (not installed)")
        else:
            print("Installed plugin files: 0 (not installed)")
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python setup.py' for usage information.")


if __name__ == '__main__':
    main()
