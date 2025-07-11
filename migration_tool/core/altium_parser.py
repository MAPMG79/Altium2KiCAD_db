"""
Parser for Altium .DbLib files and associated databases.

This module provides functionality to parse Altium database library files
and extract component data from the associated databases.
"""

import configparser
import pyodbc
import sqlite3
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from migration_tool.utils.logging_utils import get_logger
from migration_tool.utils.database_utils import create_connection, execute_query, table_exists, get_table_columns


class AltiumDbLibParser:
    """Parser for Altium .DbLib files and associated databases."""
    
    def __init__(self, config_manager=None):
        """
        Initialize the parser.
        
        Args:
            config_manager: Optional configuration manager instance
        """
        self.connection_string = None
        self.tables = {}
        self.field_mappings = {}
        self.config = config_manager
        self.logger = get_logger("core.altium_parser")
    
    def parse_dblib_file(self, dblib_path: str) -> Dict[str, Any]:
        """
        Parse Altium .DbLib configuration file.
        
        Args:
            dblib_path: Path to Altium .DbLib file
            
        Returns:
            Dictionary containing connection information and table configurations
            
        Raises:
            FileNotFoundError: If the DbLib file doesn't exist
            ValueError: If the DbLib file is invalid or missing required sections
        """
        self.logger.info(f"Parsing Altium DbLib file: {dblib_path}")
        
        if not os.path.exists(dblib_path):
            self.logger.error(f"DbLib file not found: {dblib_path}")
            raise FileNotFoundError(f"DbLib file not found: {dblib_path}")
        
        config = configparser.ConfigParser()
        config.read(dblib_path)
        
        # Check if DatabaseLinks section exists
        if 'DatabaseLinks' not in config:
            self.logger.error(f"Invalid DbLib file: Missing DatabaseLinks section")
            raise ValueError(f"Invalid DbLib file: Missing DatabaseLinks section")
        
        # Extract connection information
        db_links = config['DatabaseLinks']
        self.connection_string = db_links.get('ConnectionString', '')
        
        if not self.connection_string:
            self.logger.error("Missing connection string in DbLib file")
            raise ValueError("Missing connection string in DbLib file")
        
        # Parse table configurations
        tables_config = {}
        for section_name in config.sections():
            if section_name.startswith('Table'):
                table_info = dict(config[section_name])
                table_name = table_info.get('TableName', '')
                if table_name:
                    self.logger.debug(f"Found table configuration: {table_name}")
                    tables_config[table_name] = self._parse_table_config(table_info)
        
        if not tables_config:
            self.logger.warning("No table configurations found in DbLib file")
        
        db_config = {
            'connection_string': self.connection_string,
            'tables': tables_config,
            'database_type': self._detect_database_type()
        }
        
        self.logger.info(f"Parsed DbLib file with {len(tables_config)} tables, database type: {db_config['database_type']}")
        return db_config
    
    def _parse_table_config(self, table_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse individual table configuration.
        
        Args:
            table_info: Table configuration from DbLib file
            
        Returns:
            Parsed table configuration
        """
        # Extract custom fields
        custom_fields = []
        for key, value in table_info.items():
            if key.startswith('Field') and 'Name' in key:
                custom_fields.append(value)
        
        return {
            'enabled': table_info.get('Enabled', 'True') == 'True',
            'key_field': table_info.get('Key', 'ID'),
            'symbol_field': table_info.get('Symbols', 'Symbol'),
            'footprint_field': table_info.get('Footprints', 'Footprint'),
            'description_field': table_info.get('Description', 'Description'),
            'user_where': table_info.get('UserWhereText', ''),
            'custom_fields': custom_fields
        }
    
    def _detect_database_type(self) -> str:
        """
        Detect database type from connection string.
        
        Returns:
            Database type string ('access', 'sqlserver', 'sqlite', 'mysql', 'postgresql', or 'unknown')
        """
        conn_str = self.connection_string.lower()
        if 'microsoft.ace.oledb' in conn_str or '.mdb' in conn_str or '.accdb' in conn_str:
            return 'access'
        elif 'sql server' in conn_str or 'sqlserver' in conn_str:
            return 'sqlserver'
        elif 'sqlite' in conn_str or '.db' in conn_str or '.sqlite' in conn_str:
            return 'sqlite'
        elif 'mysql' in conn_str:
            return 'mysql'
        elif 'postgresql' in conn_str or 'postgres' in conn_str:
            return 'postgresql'
        else:
            self.logger.warning(f"Unknown database type for connection string: {self.connection_string[:30]}...")
            return 'unknown'
    
    def connect_to_database(self) -> Any:
        """
        Establish connection to Altium database.
        
        Returns:
            Database connection object
            
        Raises:
            ValueError: If the database type is unsupported
            ConnectionError: If connection fails
        """
        db_type = self._detect_database_type()
        self.logger.info(f"Connecting to {db_type} database")
        
        try:
            if db_type == 'access':
                return pyodbc.connect(self.connection_string, timeout=self._get_connection_timeout())
            elif db_type == 'sqlite':
                # Extract database path from connection string
                db_path = self._extract_sqlite_path()
                self.logger.debug(f"SQLite database path: {db_path}")
                return sqlite3.connect(db_path)
            elif db_type in ['sqlserver', 'mysql', 'postgresql']:
                return pyodbc.connect(self.connection_string, timeout=self._get_connection_timeout())
            else:
                self.logger.error(f"Unsupported database type: {db_type}")
                raise ValueError(f"Unsupported database type: {db_type}")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
    
    def _get_connection_timeout(self) -> int:
        """Get connection timeout from config or use default."""
        if self.config:
            return self.config.get('connection_timeout', 30)
        return 30
    
    def _extract_sqlite_path(self) -> str:
        """
        Extract SQLite database path from connection string.
        
        Returns:
            Path to SQLite database file
            
        Raises:
            ValueError: If SQLite database path cannot be extracted
        """
        # Parse various SQLite connection string formats
        conn_parts = self.connection_string.split(';')
        
        # Look for database= parameter
        for part in conn_parts:
            if 'database=' in part.lower():
                return part.split('=', 1)[1].strip().strip('"\'')
        
        # Look for Data Source= parameter
        for part in conn_parts:
            if 'data source=' in part.lower():
                return part.split('=', 1)[1].strip().strip('"\'')
        
        # Look for direct file path
        for part in conn_parts:
            if part.lower().endswith('.db') or part.lower().endswith('.sqlite'):
                return part.strip().strip('"\'')
        
        self.logger.error("Could not extract SQLite database path from connection string")
        raise ValueError("Could not extract SQLite database path from connection string")
    
    def extract_table_data(self, table_name: str, table_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from a specific table.
        
        Args:
            table_name: Name of the table to extract data from
            table_config: Table configuration
            
        Returns:
            List of dictionaries containing table data
            
        Raises:
            ValueError: If table doesn't exist
            Exception: For other database errors
        """
        self.logger.info(f"Extracting data from table: {table_name}")
        conn = self.connect_to_database()
        
        try:
            # Check if table exists
            if not table_exists(conn, table_name):
                self.logger.error(f"Table {table_name} does not exist in database")
                raise ValueError(f"Table {table_name} does not exist in database")
            
            # Build query with optional WHERE clause
            base_query = f"SELECT * FROM [{table_name}]"
            if table_config.get('user_where'):
                base_query += f" WHERE {table_config['user_where']}"
            
            self.logger.debug(f"Executing query: {base_query}")
            
            # Execute query and fetch results
            results = execute_query(conn, base_query)
            self.logger.info(f"Extracted {len(results)} records from {table_name}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error extracting data from {table_name}: {str(e)}")
            raise
        
        finally:
            conn.close()
    
    def extract_all_data(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract data from all configured tables.
        
        Args:
            config: Configuration dictionary from parse_dblib_file
            
        Returns:
            Dictionary containing data from all tables
        """
        self.logger.info("Extracting data from all configured tables")
        all_data = {}
        
        for table_name, table_config in config['tables'].items():
            if table_config['enabled']:
                self.logger.info(f"Processing table: {table_name}")
                try:
                    table_data = self.extract_table_data(table_name, table_config)
                    all_data[table_name] = {
                        'config': table_config,
                        'data': table_data
                    }
                    self.logger.info(f"Extracted {len(table_data)} records from {table_name}")
                except Exception as e:
                    self.logger.error(f"Error extracting from {table_name}: {str(e)}")
                    all_data[table_name] = {
                        'config': table_config,
                        'data': [],
                        'error': str(e)
                    }
        
        self.logger.info(f"Completed data extraction from {len(all_data)} tables")
        return all_data