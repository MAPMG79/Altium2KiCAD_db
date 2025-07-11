"""
Unit tests for the Logging Utilities module.
"""

import os
import logging
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from migration_tool.utils.logging_utils import (
    setup_logging,
    get_logger,
    ProgressLogger,
    log_error_with_context
)


class TestLoggingUtils:
    """Test cases for the logging utility functions."""

    def test_setup_logging_default(self):
        """Test setting up logging with default parameters."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Call the function with default parameters
            logger = setup_logging()
            
            # Check that the logger was created with the correct name
            mock_get_logger.assert_called_with("migration_tool")
            
            # Check that the logger level was set
            mock_logger.setLevel.assert_called_with(logging.INFO)
            
            # Check that a console handler was added
            assert mock_logger.addHandler.called
            
            # Check that the returned logger is the mock logger
            assert logger == mock_logger
    
    def test_setup_logging_custom_level(self):
        """Test setting up logging with a custom log level."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Call the function with a custom log level
            logger = setup_logging(log_level="DEBUG")
            
            # Check that the logger level was set to DEBUG
            mock_logger.setLevel.assert_called_with(logging.DEBUG)
    
    def test_setup_logging_invalid_level(self):
        """Test setting up logging with an invalid log level."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Call the function with an invalid log level
            logger = setup_logging(log_level="INVALID")
            
            # Check that the logger level defaults to INFO
            mock_logger.setLevel.assert_called_with(logging.INFO)
    
    def test_setup_logging_no_console(self):
        """Test setting up logging without console output."""
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_stream_handler:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Call the function with console=False
            logger = setup_logging(console=False)
            
            # Check that no StreamHandler was created
            mock_stream_handler.assert_not_called()
    
    def test_setup_logging_with_file(self, temp_dir):
        """Test setting up logging with a log file."""
        log_file = os.path.join(temp_dir, 'test.log')
        
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.handlers.RotatingFileHandler') as mock_file_handler:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            mock_handler = MagicMock()
            mock_file_handler.return_value = mock_handler
            
            # Call the function with a log file
            logger = setup_logging(log_file=log_file)
            
            # Check that a RotatingFileHandler was created with the correct parameters
            mock_file_handler.assert_called_with(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5
            )
            
            # Check that the handler was added to the logger
            mock_logger.addHandler.assert_called_with(mock_handler)
    
    def test_setup_logging_with_file_creates_directory(self, temp_dir):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        log_file = os.path.join(temp_dir, 'logs', 'test.log')
        
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.handlers.RotatingFileHandler') as mock_file_handler:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Call the function with a log file in a nonexistent directory
            logger = setup_logging(log_file=log_file)
            
            # Check that the directory was created
            assert os.path.exists(os.path.dirname(log_file))
    
    def test_setup_logging_custom_format(self):
        """Test setting up logging with a custom format."""
        custom_format = "%(levelname)s - %(message)s"
        
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.Formatter') as mock_formatter:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Call the function with a custom format
            logger = setup_logging(log_format=custom_format)
            
            # Check that the formatter was created with the custom format
            mock_formatter.assert_called_with(custom_format)
    
    def test_setup_logging_removes_existing_handlers(self):
        """Test that setup_logging removes existing handlers."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_handler1 = MagicMock()
            mock_handler2 = MagicMock()
            mock_logger.handlers = [mock_handler1, mock_handler2]
            mock_get_logger.return_value = mock_logger
            
            # Call the function
            logger = setup_logging()
            
            # Check that the existing handlers were removed
            assert mock_logger.removeHandler.call_count == 2
            mock_logger.removeHandler.assert_has_calls([call(mock_handler1), call(mock_handler2)])
    
    def test_get_logger_default(self):
        """Test getting the default logger."""
        with patch('logging.getLogger') as mock_get_logger:
            # Call the function with no name
            logger = get_logger()
            
            # Check that the correct logger was requested
            mock_get_logger.assert_called_with("migration_tool")
    
    def test_get_logger_with_name(self):
        """Test getting a logger with a specific name."""
        with patch('logging.getLogger') as mock_get_logger:
            # Call the function with a name
            logger = get_logger("test")
            
            # Check that the correct logger was requested
            mock_get_logger.assert_called_with("migration_tool.test")
    
    def test_progress_logger_init(self):
        """Test initializing a ProgressLogger."""
        mock_logger = MagicMock()
        total_items = 100
        
        # Create a ProgressLogger
        progress_logger = ProgressLogger(mock_logger, total_items)
        
        # Check that the attributes were set correctly
        assert progress_logger.logger == mock_logger
        assert progress_logger.total_items == total_items
        assert progress_logger.processed_items == 0
        assert progress_logger.last_percentage == 0
    
    def test_progress_logger_update_no_log(self):
        """Test updating progress without triggering a log message."""
        mock_logger = MagicMock()
        total_items = 100
        
        # Create a ProgressLogger
        progress_logger = ProgressLogger(mock_logger, total_items)
        
        # Update progress by a small amount
        progress_logger.update(1)
        
        # Check that the processed_items was updated
        assert progress_logger.processed_items == 1
        
        # Check that no log message was generated (less than 5% progress)
        mock_logger.info.assert_not_called()
    
    def test_progress_logger_update_with_log(self):
        """Test updating progress with a log message."""
        mock_logger = MagicMock()
        total_items = 100
        
        # Create a ProgressLogger
        progress_logger = ProgressLogger(mock_logger, total_items)
        
        # Update progress by a larger amount
        progress_logger.update(5)
        
        # Check that the processed_items was updated
        assert progress_logger.processed_items == 5
        
        # Check that a log message was generated (5% progress)
        mock_logger.info.assert_called_with("Progress: 5% (5/100)")
        assert progress_logger.last_percentage == 5
    
    def test_progress_logger_update_multiple(self):
        """Test updating progress multiple times."""
        mock_logger = MagicMock()
        total_items = 100
        
        # Create a ProgressLogger
        progress_logger = ProgressLogger(mock_logger, total_items)
        
        # Update progress multiple times
        progress_logger.update(3)  # 3%
        progress_logger.update(3)  # 6%
        progress_logger.update(4)  # 10%
        
        # Check that the processed_items was updated
        assert progress_logger.processed_items == 10
        
        # Check that log messages were generated at 5% and 10%
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_has_calls([
            call("Progress: 5% (6/100)"),
            call("Progress: 10% (10/100)")
        ])
        assert progress_logger.last_percentage == 10
    
    def test_progress_logger_update_to_100_percent(self):
        """Test updating progress to 100%."""
        mock_logger = MagicMock()
        total_items = 100
        
        # Create a ProgressLogger
        progress_logger = ProgressLogger(mock_logger, total_items)
        
        # Update progress to 100%
        progress_logger.update(100)
        
        # Check that the processed_items was updated
        assert progress_logger.processed_items == 100
        
        # Check that a log message was generated for 100%
        mock_logger.info.assert_called_with("Progress: 100% (100/100)")
        assert progress_logger.last_percentage == 100
    
    def test_progress_logger_complete(self):
        """Test marking progress as complete."""
        mock_logger = MagicMock()
        total_items = 100
        
        # Create a ProgressLogger
        progress_logger = ProgressLogger(mock_logger, total_items)
        progress_logger.processed_items = 50
        
        # Mark progress as complete
        progress_logger.complete()
        
        # Check that processed_items was set to total_items
        assert progress_logger.processed_items == total_items
        
        # Check that a log message was generated
        mock_logger.info.assert_called_with("Progress: 100% (100/100)")
    
    def test_log_error_with_context(self):
        """Test logging an error with context."""
        mock_logger = MagicMock()
        error = ValueError("Test error")
        context = {"file": "test.txt", "line": 42}
        
        # Log the error with context
        log_error_with_context(mock_logger, error, context)
        
        # Check that the error and context were logged
        mock_logger.error.assert_has_calls([
            call("Error: Test error"),
            call("Context: {'file': 'test.txt', 'line': 42}")
        ])
        
        # Check that debug was called with exc_info=True
        mock_logger.debug.assert_called_with("Exception details:", exc_info=True)