#!/usr/bin/env python3
"""
Tests for the CLI interface.
"""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from migration_tool.cli import cli, migrate, validate, batch, test_connection, generate_mapping, show_stats


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager."""
    with patch('migration_tool.cli.ConfigManager') as mock:
        config_instance = MagicMock()
        config_instance.config = {
            'altium_dblib_path': 'test.DbLib',
            'output_directory': 'output',
            'enable_parallel_processing': True,
            'max_worker_threads': 4,
            'batch_size': 1000,
            'enable_caching': True,
            'fuzzy_threshold': 0.7,
            'enable_ml_mapping': False,
            'validate_symbols': False,
            'validate_footprints': False,
            'create_views': True,
            'vacuum_database': True,
            'log_level': 'INFO'
        }
        config_instance.validate.return_value = {}
        mock.return_value = config_instance
        yield mock


@pytest.fixture
def mock_parser():
    """Mock AltiumDbLibParser."""
    with patch('migration_tool.cli.AltiumDbLibParser') as mock:
        parser_instance = MagicMock()
        parser_instance.parse_dblib_file.return_value = {
            'tables': {
                'Components': {
                    'required_fields': ['ComponentId', 'Name', 'Description']
                }
            }
        }
        parser_instance.extract_all_data.return_value = {
            'Components': {
                'data': [
                    {'ComponentId': 1, 'Name': 'Resistor', 'Description': 'Test resistor'},
                    {'ComponentId': 2, 'Name': 'Capacitor', 'Description': 'Test capacitor'}
                ]
            }
        }
        mock.return_value = parser_instance
        yield mock


@pytest.fixture
def mock_mapper():
    """Mock ComponentMappingEngine."""
    with patch('migration_tool.cli.ComponentMappingEngine') as mock:
        mapper_instance = MagicMock()
        mapper_instance.map_table_data.return_value = [
            MagicMock(confidence=0.9),
            MagicMock(confidence=0.6)
        ]
        mock.return_value = mapper_instance
        yield mock


@pytest.fixture
def mock_generator():
    """Mock KiCADDbLibGenerator."""
    with patch('migration_tool.cli.KiCADDbLibGenerator') as mock:
        generator_instance = MagicMock()
        generator_instance.generate.return_value = {
            'database_path': 'output/components.db',
            'dblib_path': 'output/components.kicad_dbl',
            'output_directory': 'output'
        }
        mock.return_value = generator_instance
        yield mock


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert 'version' in result.output.lower()


def test_migrate_command(runner, mock_config_manager, mock_parser, mock_mapper, mock_generator):
    """Test migrate command."""
    with tempfile.NamedTemporaryFile(suffix='.DbLib') as temp_file:
        result = runner.invoke(cli, [
            'migrate',
            temp_file.name,
            '--output-dir', 'output',
            '--parallel',
            '--threads', '4',
            '--batch-size', '1000',
            '--cache',
            '--fuzzy-threshold', '0.7',
            '--validate-symbols',
            '--create-views',
            '--optimize'
        ])
        
        assert result.exit_code == 0
        mock_parser.return_value.parse_dblib_file.assert_called_once()
        mock_parser.return_value.extract_all_data.assert_called_once()
        mock_mapper.return_value.map_table_data.assert_called_once()
        mock_generator.return_value.generate.assert_called_once()


def test_migrate_dry_run(runner, mock_config_manager, mock_parser, mock_mapper, mock_generator):
    """Test migrate command with dry run."""
    with tempfile.NamedTemporaryFile(suffix='.DbLib') as temp_file:
        result = runner.invoke(cli, [
            'migrate',
            temp_file.name,
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        mock_parser.return_value.parse_dblib_file.assert_called_once()
        mock_parser.return_value.extract_all_data.assert_called_once()
        mock_mapper.return_value.map_table_data.assert_called_once()
        mock_generator.return_value.generate.assert_not_called()


def test_validate_command(runner, mock_config_manager, mock_parser):
    """Test validate command."""
    with tempfile.NamedTemporaryFile(suffix='.DbLib') as temp_file:
        # Mock connection
        conn_mock = MagicMock()
        mock_parser.return_value.connect_to_database.return_value = conn_mock
        
        # Mock table_exists
        with patch('migration_tool.cli.table_exists', return_value=True):
            result = runner.invoke(cli, [
                'validate',
                temp_file.name
            ])
            
            assert result.exit_code == 0
            mock_parser.return_value.parse_dblib_file.assert_called_once()
            mock_parser.return_value.connect_to_database.assert_called_once()


def test_test_connection_command(runner, mock_config_manager, mock_parser):
    """Test test-connection command."""
    with tempfile.NamedTemporaryFile(suffix='.DbLib') as temp_file:
        # Mock connection
        conn_mock = MagicMock()
        mock_parser.return_value.connect_to_database.return_value = conn_mock
        
        # Mock execute_query
        with patch('migration_tool.cli.execute_query', return_value=[{'name': 'Components'}]):
            result = runner.invoke(cli, [
                'test-connection',
                temp_file.name
            ])
            
            assert result.exit_code == 0
            mock_parser.return_value.parse_dblib_file.assert_called_once()
            mock_parser.return_value.connect_to_database.assert_called_once()


def test_generate_mapping_command(runner):
    """Test generate-mapping command."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(cli, [
            'generate-mapping',
            '--output-dir', temp_dir,
            '--type', 'symbol'
        ])
        
        assert result.exit_code == 0
        assert os.path.exists(os.path.join(temp_dir, 'symbol_mapping_rules.yaml'))


