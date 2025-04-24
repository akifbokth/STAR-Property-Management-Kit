from PySide6.QtWidgets import QMessageBox, QDialog
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.landlord_details_page import LandlordDetailsPage
import os
import shutil
import glob


class LandlordManager(BaseManager):
    def __init__(self, parent=None):
        self.db = DatabaseManager()
        super().__init__(
            title="Landlord Management",
            search_placeholder="Search by name, email, or phone...",
            columns=["ID", "Name", "Email", "Phone"],
            parent=parent
        )
        self.load_data()

    def get_data(self):
        query = """
            SELECT
                landlord_id,
                first_name,
                last_name,
                email,
                phone
            FROM landlords
            ORDER BY first_name, last_name
        """
        with self.db.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            return [
                {
                    "landlord_id": row[0],
                    "first_name": row[1],
                    "last_name": row[2],
                    "email": row[3],
                    "phone": row[4],
                    "name": f"{row[1]} {row[2]}"
                }
                for row in results
            ]

    def extract_row_values(self, item):
        return [
            item["landlord_id"],
            item["name"],
            item["email"],
            item["phone"]
        ]

    def open_details_dialog(self, item):
        dialog = LandlordDetailsPage(landlord_data=item)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.load_data()

    def delete_item(self, item):
        landlord_id = item["landlord_id"]

        with self.db.cursor() as cur:
            cur.execute("DELETE FROM landlords WHERE landlord_id = ?", (landlord_id,))

        # Remove landlord folder(s) matching pattern
        pattern = os.path.join("landlords", f"{landlord_id}_*")
        for folder in glob.glob(pattern):
            shutil.rmtree(folder, ignore_errors=True)

        self.load_data()