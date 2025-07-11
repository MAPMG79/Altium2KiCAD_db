#!/usr/bin/env python3
"""
Tests for the GUI interface.
"""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import GUI components
from migration_tool.gui import (
    LoggingHandler,
    MigrationProgressDialog,
    DatabaseConnectionDialog,
    MappingRuleDialog,
    BatchProcessDialog,
    HelpDialog,
    AltiumToKiCADMigrationApp
)


@pytest.fixture
def mock_tk():
    """Mock tkinter."""
    with patch('migration_tool.gui.tk') as mock:
        # Mock Tk root
        root_mock = MagicMock()
        mock.Tk.return_value = root_mock
        
        # Mock widgets
        mock.Label = MagicMock()
        mock.Button = MagicMock()
        mock.Entry = MagicMock()
        mock.Text = MagicMock()
        mock.Frame = MagicMock()
        mock.StringVar = MagicMock()
        mock.BooleanVar = MagicMock()
        mock.Listbox = MagicMock()
        mock.END = 'end'
        mock.SUNKEN = 'sunken'
        mock.W = 'w'
        mock.X = 'x'
        mock.Y = 'y'
        mock.BOTH = 'both'
        mock.LEFT = 'left'
        mock.RIGHT = 'right'
        mock.TOP = 'top'
        mock.BOTTOM = 'bottom'
        
        yield mock


@pytest.fixture
def mock_ttk():
    """Mock ttk."""
    with patch('migration_tool.gui.ttk') as mock:
        mock.Frame = MagicMock()
        mock.Label = MagicMock()
        mock.Button = MagicMock()
        mock.Entry = MagicMock()
        mock.Notebook = MagicMock()
        mock.Treeview = MagicMock()
        mock.Scrollbar = MagicMock()
        mock.Progressbar = MagicMock()
        mock.LabelFrame = MagicMock()
        mock.Checkbutton = MagicMock()
        mock.Radiobutton = MagicMock()
        mock.Combobox = MagicMock()
        mock.Spinbox = MagicMock()
        
        yield mock


@pytest.fixture
def mock_filedialog():
    """Mock filedialog."""
    with patch('migration_tool.gui.filedialog') as mock:
        mock.askopenfilename.return_value = '/path/to/file.DbLib'
        mock.askopenfilenames.return_value = ['/path/to/file1.DbLib', '/path/to/file2.DbLib']
        mock.askdirectory.return_value = '/path/to/directory'
        mock.asksaveasfilename.return_value = '/path/to/save/file.yaml'
        
        yield mock


@pytest.fixture
def mock_messagebox():
    """Mock messagebox."""
    with patch('migration_tool.gui.messagebox') as mock:
        mock.showinfo.return_value = 'ok'
        mock.showwarning.return_value = 'ok'
        mock.showerror.return_value = 'ok'
        
        yield mock


