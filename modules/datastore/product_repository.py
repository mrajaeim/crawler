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
            sales_price INTEGER,
            category TEXT,
            short_desc TEXT,
            brand TEXT,
            url TEXT NOT NULL UNIQUE
        )
        """
        self.execute(query)

    def create_product(self, title: str, price: str, sales_price: str, category: str, short_desc: str, brand: str,
                       url: str) -> int:
        """Create a new product and return its ID."""
        query = """
        INSERT INTO products (title, price, sales_price, category, short_desc, brand, url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(query, (title, price, sales_price, category, short_desc, brand, url))
        return self.cursor.lastrowid

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a product by its ID."""
        query = "SELECT * FROM products WHERE id = ?"
        return self.fetch_one(query, (product_id,))

    def get_product_by_url(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Fetch a product by its ID."""
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
