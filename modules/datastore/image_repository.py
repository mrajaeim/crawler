from .sqlite_repository import SQLiteRepository
from typing import List, Optional, Dict, Any


class ImageRepository(SQLiteRepository):
    """Repository for the `images` table."""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self) -> None:
        """Create the `images` table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
        """
        self.execute(query)

    def create_image(self, product_id: int, image_url: str) -> int:
        """Create a new image and return its ID."""
        query = """
        INSERT INTO images (product_id, image_url)
        VALUES (?, ?)
        """
        self.execute(query, (product_id, image_url))
        return self.cursor.lastrowid

    def get_image_by_id(self, image_id: int) -> Optional[Dict[str, Any]]:
        """Fetch an image by its ID."""
        query = "SELECT * FROM images WHERE id = ?"
        return self.fetch_one(query, (image_id,))

    def update_image(self, image_id: int, **kwargs) -> None:
        """Update an image's fields."""
        if not kwargs:
            raise ValueError("No fields to update provided.")
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE images SET {set_clause} WHERE id = ?"
        self.execute(query, (*kwargs.values(), image_id))

    def delete_image(self, image_id: int) -> None:
        """Delete an image by its ID."""
        query = "DELETE FROM images WHERE id = ?"
        self.execute(query, (image_id,))

    def get_images_by_product_id(self, product_id: int) -> List[Dict[str, Any]]:
        """Fetch all images associated with a product."""
        query = "SELECT * FROM images WHERE product_id = ?"
        return self.fetch_all(query, (product_id,))
