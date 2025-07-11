"""
Logging utilities for the Altium to KiCAD migration tool.

This module provides functions for setting up and configuring logging.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, file logging is disabled)
        console: Whether to log to console
        log_format: Format string for log messages
    
    Returns:
        Configured logger instance
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("migration_tool")
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        # Create directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name (if None, root logger is returned)
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"migration_tool.{name}")
    else:
        return logging.getLogger("migration_tool")


class ProgressLogger:
    """Logger for tracking migration progress."""
    
    def __init__(self, logger: logging.Logger, total_items: int):
        """
        Initialize progress logger.
        
        Args:
            logger: Logger instance
            total_items: Total number of items to process
        """
        self.logger = logger
        self.total_items = total_items
        self.processed_items = 0
        self.last_percentage = 0
    
    def update(self, increment: int = 1) -> None:
        """
        Update progress.
        
        Args:
            increment: Number of items processed
        """
        self.processed_items += increment
        percentage = int((self.processed_items / self.total_items) * 100)
        
        # Log progress every 5%
        if percentage >= self.last_percentage + 5 or percentage == 100:
            self.logger.info(f"Progress: {percentage}% ({self.processed_items}/{self.total_items})")
            self.last_percentage = percentage
    
    def complete(self) -> None:
        """Mark progress as complete."""
        self.processed_items = self.total_items
        self.logger.info(f"Progress: 100% ({self.total_items}/{self.total_items})")


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any]
) -> None:
    """
    Log error with context information.
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Context information
    """
    logger.error(f"Error: {str(error)}")
    logger.error(f"Context: {context}")
    logger.debug("Exception details:", exc_info=True)