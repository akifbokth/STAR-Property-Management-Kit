import os
import sys
import sqlite3
from cryptography.fernet import Fernet # Import the Fernet class for encryption
from scripts.utils.security_utils import hash_password  # Import the hash_password function

def get_base_dir():
   # Get the base directory of the script or executable
   # This is useful for locating resources relative to the script's location
    if getattr(sys, 'frozen', False): # Check if the script is running as a bundled executable
        # If running as a bundled executable, use the directory of the executable

        # Running as exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def main(): # Main function to initialize the database and create necessary directories
    try:
        # === Constants === #
        BASE_DIR = get_base_dir()
        # Paths for DB and key
        DB_DIR   = os.path.join(BASE_DIR, "resources", "database")
        KEY_PATH = os.path.join(DB_DIR, "key.key")
        DB_PATH  = os.path.join(DB_DIR, "starpmk_database.db")

        # === Create all necessary folders === #
        resource_dirs = [
            DB_DIR,
            os.path.join(BASE_DIR, "resources", "landlords"),
            os.path.join(BASE_DIR, "resources", "properties"),
            os.path.join(BASE_DIR, "resources", "tenants"),
            os.path.join(BASE_DIR, "resources", "tenancies"),
            os.path.join(BASE_DIR, "resources", "backups"),
            os.path.join(BASE_DIR, "resources", "temp_preview"),
        ]
        for d in resource_dirs: # Create each directory if it doesn't exist
            os.makedirs(d, exist_ok=True)

        # === Generate encryption key if missing === #
        if not os.path.exists(KEY_PATH): # Check if the key file exists
            key = Fernet.generate_key() # Generate a new key
            with open(KEY_PATH, "wb") as key_file: # Write the key to the file
                key_file.write(key)
        with open(KEY_PATH, "rb") as key_file: # Read the key from the file
            key = key_file.read()
        fernet = Fernet(key) # Create a Fernet object for encryption/decryption

        # === Connect to SQLite and enforce foreign keys === #
        conn = sqlite3.connect(DB_PATH) # Connect to the SQLite database
        conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign key constraints
        cur = conn.cursor() # Create a cursor object to execute SQL commands

        # === Table definitions === #
        TABLES = {
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    username    TEXT    UNIQUE NOT NULL,
                    password    TEXT    NOT NULL,
                    is_admin    INTEGER NOT NULL DEFAULT 0
                );
            """,
            "activity_logs": """
                CREATE TABLE IF NOT EXISTS activity_logs (
                    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    user        TEXT,
                    action      TEXT,
                    details     TEXT,
                    timestamp   TEXT,
                    FOREIGN KEY (user) REFERENCES users(username) ON DELETE SET NULL
                );
            """,
            "landlords": """
                CREATE TABLE IF NOT EXISTS landlords (
                    landlord_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name  TEXT,
                    last_name   TEXT,
                    email       TEXT,
                    phone       TEXT,
                    address     TEXT,
                    status      TEXT
                );
            """,
            "landlord_documents": """
                CREATE TABLE IF NOT EXISTS landlord_documents (
                    doc_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    landlord_id INTEGER,
                    doc_type    TEXT,
                    doc_name    TEXT,
                    file_path   TEXT,
                    uploaded_date TEXT,
                    expiry_date TEXT,
                    FOREIGN KEY (landlord_id) REFERENCES landlords (landlord_id) ON DELETE CASCADE
                );
            """,
            "properties": """
                CREATE TABLE IF NOT EXISTS properties (
                    property_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    door_number TEXT,
                    street      TEXT,
                    postcode    TEXT,
                    area        TEXT,
                    city        TEXT,
                    bedrooms    INTEGER,
                    property_type TEXT,
                    price       REAL,
                    availability_date TEXT,
                    landlord_id INTEGER,
                    image_path  TEXT,
                    status      TEXT,
                    notes       TEXT,
                    FOREIGN KEY (landlord_id) REFERENCES landlords (landlord_id) ON DELETE SET NULL
                );
            """,
            "property_images": """
                CREATE TABLE IF NOT EXISTS property_images (
                    image_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id   INTEGER,
                    image_path    TEXT,
                    uploaded_date TEXT,
                    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE
                );
            """,
            "property_documents": """
                CREATE TABLE IF NOT EXISTS property_documents (
                    doc_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id INTEGER,
                    doc_type    TEXT,
                    doc_name    TEXT,
                    file_path   TEXT,
                    uploaded_date TEXT,
                    expiry_date TEXT,
                    FOREIGN KEY (property_id) REFERENCES properties (property_id) ON DELETE CASCADE
                );
            """,
            "tenants": """
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name  TEXT,
                    last_name   TEXT,
                    email       TEXT,
                    phone       TEXT,
                    date_of_birth TEXT,
                    nationality TEXT,
                    emergency_contact TEXT,
                    status      TEXT
                );
            """,
            "tenant_documents": """
                CREATE TABLE IF NOT EXISTS tenant_documents (
                    doc_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id   INTEGER,
                    doc_type    TEXT,
                    doc_name    TEXT,
                    file_path   TEXT,
                    uploaded_date TEXT,
                    expiry_date TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
                );
            """,
            "tenancies": """
                CREATE TABLE IF NOT EXISTS tenancies (
                    tenancy_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id     INTEGER,
                    start_date      TEXT,
                    end_date        TEXT,
                    rent_amount     REAL,
                    deposit_amount  REAL,
                    status          TEXT,
                    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE
                );
            """,
            "tenancy_tenants": """
                CREATE TABLE IF NOT EXISTS tenancy_tenants (
                    tenancy_id    INTEGER,
                    tenant_id     INTEGER,
                    PRIMARY KEY (tenancy_id, tenant_id),
                    FOREIGN KEY (tenancy_id) REFERENCES tenancies(tenancy_id) ON DELETE CASCADE,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
                );
            """,
            "tenancy_documents": """
                CREATE TABLE IF NOT EXISTS tenancy_documents (
                    doc_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenancy_id  INTEGER,
                    doc_type    TEXT,
                    doc_name    TEXT,
                    file_path   TEXT,
                    uploaded_date TEXT,
                    expiry_date TEXT,
                    FOREIGN KEY (tenancy_id) REFERENCES tenancies(tenancy_id) ON DELETE CASCADE
                );
            """,
            "payments": """
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenancy_id  INTEGER,
                    tenant_id   INTEGER,
                    payment_date TEXT,
                    due_date    TEXT,
                    amount      REAL,
                    method      TEXT,
                    status      TEXT,
                    payment_type TEXT,
                    notes       TEXT,
                    FOREIGN KEY (tenancy_id) REFERENCES tenancies (tenancy_id) ON DELETE CASCADE,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
                );
            """,
            "maintenance": """
                CREATE TABLE IF NOT EXISTS maintenance (
                    maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id INTEGER,
                    issue       TEXT,
                    description TEXT,
                    date_reported TEXT,
                    status      TEXT,
                    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE
                );
            """,
        }

        # === Execute table creations === #
        for name, ddl in TABLES.items(): # Loop through each table definition
            cur.execute(ddl) # Execute the SQL command to create the table

        # === Seed default admin user === # 
        cur.execute("SELECT 1 FROM users WHERE username = ?;", ("admin",)) # Check if the admin user already exists
        # If not, create the admin user with a default password, the user can change it later
        # The password is hashed using the hash_password function
        if not cur.fetchone():
            admin_pw_hash = hash_password("12345")
            cur.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?);",
                ("admin", admin_pw_hash, 1)
            )

        conn.commit() # Commit the changes to the database
        conn.close() # Close the database connection
        print("✅ Database and folders initialized.") # Print success message

    except Exception as e: # Catch any exceptions that occur during the process
        print(f"❌ Error initializing database: {e}") # Print error message
        sys.exit(1) # Exit the script with an error code

if __name__ == "__main__":
    main()