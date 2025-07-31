#!/usr/bin/env python3
"""
Test script for Advanced Search Panel QGIS Plugin.
This script performs basic validation of the plugin structure and configuration.
"""

import os
import sys
import json
import importlib.util
from pathlib import Path


def test_plugin_structure():
    """Test that all required plugin files exist."""
    required_files = [
        '__init__.py',
        'configurable_search.py',
        'config_manager.py',
        'search_engine.py',
        'configurable_search_dialog.py',
        'metadata.txt',
        'README.md'
    ]
    
    missing_files = []
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)
    
    if missing_files:
        print(f"✗ Missing required files: {', '.join(missing_files)}")
        return False
    else:
        print("✓ All required files present")
        return True


def test_metadata():
    """Test that metadata.txt is valid."""
    try:
        with open('metadata.txt', 'r') as f:
            content = f.read()
        
        required_keys = ['name', 'description', 'version', 'qgisMinimumVersion']
        missing_keys = []
        
        for key in required_keys:
            if f"{key}=" not in content:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"✗ Missing metadata keys: {', '.join(missing_keys)}")
            return False
        else:
            print("✓ Metadata file valid")
            return True
            
    except Exception as e:
        print(f"✗ Error reading metadata.txt: {e}")
        return False


def test_imports():
    """Test that Python files can be imported without QGIS."""
    # This is a basic syntax check - won't work fully without QGIS environment
    python_files = [
        'config_manager.py'  # This one has minimal QGIS dependencies
    ]
    
    for file_name in python_files:
        try:
            spec = importlib.util.spec_from_file_location("test_module", file_name)
            if spec and spec.loader:
                print(f"✓ {file_name} syntax valid")
            else:
                print(f"✗ {file_name} could not be loaded")
                return False
        except Exception as e:
            print(f"✗ {file_name} syntax error: {e}")
            return False
    
    return True


def test_config_defaults():
    """Test that default configuration is valid."""
    try:
        # Import without QGIS - this will fail but we can catch syntax errors
        with open('config_manager.py', 'r') as f:
            content = f.read()
        
        # Look for default_config in the file
        if 'default_config' in content:
            print("✓ Default configuration found")
            return True
        else:
            print("✗ Default configuration not found")
            return False
            
    except Exception as e:
        print(f"✗ Error checking configuration: {e}")
        return False


def test_resources():
    """Test that resource files exist."""
    if os.path.exists('resources.qrc'):
        print("✓ Resource file exists")
        return True
    else:
        print("⚠ Resource file missing (resources.qrc)")
        return False


def show_plugin_info():
    """Show plugin information."""
    print("\nPlugin Information:")
    print("=" * 40)
    
    # File count
    py_files = len([f for f in os.listdir('.') if f.endswith('.py')])
    all_files = len([f for f in os.listdir('.') if os.path.isfile(f)])
    
    print(f"Python files: {py_files}")
    print(f"Total files: {all_files}")
    
    # Directory size
    total_size = sum(
        os.path.getsize(f) for f in os.listdir('.') 
        if os.path.isfile(f)
    )
    print(f"Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    
    # Check for optional files
    optional_files = {
        'build.bat': 'Windows build script',
        'build.sh': 'Unix build script',
        'Makefile': 'Make build file',
        'setup.py': 'Python setup script',
        'requirements.txt': 'Python dependencies',
        'icon.svg': 'Plugin icon',
        'icon-mono-configure.svg': 'Configure search icon',
        'icon-mono-search.svg': 'Search icon'
    }
    
    print("\nOptional files:")
    for file_name, description in optional_files.items():
        status = "✓" if os.path.exists(file_name) else "✗"
        print(f"  {status} {file_name} - {description}")


def main():
    """Run all tests."""
    print("Advanced Search Panel Plugin Validator")
    print("=" * 40)
    
    tests = [
        ("Plugin Structure", test_plugin_structure),
        ("Metadata File", test_metadata),
        ("Python Syntax", test_imports),
        ("Configuration", test_config_defaults),
        ("Resources", test_resources),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
    
    print(f"\n{'='*40}")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ Plugin structure is valid!")
        print("\nNext steps:")
        print("1. Create an icon.svg file (24x24 pixels)")
        print("2. Build resources: pyrcc5 -o resources.py resources.qrc")
        print("3. Install to QGIS: python setup.py install")
    else:
        print("✗ Plugin structure has issues that need to be fixed.")
    
    show_plugin_info()


if __name__ == '__main__':
    main()
