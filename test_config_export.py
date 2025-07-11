#!/usr/bin/env python3
"""Test configuration export functionality"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
if project_root not in sys.path:
    sys.path.insert(0, str(project_root))

from migration_tool.utils.config_manager import ConfigManager

print("Testing ConfigManager save functionality...")

# Create a test configuration
test_config = {
    'source_connection': {
        'connection_string': 'test_connection',
        'db_type': 'sqlite'
    },
    'target_settings': {
        'output_dir': '/test/output',
        'db_name': 'test_db',
        'lib_name': 'Test Library'
    },
    'mapping_rules': {
        'symbol': {'test': 'mapped'},
        'footprint': {},
        'category': {}
    },
    'confidence_threshold': 0.8
}

# Create ConfigManager instance
config_manager = ConfigManager()
config_manager.config = test_config

# Test saving to different formats
with tempfile.TemporaryDirectory() as tmpdir:
    # Test YAML export
    yaml_path = os.path.join(tmpdir, 'test_config.yaml')
    print(f"\nTesting YAML export to: {yaml_path}")
    
    try:
        success = config_manager.save_config(yaml_path)
        if success and os.path.exists(yaml_path):
            print("✓ YAML export successful")
            with open(yaml_path, 'r') as f:
                print("File contents preview:")
                print(f.read()[:200] + "...")
        else:
            print("✗ YAML export failed")
    except Exception as e:
        print(f"✗ YAML export error: {e}")
    
    # Test JSON export
    json_path = os.path.join(tmpdir, 'test_config.json')
    print(f"\nTesting JSON export to: {json_path}")
    
    try:
        success = config_manager.save_config(json_path)
        if success and os.path.exists(json_path):
            print("✓ JSON export successful")
            with open(json_path, 'r') as f:
                print("File contents preview:")
                print(f.read()[:200] + "...")
        else:
            print("✗ JSON export failed")
    except Exception as e:
        print(f"✗ JSON export error: {e}")

print("\n\nConfigManager save_config method signature check:")
print(f"Method expects {ConfigManager.save_config.__code__.co_argcount} arguments")
print(f"Argument names: {ConfigManager.save_config.__code__.co_varnames[:ConfigManager.save_config.__code__.co_argcount]}")