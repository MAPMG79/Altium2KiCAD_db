"""
Unit tests for the Configuration Manager module.
"""

import os
import pytest
import yaml
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from migration_tool.utils.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for the ConfigManager class."""

    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        config_manager = ConfigManager()
        
        # Check that default values are set
        assert config_manager.config is not None
        assert config_manager.config == ConfigManager.DEFAULT_CONFIG
        assert config_manager.get('output_directory') == 'output'
        assert config_manager.get('connection_timeout') == 30
        assert config_manager.get('enable_fuzzy_matching') is True
    
    def test_initialization_with_config_path(self, temp_dir):
        """Test initialization with a config path."""
        # Create a test config file
        config_path = os.path.join(temp_dir, 'test_config.yaml')
        test_config = {
            'output_directory': 'custom_output',
            'connection_timeout': 60
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Initialize with the config path
        config_manager = ConfigManager(config_path)
        
        # Check that values from the file are loaded
        assert config_manager.get('output_directory') == 'custom_output'
        assert config_manager.get('connection_timeout') == 60
        # Check that default values are preserved for unspecified settings
        assert config_manager.get('enable_fuzzy_matching') is True
    
    def test_load_config_yaml(self, temp_dir):
        """Test loading configuration from a YAML file."""
        config_path = os.path.join(temp_dir, 'test_config.yaml')
        test_config = {
            'output_directory': 'yaml_output',
            'connection_timeout': 45,
            'enable_fuzzy_matching': False
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        config_manager = ConfigManager()
        result = config_manager.load_config(config_path)
        
        # Check that values are loaded correctly
        assert result['output_directory'] == 'yaml_output'
        assert result['connection_timeout'] == 45
        assert result['enable_fuzzy_matching'] is False
        # Check that the config manager's state is updated
        assert config_manager.get('output_directory') == 'yaml_output'
        assert config_manager.get('connection_timeout') == 45
        assert config_manager.get('enable_fuzzy_matching') is False
    
    def test_load_config_json(self, temp_dir):
        """Test loading configuration from a JSON file."""
        config_path = os.path.join(temp_dir, 'test_config.json')
        test_config = {
            'output_directory': 'json_output',
            'connection_timeout': 50,
            'enable_ml_matching': True
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        config_manager = ConfigManager()
        result = config_manager.load_config(config_path)
        
        # Check that values are loaded correctly
        assert result['output_directory'] == 'json_output'
        assert result['connection_timeout'] == 50
        assert result['enable_ml_matching'] is True
        # Check that the config manager's state is updated
        assert config_manager.get('output_directory') == 'json_output'
        assert config_manager.get('connection_timeout') == 50
        assert config_manager.get('enable_ml_matching') is True
    
    def test_load_config_nonexistent_file(self):
        """Test loading configuration from a nonexistent file."""
        config_manager = ConfigManager()
        
        # Try to load a nonexistent file
        result = config_manager.load_config('nonexistent_config.yaml')
        
        # Check that default values are returned
        assert result == ConfigManager.DEFAULT_CONFIG
        # Check that the config manager's state is unchanged
        assert config_manager.config == ConfigManager.DEFAULT_CONFIG
    
    def test_load_config_unsupported_format(self, temp_dir):
        """Test loading configuration from an unsupported file format."""
        config_path = os.path.join(temp_dir, 'test_config.txt')
        
        with open(config_path, 'w') as f:
            f.write('output_directory: text_output\n')
        
        config_manager = ConfigManager()
        result = config_manager.load_config(config_path)
        
        # Check that default values are returned
        assert result == ConfigManager.DEFAULT_CONFIG
        # Check that the config manager's state is unchanged
        assert config_manager.config == ConfigManager.DEFAULT_CONFIG
    
    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading configuration from an invalid YAML file."""
        config_path = os.path.join(temp_dir, 'invalid_config.yaml')
        
        with open(config_path, 'w') as f:
            f.write('invalid: yaml: content:\n  - missing colon\n')
        
        config_manager = ConfigManager()
        result = config_manager.load_config(config_path)
        
        # Check that default values are returned
        assert result == ConfigManager.DEFAULT_CONFIG
        # Check that the config manager's state is unchanged
        assert config_manager.config == ConfigManager.DEFAULT_CONFIG
    
    def test_load_config_invalid_json(self, temp_dir):
        """Test loading configuration from an invalid JSON file."""
        config_path = os.path.join(temp_dir, 'invalid_config.json')
        
        with open(config_path, 'w') as f:
            f.write('{"invalid": "json", missing: "quotes"}')
        
        config_manager = ConfigManager()
        result = config_manager.load_config(config_path)
        
        # Check that default values are returned
        assert result == ConfigManager.DEFAULT_CONFIG
        # Check that the config manager's state is unchanged
        assert config_manager.config == ConfigManager.DEFAULT_CONFIG
    
    def test_save_config_yaml(self, temp_dir):
        """Test saving configuration to a YAML file."""
        config_path = os.path.join(temp_dir, 'output_config.yaml')
        
        config_manager = ConfigManager()
        config_manager.set('output_directory', 'custom_output')
        config_manager.set('connection_timeout', 60)
        
        result = config_manager.save_config(config_path)
        
        # Check that the save operation was successful
        assert result is True
        # Check that the file was created
        assert os.path.exists(config_path)
        
        # Check file contents
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        assert loaded_config['output_directory'] == 'custom_output'
        assert loaded_config['connection_timeout'] == 60
    
    def test_save_config_json(self, temp_dir):
        """Test saving configuration to a JSON file."""
        config_path = os.path.join(temp_dir, 'output_config.json')
        
        config_manager = ConfigManager()
        config_manager.set('output_directory', 'custom_output')
        config_manager.set('connection_timeout', 60)
        
        result = config_manager.save_config(config_path)
        
        # Check that the save operation was successful
        assert result is True
        # Check that the file was created
        assert os.path.exists(config_path)
        
        # Check file contents
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
        
        assert loaded_config['output_directory'] == 'custom_output'
        assert loaded_config['connection_timeout'] == 60
    
    def test_save_config_unsupported_format(self, temp_dir):
        """Test saving configuration to an unsupported file format."""
        config_path = os.path.join(temp_dir, 'output_config.txt')
        
        config_manager = ConfigManager()
        result = config_manager.save_config(config_path)
        
        # Check that the save operation failed
        assert result is False
        # The file might be created but should be empty or invalid
    
    def test_save_config_create_directory(self, temp_dir):
        """Test saving configuration to a file in a nonexistent directory."""
        config_path = os.path.join(temp_dir, 'new_dir', 'output_config.yaml')
        
        config_manager = ConfigManager()
        result = config_manager.save_config(config_path)
        
        # Check that the save operation was successful
        assert result is True
        # Check that the directory and file were created
        assert os.path.exists(config_path)
    
    def test_save_config_permission_error(self, temp_dir):
        """Test saving configuration with insufficient permissions."""
        config_path = os.path.join(temp_dir, 'output_config.yaml')
        
        # Mock the open function to raise a permission error
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            config_manager = ConfigManager()
            result = config_manager.save_config(config_path)
            
            # Check that the save operation failed
            assert result is False
    
    def test_get_existing_key(self):
        """Test getting an existing configuration value."""
        config_manager = ConfigManager()
        
        # Get an existing key
        value = config_manager.get('output_directory')
        
        # Check that the correct value is returned
        assert value == 'output'
    
    def test_get_nonexistent_key(self):
        """Test getting a nonexistent configuration value."""
        config_manager = ConfigManager()
        
        # Get a nonexistent key with no default
        value = config_manager.get('nonexistent_key')
        
        # Check that None is returned
        assert value is None
    
    def test_get_with_default(self):
        """Test getting a configuration value with a default."""
        config_manager = ConfigManager()
        
        # Get a nonexistent key with a default
        value = config_manager.get('nonexistent_key', 'default_value')
        
        # Check that the default value is returned
        assert value == 'default_value'
    
    def test_set_new_key(self):
        """Test setting a new configuration value."""
        config_manager = ConfigManager()
        
        # Set a new key
        config_manager.set('new_key', 'new_value')
        
        # Check that the key was added
        assert 'new_key' in config_manager.config
        assert config_manager.get('new_key') == 'new_value'
    
    def test_set_existing_key(self):
        """Test setting an existing configuration value."""
        config_manager = ConfigManager()
        
        # Set an existing key
        config_manager.set('output_directory', 'new_output')
        
        # Check that the value was updated
        assert config_manager.get('output_directory') == 'new_output'
    
    def test_update_with_dict(self):
        """Test updating configuration with a dictionary."""
        config_manager = ConfigManager()
        
        # Update with a dictionary
        update_dict = {
            'output_directory': 'updated_output',
            'connection_timeout': 75,
            'new_key': 'new_value'
        }
        config_manager.update(update_dict)
        
        # Check that values were updated
        assert config_manager.get('output_directory') == 'updated_output'
        assert config_manager.get('connection_timeout') == 75
        assert config_manager.get('new_key') == 'new_value'
        # Check that other values are unchanged
        assert config_manager.get('enable_fuzzy_matching') is True
    
    def test_validate_valid_config(self, temp_dir):
        """Test validating a valid configuration."""
        # Create a valid Altium DbLib file
        altium_dblib_path = os.path.join(temp_dir, 'valid.DbLib')
        with open(altium_dblib_path, 'w') as f:
            f.write('Mock Altium DbLib file')
        
        config_manager = ConfigManager()
        config_manager.set('altium_dblib_path', altium_dblib_path)
        config_manager.set('output_directory', 'valid_output')
        
        issues = config_manager.validate()
        
        # Check that no issues were found
        assert not issues
    
    def test_validate_missing_required_paths(self):
        """Test validating a configuration with missing required paths."""
        config_manager = ConfigManager()
        config_manager.set('altium_dblib_path', '')
        config_manager.set('output_directory', '')
        
        issues = config_manager.validate()
        
        # Check that issues were found
        assert 'altium_dblib_path' in issues
        assert 'output_directory' in issues
    
    def test_validate_nonexistent_altium_dblib(self):
        """Test validating a configuration with a nonexistent Altium DbLib file."""
        config_manager = ConfigManager()
        config_manager.set('altium_dblib_path', 'nonexistent.DbLib')
        
        issues = config_manager.validate()
        
        # Check that an issue was found
        assert 'altium_dblib_path' in issues
        assert 'File not found' in issues['altium_dblib_path']
    
    def test_validate_invalid_numeric_values(self):
        """Test validating a configuration with invalid numeric values."""
        config_manager = ConfigManager()
        config_manager.set('connection_timeout', -10)
        config_manager.set('fuzzy_threshold', 2.0)
        config_manager.set('max_worker_threads', 0)
        
        issues = config_manager.validate()
        
        # Check that issues were found
        assert 'connection_timeout' in issues
        assert 'fuzzy_threshold' in issues
        assert 'max_worker_threads' in issues
    
    def test_generate_default_config(self, temp_dir):
        """Test generating a default configuration file."""
        config_path = os.path.join(temp_dir, 'default_config.yaml')
        
        config_manager = ConfigManager()
        result = config_manager.generate_default_config(config_path)
        
        # Check that the operation was successful
        assert result is True
        # Check that the file was created
        assert os.path.exists(config_path)
        
        # Check file contents
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        # Check that all default values are present
        for key, value in ConfigManager.DEFAULT_CONFIG.items():
            assert key in loaded_config
            assert loaded_config[key] == value