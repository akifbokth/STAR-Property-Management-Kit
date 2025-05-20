from PySide6.QtWidgets import QMessageBox, QDialog
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.landlord_details_page import LandlordDetailsPage
import os
import shutil
import glob
from config import LANDLORDS_DIR


# LandlordManager class to manage landlord data
# This class inherits from BaseManager and provides a table view for landlords.
# It allows for the addition, deletion, and editing of landlord information.
# The landlords are stored in a SQLite database and can be searched by name, email, or phone number.

class LandlordManager(BaseManager): # This class inherits from BaseManager to create a custom table view
    def __init__(self, parent=None):
        self.db = DatabaseManager()
        super().__init__(
            title="Landlord Management",
            search_placeholder="Search by name, email, or phone...",
            columns=["Name", "Email", "Phone", "Status"],
            parent=parent
        )
        self.load_data()

    def get_data(self): # Fetch landlord data from the database
        query = """
            SELECT
                landlord_id,
                first_name,
                last_name,
                email,
                phone,
                status
            FROM landlords
            ORDER BY first_name, last_name
        """
        with self.db.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        landlords = []
        for row in rows:
            landlords.append({
                "landlord_id": row[0],
                "first_name":  row[1],
                "last_name":   row[2],
                "email":       row[3],
                "phone":       row[4],
                "status":      row[5],
                "name":        f"{row[1]} {row[2]}"
            })
        return landlords

    def extract_row_values(self, item): # Extract values from the landlord item for display in the table
        return [
            item["name"],
            item["email"],
            item["phone"],
            item.get("status", "")
        ]

    def open_details_dialog(self, item): # Open the landlord details dialog for adding or editing landlord information
        dialog = LandlordDetailsPage(landlord_data=item)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.load_data()

    def delete_item(self, item): # Delete the selected landlord from the database
        landlord_id = item["landlord_id"]
        with self.db.cursor() as cur:
            cur.execute(
                "DELETE FROM landlords WHERE landlord_id = ?",
                (landlord_id,)
            )
        # Clean up folder in resources\landlords
        # Checks if the folder exists before attempting to delete it
        pattern = os.path.join(LANDLORDS_DIR, f"{landlord_id}_*")
        for folder in glob.glob(pattern):
            shutil.rmtree(folder, ignore_errors=True)

        self.load_data()