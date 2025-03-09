from .sqlite_repository import SQLiteRepository
from typing import List, Optional, Dict, Any


class VariationRepository(SQLiteRepository):
    """Repository for the `product_variations` table."""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self) -> None:
        """Create the `product_variations` table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS product_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            variation_code TEXT NOT NULL,
            image_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
            FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE SET NULL,
            UNIQUE(product_id, variation_code)
        )
        """
        self.execute(query)

    def create_variation(self, product_id: int, variation_code: str, image_id: Optional[int] = None) -> int:
        """Create a new product variation and return its ID."""
        query = """
        INSERT INTO product_variations (product_id, variation_code, image_id)
        VALUES (?, ?, ?)
        """
        self.execute(query, (product_id, variation_code, image_id))
        return self.cursor.lastrowid

    def get_variation_by_id(self, variation_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a variation by its ID."""
        query = "SELECT * FROM product_variations WHERE id = ?"
        return self.fetch_one(query, (variation_id,))

    def get_variations_by_product_id(self, product_id: int) -> List[Dict[str, Any]]:
        """Fetch all variations for a specific product."""
        query = """
        SELECT pv.*, i.image_url 
        FROM product_variations pv
        LEFT JOIN images i ON pv.image_id = i.id
        WHERE pv.product_id = ?
        """
        return self.fetch_all(query, (product_id,))

    def get_variation_by_code(self, product_id: int, variation_code: str) -> Optional[Dict[str, Any]]:
        """Fetch a variation by its product ID and code."""
        query = "SELECT * FROM product_variations WHERE product_id = ? AND variation_code = ?"
        return self.fetch_one(query, (product_id, variation_code))

    def update_variation(self, variation_id: int, **kwargs) -> None:
        """Update a variation's fields."""
        if not kwargs:
            raise ValueError("No fields to update provided.")
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE product_variations SET {set_clause} WHERE id = ?"
        self.execute(query, (*kwargs.values(), variation_id))

    def delete_variation(self, variation_id: int) -> None:
        """Delete a variation by its ID."""
        query = "DELETE FROM product_variations WHERE id = ?"
        self.execute(query, (variation_id,))

    def delete_variations_by_product_id(self, product_id: int) -> None:
        """Delete all variations for a specific product."""
        query = "DELETE FROM product_variations WHERE product_id = ?"
        self.execute(query, (product_id,))
