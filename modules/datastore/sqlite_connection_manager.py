import sqlite3
from threading import Lock

class SQLiteConnectionManager:
    """Singleton manager for SQLite connections."""
    _instances = {}
    _lock = Lock()  # Ensure thread safety

    def __new__(cls, db_path: str):
        """Ensure only one connection per database path."""
        with cls._lock:  # Thread-safe instantiation
            if db_path not in cls._instances:
                instance = super().__new__(cls)
                instance.connection = sqlite3.connect(db_path)
                instance.connection.row_factory = sqlite3.Row
                cls._instances[db_path] = instance
            return cls._instances[db_path]

    def get_connection(self) -> sqlite3.Connection:
        """Get the SQLite connection."""
        return self.connection

    @classmethod
    def close_all(cls) -> None:
        """Close all connections and clear the instances."""
        with cls._lock:  # Thread-safe cleanup
            for db_path, instance in list(cls._instances.items()):
                if instance.connection:
                    instance.connection.close()
                del cls._instances[db_path]  # Remove the instance to avoid memory leaks