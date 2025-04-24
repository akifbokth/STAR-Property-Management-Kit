import os
import shutil
import glob
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.property_details_page import PropertyDetailsPage
from PyQt5.QtWidgets import QDialog


class PropertyManager(BaseManager):
    def __init__(self, filter_vacant=False):
        self.db = DatabaseManager()
        self.properties = []
        self.filter_vacant = filter_vacant

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
        

    def load_properties(self):
        with self.db.cursor() as cur:
            if self.filter_vacant:
                cur.execute("""
                    SELECT p.property_id, p.door_number, p.street, p.postcode, p.area, p.city,
                        p.bedrooms, p.property_type, p.price,
                        p.availability_date, p.status, p.notes
                    FROM properties p
                    WHERE NOT EXISTS (
                        SELECT 1 FROM tenancies t
                        WHERE t.property_id = p.property_id AND DATE('now') BETWEEN t.start_date AND t.end_date
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

    def get_data(self):
        return self.properties

    def extract_row_values(self, item):
        return [
            item["door_number"],
            item["street"],
            item["postcode"],
            item["area"],
            item["city"],
            item["price"],
            item["property_type"],
            item["availability_date"],
            item["status"]
        ]

    def filter_item(self, item, query):
        query = query.lower()
        return (
            query in item["postcode"].lower()
            or query in item["city"].lower()
            or query in item["property_type"].lower()
        )

    def open_details_dialog(self, item):
        dialog = PropertyDetailsPage(property_data=item)

        while True:
            result = dialog.exec()
            if result == QDialog.Accepted:
                data = dialog.collect_data()
                if data is None:
                    continue  # validation failed, loop again

                with self.db.cursor() as cur:
                    if item:
                        cur.execute("""
                            UPDATE properties
                            SET door_number = ?, street = ?, postcode = ?, area = ?, city = ?,
                                bedrooms = ?, property_type = ?, price = ?, availability_date = ?, status = ?, notes = ?
                            WHERE property_id = ?
                        """, (
                            data["door_number"], data["street"], data["postcode"], data["area"], data["city"],
                            data["bedrooms"], data["property_type"], data["price"], data["availability_date"],
                            data["status"], data["notes"], item["id"]
                        ))
                    else:
                        cur.execute("""
                            INSERT INTO properties (
                                door_number, street, postcode, area, city,
                                bedrooms, property_type, price, availability_date, status, notes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data["door_number"], data["street"], data["postcode"], data["area"], data["city"],
                            data["bedrooms"], data["property_type"], data["price"], data["availability_date"],
                            data["status"], data["notes"]
                        ))
                        
                        new_id = cur.lastrowid
                        data["id"] = new_id
                        dialog.property_data["id"] = new_id

                self.load_properties()
                self.load_data()
                break
            else:
                break  # user cancelled the dialog


    def delete_item(self, item):
        property_id = item["id"]

        with self.db.cursor() as cur:
            cur.execute("DELETE FROM properties WHERE property_id = ?", (property_id,))

        # Delete property folder(s) matching pattern
        pattern = os.path.join("properties", f"{property_id}_*")
        for folder in glob.glob(pattern):
            shutil.rmtree(folder, ignore_errors=True)

        self.load_properties()
        self.load_data()
