#!/usr/bin/env python3
"""
Tests for the Configuration Manager utility module.
"""

import os
import unittest
import tempfile
from unittest.mock import patch, mock_open

from migration_tool.utils.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for the ConfigManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = self.temp_dir.name
        
        # Sample test configuration
        self.test_config = {
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': None
            },
            'database': {
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 2
            },
            'migration': {
                'create_component_views': True,
                'include_confidence_scores': True,
                'validate_symbols': False,
                'batch_size': 1000,
                'min_confidence': 50
            }
        }
        
        # Create a test config file
        self.config_path = os.path.join(self.config_dir, 'test_config.yaml')
        with open(self.config_path, 'w') as f:
            f.write("""
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null

database:
  timeout: 30
  max_retries: 3
  retry_delay: 2

migration:
  create_component_views: true
  include_confidence_scores: true
  validate_symbols: false
  batch_size: 1000
  min_confidence: 50
""")

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of the config manager."""
        config_manager = ConfigManager()
        self.assertIsInstance(config_manager, ConfigManager)
        self.assertEqual(config_manager.config, {})

    def test_load_config(self):
        """Test loading configuration from a file."""
        config_manager = ConfigManager()
        config = config_manager.load_config(self.config_path)
        
        self.assertIsNotNone(config)
        self.assertIn('logging', config)
        self.assertIn('database', config)
        self.assertIn('migration', config)
        self.assertEqual(config['logging']['level'], 'INFO')
        self.assertEqual(config['database']['timeout'], 30)
        self.assertEqual(config['migration']['batch_size'], 1000)

    def test_load_default_config(self):
        """Test loading default configuration."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('builtins.open', mock_open(read_data="""
logging:
  level: DEBUG
  format: "%(asctime)s - %(levelname)s - %(message)s"
  file: "logs/migration.log"
""")):
                config_manager = ConfigManager()
                config = config_manager.load_default_config()
                
                self.assertIsNotNone(config)
                self.assertIn('logging', config)
                self.assertEqual(config['logging']['level'], 'DEBUG')

    def test_merge_configs(self):
        """Test merging of configurations."""
        config_manager = ConfigManager()
        
        # Base config
        base_config = {
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'file': None
            },
            'database': {
                'timeout': 30
            }
        }
        
        # Override config
        override_config = {
            'logging': {
                'level': 'DEBUG',
                'file': 'logs/debug.log'
            },
            'migration': {
                'batch_size': 500
            }
        }
        
        # Merge configs
        merged_config = config_manager.merge_configs(base_config, override_config)
        
        # Check merged result
        self.assertEqual(merged_config['logging']['level'], 'DEBUG')  # Overridden
        self.assertEqual(merged_config['logging']['format'], '%(asctime)s - %(levelname)s - %(message)s')  # From base
        self.assertEqual(merged_config['logging']['file'], 'logs/debug.log')  # Overridden
        self.assertEqual(merged_config['database']['timeout'], 30)  # From base
        self.assertEqual(merged_config['migration']['batch_size'], 500)  # From override

    def test_validate_config(self):
        """Test validation of configuration."""
        config_manager = ConfigManager()
        
        # Valid config
        valid_config = self.test_config.copy()
        result = config_manager.validate_config(valid_config)
        self.assertTrue(result)
        
        # Invalid config (missing required field)
        invalid_config = self.test_config.copy()
        del invalid_config['logging']['level']
        
        with self.assertRaises(ValueError):
            config_manager.validate_config(invalid_config)
        
        # Invalid config (wrong type)
        invalid_config = self.test_config.copy()
        invalid_config['database']['timeout'] = 'not_an_integer'
        
        with self.assertRaises(TypeError):
            config_manager.validate_config(invalid_config)

    def test_get_config_value(self):
        """Test getting a value from the configuration."""
        config_manager = ConfigManager()
        config_manager.config = self.test_config.copy()
        
        # Get existing value
        value = config_manager.get_config_value('logging.level')
        self.assertEqual(value, 'INFO')
        
        # Get nested value
        value = config_manager.get_config_value('migration.batch_size')
        self.assertEqual(value, 1000)
        
        # Get non-existent value with default
        value = config_manager.get_config_value('non.existent.key', default='default_value')
        self.assertEqual(value, 'default_value')
        
        # Get non-existent value without default
        with self.assertRaises(KeyError):
            config_manager.get_config_value('non.existent.key')

    def test_set_config_value(self):
        """Test setting a value in the configuration."""
        config_manager = ConfigManager()
        config_manager.config = self.test_config.copy()
        
        # Set existing value
        config_manager.set_config_value('logging.level', 'DEBUG')
        self.assertEqual(config_manager.config['logging']['level'], 'DEBUG')
        
        # Set nested value
        config_manager.set_config_value('migration.batch_size', 2000)
        self.assertEqual(config_manager.config['migration']['batch_size'], 2000)
        
        # Set new value
        config_manager.set_config_value('new.key', 'new_value')
        self.assertEqual(config_manager.config['new']['key'], 'new_value')

    def test_save_config(self):
        """Test saving configuration to a file."""
        config_manager = ConfigManager()
        config_manager.config = self.test_config.copy()
        
        # Save to a new file
        save_path = os.path.join(self.config_dir, 'saved_config.yaml')
        config_manager.save_config(save_path)
        
        # Check if file exists
        self.assertTrue(os.path.exists(save_path))
        
        # Load the saved file and verify content
        loaded_config = ConfigManager().load_config(save_path)
        self.assertEqual(loaded_config['logging']['level'], 'INFO')
        self.assertEqual(loaded_config['database']['timeout'], 30)
        self.assertEqual(loaded_config['migration']['batch_size'], 1000)


if __name__ == '__main__':
    unittest.main()