import os
import shutil
import datetime
import tempfile
import webbrowser
from scripts import encryption_manager
from scripts.encryption_manager import encrypt_file
from scripts.database_manager import DatabaseManager
from config import STORAGE_PATHS, TEMP_PREVIEW_DIR

TEMP_FILES_TO_CLEAN = []

class DocumentManager:
    def __init__(self):
        self.db = DatabaseManager()

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

    def ensure_entity_folders_exist(self, entity_type, folder_name):
        base = STORAGE_PATHS[entity_type]
        path = os.path.join(base, folder_name)
        os.makedirs(path, exist_ok=True)
        return path

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

        except Exception as e:
            print("[ERROR] Upload failed:", e)
            return False

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

        except Exception as e:
            print("[ERROR] Get documents failed:", e)
            return []

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

            self.db.conn.commit()
            self.log_activity("Document Delete", f"{filename} removed from {entity_type} {entity_id}")
            return True
        except Exception as e:
            print("[ERROR] Delete failed:", e)
            return False

    def decrypt_document_to_temp(self, entity_type, entity_id, filename):
        try:
            config = self.table_map[entity_type]
            folder_name = self.get_folder_name(entity_type, entity_id)
            path = os.path.join(STORAGE_PATHS[entity_type], folder_name, filename)

            if not os.path.exists(path):
                return None

            os.makedirs("temp_preview", exist_ok=True)
            target = os.path.join("temp_preview", filename.replace(".encrypted", ""))
            encryption_manager.decrypt_file(path, target)
            return target
        except Exception as e:
            print("[ERROR] Decrypt failed:", e)
            return None

    def log_activity(self, action, details):
        user = "admin"  # Replace with session user if available
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """
            INSERT INTO activity_logs (user, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        """
        self.db.execute(query, (user, action, details, timestamp))
        print(f"[INFO] Activity logged: {action} - {details}")