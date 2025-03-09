from .sqlite_repository import SQLiteRepository
from typing import List, Optional, Dict, Any


class ProductRepository(SQLiteRepository):
    """Repository for the `products` table."""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self) -> None:
        """Create the `products` table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price TEXT NOT NULL,
            sales_price TEXT,
            category TEXT,
            short_desc TEXT,
            brand TEXT,
            url TEXT NOT NULL UNIQUE,
            has_variations BOOLEAN DEFAULT 0,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES products (id) ON DELETE CASCADE
        )
        """
        self.execute(query)

    def create_product(self, title: str, price: str, sales_price: str, category: str, short_desc: str, brand: str,
                       url: str, has_variations: bool = False, parent_id: Optional[int] = None) -> int:
        """Create a new product and return its ID."""
        query = """
        INSERT INTO products (title, price, sales_price, category, short_desc, brand, url, has_variations, parent_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(query, (title, price, sales_price, category, short_desc, brand, url, has_variations, parent_id))
        return self.cursor.lastrowid

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a product by its ID."""
        query = "SELECT * FROM products WHERE id = ?"
        return self.fetch_one(query, (product_id,))

    def get_product_by_url(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Fetch a product by its URL."""
        query = "SELECT * FROM products WHERE url = ?"
        return self.fetch_one(query, (product_url,))

    def update_product(self, product_id: int, **kwargs) -> None:
        """Update a product's fields."""
        if not kwargs:
            raise ValueError("No fields to update provided.")
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE products SET {set_clause} WHERE id = ?"
        self.execute(query, (*kwargs.values(), product_id))

    def delete_product(self, product_id: int) -> None:
        """Delete a product by its ID."""
        query = "DELETE FROM products WHERE id = ?"
        self.execute(query, (product_id,))

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Fetch all products."""
        query = "SELECT * FROM products"
        return self.fetch_all(query)
        
    def get_product_variations(self, parent_id: int) -> List[Dict[str, Any]]:
        """Fetch all variations of a parent product."""
        query = """
        SELECT p.*, v.variation_code, i.image_url 
        FROM products p
        JOIN product_variations v ON p.id = v.product_id
        LEFT JOIN images i ON v.image_id = i.id
        WHERE p.parent_id = ?
        """
        return self.fetch_all(query, (parent_id,))
        
    def mark_product_has_variations(self, product_id: int, has_variations: bool = True) -> None:
        """Mark a product as having variations."""
        query = "UPDATE products SET has_variations = ? WHERE id = ?"
        self.execute(query, (has_variations, product_id))
