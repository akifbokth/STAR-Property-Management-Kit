import sqlite3
import os
from contextlib import contextmanager
from config import DB_PATH

# DatabaseManager class to manage SQLite database connections and queries
# Singleton pattern to ensure only one instance of DatabaseManager exists
# This class handles the connection to the SQLite database, executes queries,
# and manages transactions. It also provides a context manager for cursor management, 
# ensuring that connections are properly closed after use.

class DatabaseManager:
    _instance = None

    def __new__(cls, db_path=DB_PATH): # This method is called to create a new instance of the class
        if cls._instance is None: # If no instance exists, create one
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.db_path = db_path
            cls._instance._setup()
        return cls._instance # Return the existing instance if it already exists

    def _setup(self): # This method is called to set up the database connection
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True) # Create the directory if it doesn't exist
        if not hasattr(self, '_logged'):
            print(f"[DB] Connecting to: {self.db_path}")
            self._logged = True
        

    def connect(self): # This method is called to connect to the database
        conn = sqlite3.connect(
            self.db_path,
            timeout=10,                 # Increase timeout to handle locked DB
            check_same_thread=False     # For multithreaded PySide6 apps
        )
        conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign key constraints
        return conn

    @contextmanager # Context manager for handling database connections
    def cursor(self): # This method is called to create a cursor for executing queries
        conn = self.connect()
        cur = conn.cursor()

        try: # This method is called to execute a query
            yield cur # Yield the cursor to the caller. 
            # Yield means that the function will return the cursor and pause execution until the caller is done with it.
            conn.commit()

        except sqlite3.OperationalError as e: # Handle database locked error
            conn.rollback() # Rollback the transaction on error
            print(f"Database locked error: {e}")
            raise # Re-raise the exception to be handled by the caller

        except Exception as e: # Handle other database errors
            conn.rollback() # Rollback the transaction on error
            print(f"Database error: {e}")
            raise # Re-raise the exception to be handled by the caller

        finally: # This method is called to close the cursor and connection
            cur.close()
            conn.close()  # Always close the connection after operation

    def execute(self, query, params=(), fetchone=False, fetchall=False, commit=False): # Execute a query on the database
        with self.cursor() as cur:
            cur.execute(query, params)

            if fetchone: # Fetch one result from the database
                result = cur.fetchone()
                print(f"Fetchone result: {result}") # Print the result of the fetchone operation
                return result
            
            if fetchall: # Fetch all results from the database
                result = cur.fetchall()
                print(f"Fetchall result: {result}") # Print the result of the fetchall operation
                return result
            return None
    
    def fetchval(self, query, params=None): # Fetch a value from the database
        with self.cursor() as cur:
            cur.execute(query, params or ())
            result = cur.fetchone()
            return result[0] if result else None
        
    def fetchall(self, query, params=None): # Fetch all values from the database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(query, params or ())
                return cur.fetchall()
        except sqlite3.Error as e: # Handle database errors
            print("Database fetchall error:", e)
            return []


