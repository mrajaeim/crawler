import sqlite3
from typing import List, Optional, Dict, Any
from .sqlite_connection_manager import SQLiteConnectionManager


class SQLiteRepository:
    """Base repository class for SQLite database operations."""
    def __init__(self, db_path: str):
        self.connection_manager = SQLiteConnectionManager(db_path)
        self.connection = self.connection_manager.get_connection()
        self.cursor = self.connection.cursor()

    def __del__(self):
        """Close the database connection when the object is destroyed."""
        if self.connection:
            self.connection.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query with optional parameters."""
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database."""
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows from the database."""
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]