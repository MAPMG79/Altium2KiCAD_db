import configparser
import pyodbc
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class AltiumDbLibParser:
    """Parser for Altium .DbLib files and associated databases"""
    
    def __init__(self):
        self.connection_string = None
        self.tables = {}
        self.field_mappings = {}
    
    def parse_dblib_file(self, dblib_path: str) -> Dict[str, Any]:
        """Parse Altium .DbLib configuration file"""
        config = configparser.ConfigParser()
        config.read(dblib_path)
        
        # Extract connection information
        db_links = config['DatabaseLinks']
        self.connection_string = db_links.get('ConnectionString', '')
        
        # Parse table configurations
        tables_config = {}
        for section_name in config.sections():
            if section_name.startswith('Table'):
                table_info = dict(config[section_name])
                table_name = table_info.get('TableName', '')
                if table_name:
                    tables_config[table_name] = self._parse_table_config(table_info)
        
        return {
            'connection_string': self.connection_string,
            'tables': tables_config,
            'database_type': self._detect_database_type()
        }
    
    def _parse_table_config(self, table_info: Dict[str, str]) -> Dict[str, Any]:
        """Parse individual table configuration"""
        return {
            'enabled': table_info.get('Enabled', 'True') == 'True',
            'key_field': table_info.get('Key', 'ID'),
            'symbol_field': table_info.get('Symbols', 'Symbol'),
            'footprint_field': table_info.get('Footprints', 'Footprint'),
            'description_field': table_info.get('Description', 'Description'),
            'user_where': table_info.get('UserWhereText', ''),
            'custom_fields': self._extract_custom_fields(table_info)
        }
    
    def _extract_custom_fields(self, table_info: Dict[str, str]) -> List[str]:
        """Extract custom field definitions from table config"""
        custom_fields = []
        # Look for field definitions in Altium format
        for key, value in table_info.items():
            if key.startswith('Field') and 'Name' in key:
                custom_fields.append(value)
        return custom_fields
    
    def _detect_database_type(self) -> str:
        """Detect database type from connection string"""
        conn_str = self.connection_string.lower()
        if 'microsoft.ace.oledb' in conn_str or '.mdb' in conn_str:
            return 'access'
        elif 'sql server' in conn_str or 'sqlserver' in conn_str:
            return 'sqlserver'
        elif 'sqlite' in conn_str:
            return 'sqlite'
        elif 'mysql' in conn_str:
            return 'mysql'
        elif 'postgresql' in conn_str:
            return 'postgresql'
        else:
            return 'unknown'
    
    def connect_to_database(self) -> Any:
        """Establish connection to Altium database"""
        db_type = self._detect_database_type()
        
        if db_type == 'access':
            return pyodbc.connect(self.connection_string)
        elif db_type == 'sqlite':
            # Extract database path from connection string
            db_path = self._extract_sqlite_path()
            return sqlite3.connect(db_path)
        elif db_type in ['sqlserver', 'mysql', 'postgresql']:
            return pyodbc.connect(self.connection_string)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def extract_table_data(self, table_name: str, table_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract data from a specific table"""
        conn = self.connect_to_database()
        
        # Build query with optional WHERE clause
        base_query = f"SELECT * FROM [{table_name}]"
        if table_config.get('user_where'):
            base_query += f" WHERE {table_config['user_where']}"
        
        try:
            cursor = conn.cursor()
            cursor.execute(base_query)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()