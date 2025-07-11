"""
Database utilities for the Altium to KiCAD migration tool.

This module provides helper functions and classes for database operations.
"""

import sqlite3
import pyodbc
from typing import Any, Dict, List, Optional, Tuple


class DatabaseUtils:
    """Database utility class for the Altium to KiCAD migration tool."""
    
    @staticmethod
    def create_connection(connection_string: str, db_type: str) -> Any:
        """Create database connection based on database type."""
        return create_connection(connection_string, db_type)
    
    @staticmethod
    def execute_query(connection: Any, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dictionaries."""
        return execute_query(connection, query, params)
    
    @staticmethod
    def execute_script(connection: Any, script: str) -> None:
        """Execute SQL script with multiple statements."""
        execute_script(connection, script)
    
    @staticmethod
    def table_exists(connection: Any, table_name: str) -> bool:
        """Check if table exists in database."""
        return table_exists(connection, table_name)
    
    @staticmethod
    def get_table_columns(connection: Any, table_name: str) -> List[str]:
        """Get list of column names for a table."""
        return get_table_columns(connection, table_name)
    
    @staticmethod
    def optimize_database(db_path: str) -> None:
        """Optimize SQLite database for better performance."""
        optimize_database(db_path)
    
    @staticmethod
    def create_indexes(connection: Any, table_name: str, columns: List[str]) -> None:
        """Create indexes on specified columns for better query performance."""
        create_indexes(connection, table_name, columns)


def create_connection(connection_string: str, db_type: str) -> Any:
    """Create database connection based on database type."""
    if db_type == 'sqlite':
        return sqlite3.connect(connection_string)
    elif db_type in ['access', 'sqlserver', 'mysql', 'postgresql']:
        return pyodbc.connect(connection_string)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def execute_query(connection: Any, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """Execute SQL query and return results as list of dictionaries."""
    cursor = connection.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Get column names
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            
            # Fetch all rows and convert to dictionaries
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    row_dict[column] = row[i]
                result.append(row_dict)
            
            return result
        else:
            # No results (e.g., for INSERT, UPDATE, DELETE)
            return []
    
    finally:
        cursor.close()


def execute_script(connection: Any, script: str) -> None:
    """Execute SQL script with multiple statements."""
    cursor = connection.cursor()
    
    try:
        cursor.executescript(script) if hasattr(cursor, 'executescript') else cursor.execute(script)
        connection.commit()
    
    finally:
        cursor.close()


def table_exists(connection: Any, table_name: str) -> bool:
    """Check if table exists in database."""
    cursor = connection.cursor()
    
    try:
        # SQLite specific query
        if isinstance(connection, sqlite3.Connection):
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
        
        # ODBC connection (more generic)
        else:
            try:
                cursor.tables(table=table_name)
                return len(cursor.fetchall()) > 0
            except:
                # Fallback method
                try:
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE 1=0")
                    return True
                except:
                    return False
    
    finally:
        cursor.close()


def get_table_columns(connection: Any, table_name: str) -> List[str]:
    """Get list of column names for a table."""
    cursor = connection.cursor()
    
    try:
        # SQLite specific query
        if isinstance(connection, sqlite3.Connection):
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [row[1] for row in cursor.fetchall()]
        
        # ODBC connection
        else:
            cursor.execute(f"SELECT * FROM {table_name} WHERE 1=0")
            return [column[0] for column in cursor.description]
    
    except Exception as e:
        print(f"Error getting columns for table {table_name}: {e}")
        return []
    
    finally:
        cursor.close()


def optimize_database(db_path: str) -> None:
    """Optimize SQLite database for better performance."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Analyze tables to update statistics
        cursor.execute("ANALYZE")
        
        # Vacuum database to reclaim space and defragment
        cursor.execute("VACUUM")
        
        # Set pragma settings for better performance
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes
        cursor.execute("PRAGMA cache_size=10000")  # Larger cache
        cursor.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp data
        
        conn.commit()
    
    finally:
        cursor.close()
        conn.close()


def create_indexes(connection: Any, table_name: str, columns: List[str]) -> None:
    """Create indexes on specified columns for better query performance."""
    cursor = connection.cursor()
    
    try:
        for column in columns:
            index_name = f"idx_{table_name}_{column}"
            query = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column})"
            cursor.execute(query)
        
        connection.commit()
    
    finally:
        cursor.close()