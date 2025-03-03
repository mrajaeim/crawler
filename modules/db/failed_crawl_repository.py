from .sqlite_repository import SQLiteRepository
from typing import List, Optional, Dict, Any


class FailedCrawlRepository(SQLiteRepository):
    """Repository for the `failed_crawls` table."""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self) -> None:
        """Create the `failed_crawls` table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS failed_crawls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            type TEXT NOT NULL,
            error TEXT,
            foreign_id INTEGER NOT NULL,
            status TEXT
        )
        """
        self.execute(query)

    def create_failed_crawl(self, url: str, type: str, error: str, foreign_id: int, status: str) -> int:
        """Create a new failed crawl entry and return its ID."""
        query = """
        INSERT INTO failed_crawls (url, type, error, foreign_id, status)
        VALUES (?, ?, ?, ?, ?)
        """
        self.execute(query, (url, type, error, foreign_id, status))
        return self.cursor.lastrowid

    def get_failed_crawl_by_id(self, failed_crawl_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a failed crawl entry by its ID."""
        query = "SELECT * FROM failed_crawls WHERE id = ?"
        return self.fetch_one(query, (failed_crawl_id,))

    def update_failed_crawl(self, failed_crawl_id: int, **kwargs) -> None:
        """Update a failed crawl entry's fields."""
        if not kwargs:
            raise ValueError("No fields to update provided.")
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE failed_crawls SET {set_clause} WHERE id = ?"
        self.execute(query, (*kwargs.values(), failed_crawl_id))

    def delete_failed_crawl(self, failed_crawl_id: int) -> None:
        """Delete a failed crawl entry by its ID."""
        query = "DELETE FROM failed_crawls WHERE id = ?"
        self.execute(query, (failed_crawl_id,))

    def get_all_failed_crawls(self) -> List[Dict[str, Any]]:
        """Fetch all failed crawl entries."""
        query = "SELECT * FROM failed_crawls"
        return self.fetch_all(query)