def test_show_stats_command(runner):
    """Test show-stats command."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock report file
        report_path = os.path.join(temp_dir, 'migration_report.json')
        with open(report_path, 'w') as f:
            f.write('''{
                "migration_summary": {
                    "total_components": 100,
                    "high_confidence": 80,
                    "medium_confidence": 15,
                    "low_confidence": 5
                },
                "table_details": {
                    "Components": {
                        "component_count": 100,
                        "high_confidence": 80,
                        "medium_confidence": 15,
                        "low_confidence": 5
                    }
                }
            }''')
        
        result = runner.invoke(cli, [
            'show-stats',
            temp_dir
        ])
        
        assert result.exit_code == 0
        assert "Migration Statistics Report" in result.output


def test_batch_command(runner, mock_config_manager, mock_parser, mock_mapper, mock_generator):
    """Test batch command."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock DbLib file
        dblib_path = os.path.join(temp_dir, 'test.DbLib')
        with open(dblib_path, 'w') as f:
            f.write('mock dblib file')
        
        result = runner.invoke(cli, [
            'batch',
            temp_dir,
            '--output-dir', 'output',
            '--pattern', '*.DbLib',
            '--parallel'
        ])
        
        assert result.exit_code == 0


def test_config_generate_command(runner, mock_config_manager):
    """Test config generate command."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, 'config.yaml')
        
        mock_config_manager.return_value.generate_default_config.return_value = True
        
        result = runner.invoke(cli, [
            'config', 'generate',
            config_path
        ])
        
        assert result.exit_code == 0
        mock_config_manager.return_value.generate_default_config.assert_called_once_with(config_path)


def test_config_show_command(runner, mock_config_manager):
    """Test config show command."""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as temp_file:
        result = runner.invoke(cli, [
            'config', 'show',
            temp_file.name
        ])
        
        assert result.exit_code == 0
        mock_config_manager.assert_called_once_with(temp_file.name)


def test_config_validate_command(runner, mock_config_manager):
    """Test config validate command."""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as temp_file:
        # Valid config
        mock_config_manager.return_value.validate.return_value = {}
        
        result = runner.invoke(cli, [
            'config', 'validate',
            temp_file.name
        ])
        
        assert result.exit_code == 0
        assert "Configuration is valid" in result.output
        
        # Invalid config
        mock_config_manager.return_value.validate.return_value = {
            'altium_dblib_path': 'File not found'
        }
        
        result = runner.invoke(cli, [
            'config', 'validate',
            temp_file.name
        ])
        
        assert result.exit_code == 1
        assert "Configuration has issues" in result.output