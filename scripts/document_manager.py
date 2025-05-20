import os
import shutil
import datetime
import tempfile
import webbrowser
from scripts import encryption_manager
from scripts.encryption_manager import encrypt_file
from scripts.database_manager import DatabaseManager
from config import STORAGE_PATHS, TEMP_PREVIEW_DIR

TEMP_FILES_TO_CLEAN = [] # List to keep track of temporary files created during the process
# This will be used to clean up temporary files after the process is done

# DocumentManager class to manage document storage, encryption, and database interactions
# This class handles the upload, retrieval, and deletion of documents for different entities
# (tenants, landlords, properties, tenancies) in the database.
# It also manages the encryption and decryption of files, ensuring that sensitive information is stored securely.

class DocumentManager:
    def __init__(self):
        self.db = DatabaseManager()

        # Define the mapping of entity types to their respective database tables and folder names
        # This mapping is used to determine how to store and retrieve documents for each entity type
        self.table_map = {
            "tenant": {
                "table": "tenant_documents",
                "id_field": "tenant_id",
                "folder_name_sql": "first_name || ' ' || last_name",
                "name_table": "tenants"
            },
            "landlord": {
                "table": "landlord_documents",
                "id_field": "landlord_id",
                "folder_name_sql": "first_name || ' ' || last_name",
                "name_table": "landlords"
            },
            "property": {
                "table": "property_documents",
                "id_field": "property_id",
                "folder_name_sql": "door_number || ' ' || street || ', ' || postcode",
                "name_table": "properties" 
            },
            "tenancy": {
                "table": "tenancy_documents",
                "id_field": "tenancy_id",
                "folder_name_sql": "start_date || '_' || (SELECT door_number || '_' || street || '_' || postcode FROM properties WHERE properties.property_id = tenancies.property_id)",
                "name_table": "tenancies"
            }
        }

    # Define the mapping of entity types to their respective storage paths
    def _get_encrypted_path(self, entity_type: str, entity_id: int, filename: str) -> str:
        # Build the folder name (e.g. "4_PropertyName")
        folder_name = self.get_folder_name(entity_type, entity_id)

        # Get the base storage folder from your config
        base_dir = STORAGE_PATHS[entity_type]

        # Return the full path to the .encrypted file
        return os.path.join(base_dir, folder_name, filename)

    # Ensure the entity folders exist in the storage path
    # This method creates the necessary folders for storing documents based on the entity type
    def ensure_entity_folders_exist(self, entity_type, folder_name):
        base = STORAGE_PATHS[entity_type]
        path = os.path.join(base, folder_name)
        os.makedirs(path, exist_ok=True)
        return path

    # Get the folder name for the entity based on its type and ID
    # This method retrieves the folder name from the database based on the entity type and ID
    def get_folder_name(self, entity_type, entity_id):
        with self.db.cursor() as cur:
            config = self.table_map[entity_type]
            query = f"SELECT {config['folder_name_sql']} AS name FROM {config.get('name_table', config['table'])} WHERE {config['id_field']} = ?"
            cur.execute(query, (entity_id,))
            result = cur.fetchone()
            if result and result[0]:
                name = result[0]
                sanitized = "_".join(name.split())  # Replaces spaces with _
                sanitized = "".join(c if c.isalnum() or c == "_" else "" for c in sanitized)
                return f"{entity_id}_{sanitized}"
        return str(entity_id)

    # Upload a document for a specific entity type and ID
    # This method handles the encryption of the document and stores it in the appropriate folder
    def upload_document(self, entity_type, entity_id, doc_name, doc_type, expiry_date, file_path):
        try:
            config = self.table_map[entity_type]

            folder_name = self.get_folder_name(entity_type, entity_id)
            print("🔍 Folder Name:", folder_name)

            storage_path = self.ensure_entity_folders_exist(entity_type, folder_name)
            print("📂 Storage Path:", storage_path)

            filename = os.path.basename(file_path)
            encrypted_filename = f"{int(os.path.getmtime(file_path))}_{filename}.encrypted"

            full_path = os.path.join(storage_path, encrypted_filename)
            print("🔐 Full Path to Encrypt To:", full_path)

            encrypt_file(file_path, full_path)

            with self.db.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {config['table']}
                    ({config['id_field']}, doc_name, doc_type, file_path, expiry_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (entity_id, doc_name, doc_type, encrypted_filename, expiry_date))

            self.log_activity("Document Upload", f"{doc_name} uploaded for {entity_type} {entity_id}")
            return True

        except Exception as e: # Handle any exceptions that occur during the upload process
            print("[ERROR] Upload failed:", e)
            return False

    # Retrieve a document for a specific entity type and ID
    # This method retrieves the document from the storage path and returns its details
    def get_documents(self, entity_type, entity_id):
        try:
            config = self.table_map[entity_type]
            with self.db.cursor() as cur:
                cur.execute(f"""
                    SELECT doc_id, doc_name, doc_type, file_path, expiry_date
                    FROM {config['table']}
                    WHERE {config['id_field']} = ?
                """, (entity_id,))
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "filename": row[3],
                        "expiry": row[4]
                    }
                    for row in cur.fetchall()
                ]

        except Exception as e: # Handle any exceptions that occur during the retrieval process
            print("[ERROR] Get documents failed:", e)
            return []

    # Delete a document for a specific entity type and ID
    # This method removes the document from the storage path and deletes its record from the database
    def delete_document(self, entity_type, entity_id, filename):
        try:
            config = self.table_map[entity_type]
            folder_name = self.get_folder_name(entity_type, entity_id)
            path = os.path.join(STORAGE_PATHS[entity_type], folder_name, filename)

            if os.path.exists(path):
                os.remove(path)

            with self.db.cursor() as cur:
                cur.execute(f"""
                    DELETE FROM {config['table']}
                    WHERE {config['id_field']} = ? AND file_path = ?
                """, (entity_id, filename))

            self.log_activity(
                "Document Delete",
                f"{filename} removed from {entity_type} {entity_id}"
            )
            return True
        
        except Exception as e:
            print("[ERROR] Delete failed:", e)
            return False

    # Decrypt a document to a temporary location
    # This method decrypts the document and returns the path to the decrypted file
    # This is useful for previewing the document without permanently storing it in the local file system
    def decrypt_document_to_temp(self, entity_type: str, entity_id: int, filename: str) -> str | None:
        try:
            # Build the path to the .encrypted file
            encrypted_path = self._get_encrypted_path(entity_type, entity_id, filename)
            if not os.path.exists(encrypted_path):
                print(f"[ERROR] Encrypted file not found: {encrypted_path}")
                return None

            # Ensure the temp_preview folder (resources/temp_preview) exists
            os.makedirs(TEMP_PREVIEW_DIR, exist_ok=True)

            # Decrypted target path (remove the .encrypted suffix)
            target = os.path.join(
                TEMP_PREVIEW_DIR,
                filename.replace(".encrypted", "")
            )

            # Perform decryption
            encryption_manager.decrypt_file(encrypted_path, target)

            return target
        except Exception as e:
            print("[ERROR] Decrypt failed:", e)
            return None

    # Log activity in the database
    # This method records the actions performed by the user in the activity logs
    def log_activity(self, action, details):
        user = "admin"  # Replace with session user if available
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """
            INSERT INTO activity_logs (user, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        """
        self.db.execute(query, (user, action, details, timestamp))
        print(f"[INFO] Activity logged: {action} - {details}")