@pytest.fixture
def mock_scrolledtext():
    """Mock scrolledtext."""
    with patch('migration_tool.gui.scrolledtext') as mock:
        text_mock = MagicMock()
        mock.ScrolledText.return_value = text_mock
        
        yield mock


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager."""
    with patch('migration_tool.gui.ConfigManager') as mock:
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
    with patch('migration_tool.gui.AltiumDbLibParser') as mock:
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
    with patch('migration_tool.gui.ComponentMappingEngine') as mock:
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
    with patch('migration_tool.gui.KiCADDbLibGenerator') as mock:
        generator_instance = MagicMock()
        generator_instance.generate.return_value = {
            'database_path': 'output/components.db',
            'dblib_path': 'output/components.kicad_dbl',
            'output_directory': 'output'
        }
        mock.return_value = generator_instance
        yield mock


@pytest.fixture
def mock_logging():
    """Mock logging."""
    with patch('migration_tool.gui.logging') as mock:
        logger_mock = MagicMock()
        mock.getLogger.return_value = logger_mock
        mock.Handler = MagicMock
        mock.Formatter = MagicMock()
        mock.DEBUG = 10
        mock.INFO = 20
        mock.WARNING = 30
        mock.ERROR = 40
        mock.CRITICAL = 50
        
        yield mock


@pytest.fixture
def mock_setup_logging():
    """Mock setup_logging."""
    with patch('migration_tool.gui.setup_logging') as mock:
        logger_mock = MagicMock()
        mock.return_value = logger_mock
        
        yield mock


def test_logging_handler(mock_tk, mock_logging):
    """Test LoggingHandler class."""
    text_widget = mock_tk.Text()
    handler = LoggingHandler(text_widget)
    
    # Create a log record
    record = MagicMock()
    record.getMessage.return_value = "Test log message"
    handler.format = MagicMock(return_value="Formatted: Test log message")
    
    # Test emit method
    handler.emit(record)
    
    # Verify text widget was updated
    text_widget.after.assert_called_once()


def test_migration_progress_dialog(mock_tk, mock_ttk):
    """Test MigrationProgressDialog class."""
    parent = mock_tk.Tk()
    dialog = MigrationProgressDialog(parent)
    
    # Test update_status method
    dialog.update_status("Processing components")
    dialog.status_label.config.assert_called_with(text="Processing components")
    
    # Test update_task_progress method
    dialog.update_task_progress(50, 100)
    assert dialog.task_progress['value'] == 50
    assert dialog.task_progress['maximum'] == 100
    
    # Test log_message method
    dialog.log_message("Test log message")
    dialog.log_text.configure.assert_called()
    
    # Test cancel method
    dialog.cancel()
    assert dialog.cancelled is True
    
    # Test close method
    dialog.close()
    dialog.progress.stop.assert_called_once()
    dialog.window.destroy.assert_called_once()


def test_database_connection_dialog(mock_tk, mock_ttk, mock_filedialog):
    """Test DatabaseConnectionDialog class."""
    parent = mock_tk.Tk()
    dialog = DatabaseConnectionDialog(parent)
    
    # Test update_connection_form method
    dialog.db_type.get.return_value = "sqlite"
    dialog.update_connection_form()
    dialog.sqlite_frame.pack.assert_called_once()
    
    # Test build_connection_string method
    dialog.sqlite_path.get.return_value = "/path/to/database.db"
    conn_str = dialog.build_connection_string()
    assert conn_str == "sqlite:///path/to/database.db"
    
    # Test browse_sqlite_file method
    dialog.browse_sqlite_file()
    mock_filedialog.askopenfilename.assert_called_once()
    dialog.sqlite_path.set.assert_called_with('/path/to/file.DbLib')
    
    # Test save method
    dialog.save()
    assert dialog.result is not None
    dialog.window.destroy.assert_called_once()
    
    # Test cancel method
    dialog.window.destroy.reset_mock()
    dialog.cancel()
    assert dialog.result is None
    dialog.window.destroy.assert_called_once()


def test_mapping_rule_dialog(mock_tk, mock_ttk, mock_filedialog, mock_messagebox):
    """Test MappingRuleDialog class."""
    parent = mock_tk.Tk()
    existing_rules = {
        "RES": "Device:R",
        "CAP": "Device:C"
    }
    dialog = MappingRuleDialog(parent, "symbol", existing_rules)
    
    # Test populate_rules method
    dialog.rules_tree.insert.assert_called()
    
    # Test add_rule method
    dialog.altium_value.get.return_value = "IND"
    dialog.kicad_value.get.return_value = "Device:L"
    dialog.add_rule()
    assert "IND" in dialog.existing_rules
    assert dialog.existing_rules["IND"] == "Device:L"
    
    # Test clear_form method
    dialog.clear_form()
    dialog.altium_value.set.assert_called_with('')
    dialog.kicad_value.set.assert_called_with('')
    
    # Test save_rules method
    dialog.save_rules()
    assert dialog.result is not None
    dialog.window.destroy.assert_called_once()
    
    # Test cancel method
    dialog.window.destroy.reset_mock()
    dialog.cancel()
    assert dialog.result is None
    dialog.window.destroy.assert_called_once()


def test_batch_process_dialog(mock_tk, mock_ttk, mock_filedialog, mock_messagebox):
    """Test BatchProcessDialog class."""
    parent = mock_tk.Tk()
    dialog = BatchProcessDialog(parent)
    
    # Test add_files method
    dialog.add_files()
    mock_filedialog.askopenfilenames.assert_called_once()
    assert len(dialog.files) == 2
    dialog.files_list.insert.assert_called()
    
    # Test remove_file method
    dialog.files_list.curselection.return_value = (0,)
    dialog.files_list.get.return_value = "/path/to/file1.DbLib"
    dialog.remove_file()
    assert len(dialog.files) == 1
    dialog.files_list.delete.assert_called_once()
    
    # Test clear_files method
    dialog.clear_files()
    assert len(dialog.files) == 0
    dialog.files_list.delete.assert_called()
    
    # Test start_processing method
    dialog.files = ["/path/to/file1.DbLib", "/path/to/file2.DbLib"]
    dialog.start_processing()
    assert dialog.result is not None
    dialog.window.destroy.assert_called_once()
    
    # Test cancel method
    dialog.window.destroy.reset_mock()
    dialog.cancel()
    assert dialog.result is None
    dialog.window.destroy.assert_called_once()


def test_help_dialog(mock_tk, mock_ttk):
    """Test HelpDialog class."""
    parent = mock_tk.Tk()
    dialog = HelpDialog(parent)
    
    # Verify notebook was created with tabs
    mock_ttk.Notebook.assert_called_once()
    mock_ttk.Notebook.return_value.add.assert_called()
    
    # Test close button
    mock_ttk.Button.assert_called()


def test_altium_to_kicad_migration_app(
    mock_tk, mock_ttk, mock_filedialog, mock_messagebox, mock_scrolledtext,
    mock_config_manager, mock_parser, mock_mapper, mock_generator, mock_setup_logging
):
    """Test AltiumToKiCADMigrationApp class."""
    # Mock os.path.exists
    with patch('os.path.exists', return_value=True):
        app = AltiumToKiCADMigrationApp()
        
        # Test initialization
        mock_tk.Tk.assert_called_once()
        mock_setup_logging.assert_called_once()
        
        # Test browse_altium_file method
        app.browse_altium_file()
        mock_filedialog.askopenfilename.assert_called()
        app.altium_dblib_path.set.assert_called()
        
        # Test browse_output_dir method
        app.browse_output_dir()
        mock_filedialog.askdirectory.assert_called()
        app.output_directory.set.assert_called()
        
        # Test update_config_from_ui method
        app.update_config_from_ui()
        mock_config_manager.return_value.set.assert_called()
        
        # Test run method
        app.run()
        app.root.mainloop.assert_called_once()


def test_main():
    """Test main function."""
    with patch('migration_tool.gui.AltiumToKiCADMigrationApp') as mock_app:
        app_instance = MagicMock()
        mock_app.return_value = app_instance
        
        from migration_tool.gui import main
        main()
        
        mock_app.assert_called_once()
        app_instance.run.assert_called_once()