import os
import shutil
import glob
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.property_details_page import PropertyDetailsPage
from PySide6.QtWidgets import QDialog
from config import PROPERTIES_DIR


# PropertyManager class to manage property records
# This class inherits from BaseManager and provides a table view for properties.
# It allows for the addition, deletion, and updating of property records.
# The properties are stored in a SQLite database and can be filtered by availability.

class PropertyManager(BaseManager): # This class inherits from BaseManager to create a custom table view
    def __init__(self, filter_vacant=False):
        self.db = DatabaseManager() # Database manager instance
        self.properties = [] # List to hold property data
        self.filter_vacant = filter_vacant # Flag to filter vacant properties

        super().__init__(
            title="Property Management",
            search_placeholder="Search properties by postcode, city, or type...",
            columns=[
                "Door No/Building", "Street", "Postcode", "Area", "City",
                "Rent", "Property Type", "Available", "Status"
            ]
        )
        self.load_properties()
        self.load_data()

    def load_properties(self): # Load properties from the database
        with self.db.cursor() as cur:
            if self.filter_vacant:
                cur.execute("""
                    SELECT property_id, door_number, street, postcode, area, city,
                        bedrooms, property_type, price,
                        availability_date, status, notes
                    FROM properties p
                    WHERE NOT EXISTS (
                      SELECT 1 FROM tenancies t
                      WHERE t.property_id = p.property_id
                        AND DATE('now') BETWEEN t.start_date AND t.end_date
                    )
                """)
            else:
                cur.execute("""
                    SELECT property_id, door_number, street, postcode, area, city,
                        bedrooms, property_type, price,
                        availability_date, status, notes
                    FROM properties
                """)
            rows = cur.fetchall()
            self.properties = [
                {
                    "id": row[0],
                    "door_number": row[1],
                    "street": row[2],
                    "postcode": row[3],
                    "area": row[4],
                    "city": row[5],
                    "bedrooms": row[6],
                    "property_type": row[7],
                    "price": row[8],
                    "availability_date": row[9],
                    "status": row[10],
                    "notes": row[11],
                }
                for row in rows
            ]

    def get_data(self): # Fetch property data from the database
        return self.properties

    def extract_row_values(self, item): # Extract values from the property item for display in the table
        return [
            item["door_number"],
            item["street"],
            item["postcode"],
            item["area"],
            item["city"],
            item["price"],
            item["property_type"],
            item["availability_date"],
            item["status"],
        ]

    def filter_item(self, item, query): # Filter properties based on the search query
        query = query.lower()
        return (
            query in item["postcode"].lower()
            or query in item["city"].lower()
            or query in item["property_type"].lower()
        )

    def open_details_dialog(self, item): # Open the Property Details dialog for adding or editing a property
        is_new = item is None # Check if the item is new or existing
        data = {} if is_new else item.copy() # Copy the item data if it exists

        dialog = PropertyDetailsPage(property_data=data) # Create a new PropertyDetailsPage dialog
        while True: # Loop until the dialog is closed
            result = dialog.exec() # Execute the dialog
            if result != QDialog.Accepted: # Check if the dialog was accepted
                break

            new_data = dialog.collect_data() # Collect data from the dialog
            if new_data is None: # Check if the data is valid
                continue

            with self.db.cursor() as cur:
                if not is_new:
                    # Update existing property
                    cur.execute(
                        """
                        UPDATE properties
                        SET door_number=?, street=?, postcode=?, area=?, city=?,
                            bedrooms=?, property_type=?, price=?,
                            availability_date=?, status=?, notes=?
                        WHERE property_id=?
                        """,
                        (
                            new_data["door_number"], new_data["street"],
                            new_data["postcode"], new_data["area"],
                            new_data["city"], new_data["bedrooms"],
                            new_data["property_type"], new_data["price"],
                            new_data["availability_date"], new_data["status"],
                            new_data["notes"], data["id"],
                        )
                    )
                else:
                    # Insert new property
                    cur.execute(
                        """
                        INSERT INTO properties (
                            door_number, street, postcode, area, city,
                            bedrooms, property_type, price,
                            availability_date, status, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_data["door_number"], new_data["street"],
                            new_data["postcode"], new_data["area"],
                            new_data["city"], new_data["bedrooms"],
                            new_data["property_type"], new_data["price"],
                            new_data["availability_date"], new_data["status"],
                            new_data["notes"],
                        )
                    )
                    new_data["id"] = cur.lastrowid # Get the last inserted ID
                    data = new_data # Update the data with the new property ID

            self.load_properties()
            self.load_data()
            break

    def delete_item(self, item): # Delete a property record from the database and its associated folder
        property_id = item["id"] # Get the property ID from the item
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM properties WHERE property_id = ?", (property_id,))

        # cleanup folder in resources\properties
        # Checks if the folder exists before attempting to delete it
        pattern = os.path.join(PROPERTIES_DIR, f"{property_id}_*")
        for folder in glob.glob(pattern):
            shutil.rmtree(folder, ignore_errors=True)

        self.load_properties()
        self.load_data()
