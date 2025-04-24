import os
import shutil
import glob
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.tenant_details_page import TenantDetailsPage
from PySide6.QtWidgets import QDialog


class TenantManager(BaseManager):
    def __init__(self):
        self.db = DatabaseManager()
        self.tenants = []
        
        super().__init__(
            title="Tenant Management",
            search_placeholder="Search tenants by name, email, phone...",
            columns=["Full Name", "Email", "Phone", "Status"]
        )
        self.load_tenants()
        self.load_data()

    def load_tenants(self):
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT tenant_id, first_name, last_name, email, phone,
                       date_of_birth, nationality,
                       emergency_contact,
                       status
                FROM tenants
            """)
            rows = cur.fetchall()
            self.tenants = [
                {
                    "id": row[0],
                    "first_name": row[1],
                    "last_name": row[2],
                    "email": row[3],
                    "phone": row[4],
                    "date_of_birth": row[5],
                    "nationality": row[6],
                    "emergency_contact": row[7],
                    "status": row[8]
                }
                for row in rows
            ]

    def get_data(self):
        return self.tenants

    def extract_row_values(self, item):
        full_name = f"{item['first_name']} {item['last_name']}"
        return [full_name, item["email"], item["phone"], item["status"]]

    def filter_item(self, item, query):
        query = query.lower()
        return (
            query in item["first_name"].lower()
            or query in item["last_name"].lower()
            or query in item["email"].lower()
            or query in item["phone"].lower()
            or query in item["status"].lower()
        )

    def open_details_dialog(self, item):
        dialog = TenantDetailsPage(tenant_data=item)

        while True:
            result = dialog.exec()
            if result == QDialog.Accepted:
                data = dialog.collect_data()
                if data is None:
                    continue  # if Validation failed, keep dialog open

                with self.db.cursor() as cur:
                    if item:
                        cur.execute("""
                            UPDATE tenants
                            SET first_name = ?, last_name = ?, email = ?, phone = ?,
                                date_of_birth = ?, nationality = ?,
                                emergency_contact = ?, status = ?
                            WHERE tenant_id = ?
                        """, (
                            data["first_name"], data["last_name"], data["email"], data["phone"],
                            data["date_of_birth"], data["nationality"],
                            data["emergency_contact"], data["status"], item["id"]
                        ))
                    else:
                        cur.execute("""
                            INSERT INTO tenants (
                                first_name, last_name, email, phone,
                                date_of_birth, nationality,
                                emergency_contact, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data["first_name"], data["last_name"], data["email"], data["phone"],
                            data["date_of_birth"], data["nationality"],
                            data["emergency_contact"], data["status"]
                        ))
                        new_id = cur.lastrowid
                        data["id"] = new_id
                        dialog.tenant_data = data

                self.load_tenants()
                self.load_data()
                break
            else:
                break  # Dialog was cancelled

    def delete_item(self, item):
        tenant_id = item["id"]

        with self.db.cursor() as cur:
            cur.execute("DELETE FROM tenants WHERE tenant_id = ?", (tenant_id,))

        # Delete tenant folder(s) matching pattern
        pattern = os.path.join("tenants", f"{tenant_id}_*")
        for folder in glob.glob(pattern):
            shutil.rmtree(folder, ignore_errors=True)

        self.load_tenants()
        self.load_data()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()

