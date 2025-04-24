import sqlite3
import sys
import os
import hashlib
import shutil

sys.path.append(os.path.dirname(os.path.dirname(__file__))) # Adjust the path to the parent directory
from config import DB_PATH, DB_DIR

def connect_db():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def backup_database():
    if os.path.exists(DB_PATH):
        backup_path = f"{DB_PATH}.backup"
        shutil.copy2(DB_PATH, backup_path)
        print(f"🗄️ Backup created at {backup_path}")

def drop_tables(cursor):
    print("🔨 Dropping existing tables...")

    tables_to_drop = [
        "tenancy_tenants", "payments", "maintenance", "tenants", "tenancies",
        "property_images", "property_documents", "properties", "landlords", "landlord_documents",
        "users", "activity_logs", "tenant_documents", "tenancy_documents"
    ]

    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"✅ Dropped table: {table}")

def create_tables(cursor):
    table_queries = {
        "users": '''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                is_admin INTEGER DEFAULT 0
            )''',
        "activity_logs": '''CREATE TABLE IF NOT EXISTS activity_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT,
                FOREIGN KEY (user) REFERENCES users(username) ON DELETE SET NULL
            )''',
        "landlords": '''CREATE TABLE IF NOT EXISTS landlords (
                landlord_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                status TEXT
            )''',
        "landlord_documents": '''CREATE TABLE IF NOT EXISTS landlord_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                landlord_id INTEGER,
                doc_type TEXT,
                doc_name TEXT,
                file_path TEXT,
                uploaded_date TEXT,
                expiry_date TEXT,
                FOREIGN KEY (landlord_id) REFERENCES landlords (landlord_id) ON DELETE CASCADE
            )''',
        "properties": '''CREATE TABLE IF NOT EXISTS properties (
                property_id INTEGER PRIMARY KEY AUTOINCREMENT,
                door_number TEXT,
                street TEXT,
                postcode TEXT,
                area TEXT,
                city TEXT,
                bedrooms INTEGER,
                property_type TEXT,
                price REAL,
                availability_date TEXT,
                landlord_id INTEGER,
                image_path TEXT,
                status TEXT,
                notes TEXT,
                FOREIGN KEY (landlord_id) REFERENCES landlords (landlord_id) ON DELETE SET NULL
            )''',
        "property_images": '''CREATE TABLE IF NOT EXISTS property_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER,
                image_path TEXT,
                uploaded_date TEXT,
                FOREIGN KEY (property_id) REFERENCES properties (property_id) ON DELETE CASCADE
            )''',
        "property_documents": '''CREATE TABLE IF NOT EXISTS property_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER,
                doc_type TEXT,
                doc_name TEXT,
                file_path TEXT,
                uploaded_date TEXT,
                expiry_date TEXT,
                FOREIGN KEY (property_id) REFERENCES properties (property_id) ON DELETE CASCADE
            )''',
        "tenants": '''CREATE TABLE IF NOT EXISTS tenants (
                tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                date_of_birth TEXT,
                nationality TEXT,
                emergency_contact TEXT,
                status TEXT
            )''',
        "tenant_documents": '''CREATE TABLE IF NOT EXISTS tenant_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER,
                doc_type TEXT,
                doc_name TEXT,
                file_path TEXT,
                uploaded_date TEXT,
                expiry_date TEXT,
                FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
            )''',
        "tenancies": '''CREATE TABLE IF NOT EXISTS tenancies (
                tenancy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER,
                start_date TEXT,
                end_date TEXT,
                rent_amount REAL,
                deposit_amount REAL,
                status TEXT,
                FOREIGN KEY (property_id) REFERENCES properties (property_id) ON DELETE CASCADE
            )''',
        "tenancy_tenants": '''CREATE TABLE IF NOT EXISTS tenancy_tenants (
                tenancy_id INTEGER,
                tenant_id INTEGER,
                PRIMARY KEY (tenancy_id, tenant_id),
                FOREIGN KEY (tenancy_id) REFERENCES tenancies (tenancy_id) ON DELETE CASCADE,
                FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
            )''',
        "tenancy_documents": '''CREATE TABLE IF NOT EXISTS tenancy_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenancy_id INTEGER,
                doc_type TEXT,
                doc_name TEXT,
                file_path TEXT,
                uploaded_date TEXT,
                expiry_date TEXT,
                FOREIGN KEY (tenancy_id) REFERENCES tenancies (tenancy_id) ON DELETE CASCADE
            )''',
        "payments": '''CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenancy_id INTEGER,
                tenant_id INTEGER,
                payment_date TEXT,
                due_date TEXT,
                amount REAL,
                method TEXT,
                status TEXT,
                payment_type TEXT,
                notes TEXT,
                FOREIGN KEY (tenancy_id) REFERENCES tenancies (tenancy_id) ON DELETE CASCADE,
                FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
            )''',
        "maintenance": '''CREATE TABLE IF NOT EXISTS maintenance (
                maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER,
                issue TEXT,
                description TEXT,
                date_reported TEXT,
                status TEXT,
                FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE
            )'''
    }

    print("🛠️ Creating tables...")
    for table_name, create_query in table_queries.items():
        cursor.execute(create_query)
        print(f"✅ Created table: {table_name}")

def create_default_admin(cursor):
    print("👤 Creating default admin user...")
    username = "admin"
    password = hash_password("12345")  # hashed password

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, 1))
        print("✅ Admin user created with password '12345'")
    else:
        print("ℹ️ Admin user already exists.")

def initialize_database():
    conn = connect_db()
    cursor = conn.cursor()

    drop_tables(cursor)
    create_tables(cursor)
    create_default_admin(cursor)

    conn.commit()
    conn.close()

    print("✅ Database initialized!")

if __name__ == "__main__":
    initialize_database()
