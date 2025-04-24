import sqlite3
import os
from contextlib import contextmanager
from config import DB_PATH


class DatabaseManager:
    _instance = None

    def __new__(cls, db_path=DB_PATH):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.db_path = db_path
            cls._instance._setup()
        return cls._instance

    def _setup(self):
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not hasattr(self, '_logged'):
            print(f"[DB] Connecting to: {self.db_path}")
            self._logged = True
        

    def connect(self):
        """
        Always creates a new connection (thread-safe for PySide6),
        with a timeout and foreign keys enabled.
        """
        conn = sqlite3.connect(
            self.db_path,
            timeout=10,                 # Increase timeout to handle locked DB
            check_same_thread=False     # For multithreaded PySide6 apps
        )
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def cursor(self):
        """
        Context manager for opening a cursor, ensuring commit/rollback,
        and closing the connection after use.
        """
        conn = self.connect()
        cur = conn.cursor()

        try:
            yield cur
            conn.commit()
        except sqlite3.OperationalError as e:
            conn.rollback()
            print(f"Database locked error: {e}")
            raise
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            cur.close()
            conn.close()  # Always close the connection after operation

    def execute(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        """
        Executes a query using the context-managed cursor.
        """
        with self.cursor() as cur:
            cur.execute(query, params)
            if fetchone:
                result = cur.fetchone()
                print(f"Fetchone result: {result}")
                return result
            if fetchall:
                result = cur.fetchall()
                print(f"Fetchall result: {result}")
                return result
            return None
    
    def fetchval(self, query, params=None): # Fetch a value from the database
        with self.cursor() as cur:
            cur.execute(query, params or ())
            result = cur.fetchone()
            return result[0] if result else 0
        
    def fetchall(self, query, params=None): # Fetch all values from the database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(query, params or ())
                return cur.fetchall()
        except sqlite3.Error as e:
            print("Database fetchall error:", e)
            return []


