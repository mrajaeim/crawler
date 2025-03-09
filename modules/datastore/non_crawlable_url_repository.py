from .sqlite_repository import SQLiteRepository
from typing import List, Optional, Dict, Any


class NonCrawlableUrlRepository(SQLiteRepository):
    """Repository for the `non_crawlable_urls` table - stores URLs that aren't products or images."""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self) -> None:
        """Create the `non_crawlable_urls` table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS non_crawlable_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            url_type TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute(query)
        # Create index on URL for faster lookups
        self.execute("CREATE INDEX IF NOT EXISTS idx_non_crawlable_urls_url ON non_crawlable_urls(url)")

    def create_non_crawlable_url(self, url: str, url_type: str, reason: str = None) -> int:
        """
        Create a new non-crawlable URL entry and return its ID.
        
        Args:
            url: The URL that shouldn't be crawled
            url_type: Type of URL (e.g., 'page', 'category', 'search')
            reason: Optional reason why this URL isn't crawlable
            
        Returns:
            ID of the created entry
        """
        query = """
        INSERT OR IGNORE INTO non_crawlable_urls (url, url_type, reason)
        VALUES (?, ?, ?)
        """
        self.execute(query, (url, url_type, reason))
        return self.cursor.lastrowid

    def is_non_crawlable_url(self, url: str) -> bool:
        """
        Check if a URL is in the non-crawlable list.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL exists in the non-crawlable list, False otherwise
        """
        query = "SELECT COUNT(*) FROM non_crawlable_urls WHERE url = ?"
        result = self.fetch_one(query, (url,))
        return result["COUNT(*)"] > 0 if result else False

    def get_non_crawlable_url_by_id(self, url_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a non-crawlable URL entry by its ID."""
        query = "SELECT * FROM non_crawlable_urls WHERE id = ?"
        return self.fetch_one(query, (url_id,))

    def get_non_crawlable_url_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch a non-crawlable URL entry by its URL."""
        query = "SELECT * FROM non_crawlable_urls WHERE url = ?"
        return self.fetch_one(query, (url,))

    def update_non_crawlable_url(self, url_id: int, **kwargs) -> None:
        """Update a non-crawlable URL entry's fields."""
        if not kwargs:
            raise ValueError("No fields to update provided.")
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE non_crawlable_urls SET {set_clause} WHERE id = ?"
        self.execute(query, (*kwargs.values(), url_id))

    def delete_non_crawlable_url(self, url_id: int) -> None:
        """Delete a non-crawlable URL entry by its ID."""
        query = "DELETE FROM non_crawlable_urls WHERE id = ?"
        self.execute(query, (url_id,))

    def get_all_non_crawlable_urls(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch all non-crawlable URL entries with pagination.
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of non-crawlable URL entries
        """
        query = "SELECT * FROM non_crawlable_urls ORDER BY created_at DESC LIMIT ? OFFSET ?"
        return self.fetch_all(query, (limit, offset))

    def get_non_crawlable_urls_count(self) -> int:
        """Get the total count of non-crawlable URLs."""
        query = "SELECT COUNT(*) FROM non_crawlable_urls"
        result = self.fetch_one(query)
        return result["COUNT(*)"] if result else 0
