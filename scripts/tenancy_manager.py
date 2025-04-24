import glob
import os
import shutil
from PySide6.QtWidgets import QMessageBox
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.tenancy_details_page import TenancyDetailsPage


class TenancyManager(BaseManager):
    def __init__(self, filter_ending_soon=False, parent=None): # The filter_ending_soon parameter
                                                               # is for the dashbaord card
        self.db = DatabaseManager()
        self.filter_ending_soon = filter_ending_soon

        super().__init__(
            title="Tenancy Management",
            search_placeholder="Search by tenant name, property address, or status...",
            columns=[
                "ID", "Tenants", "Property", "Start Date", "End Date",
                "Rent (£)", "Status"
            ],
            parent=parent
        )
        self.load_data()

    def get_data(self):
        query = """
            SELECT
                tn.tenancy_id,
                p.door_number || ' ' || p.street || ', ' || p.postcode AS property_address,
                tn.start_date,
                tn.end_date,
                tn.rent_amount,
                tn.status,
                GROUP_CONCAT(t.first_name || ' ' || t.last_name, ', ') AS tenant_names
            FROM tenancies tn
            JOIN tenancy_tenants tt ON tn.tenancy_id = tt.tenancy_id
            JOIN tenants t ON tt.tenant_id = t.tenant_id
            JOIN properties p ON tn.property_id = p.property_id
        """

        if self.filter_ending_soon:
            query += " WHERE tn.end_date <= DATE('now', '+30 day')"

        query += " GROUP BY tn.tenancy_id"

        with self.db.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in results]



    def extract_row_values(self, item):
        return [
            item["tenancy_id"],
            item["tenant_names"],
            item["property_address"],
            item["start_date"],
            item["end_date"],
            item["rent_amount"],
            item["status"]
        ]


    def open_details_dialog(self, item=None):
        dialog = TenancyDetailsPage(tenancy_data=item)
        if dialog.exec():
            self.load_data()

    def delete_item(self, item):
        tenancy_id = item["tenancy_id"]

        with self.db.cursor() as cur:
            cur.execute("DELETE FROM tenancies WHERE tenancy_id = ?", (tenancy_id,))
            cur.execute("DELETE FROM tenancy_tenants WHERE tenancy_id = ?", (tenancy_id,))

        # Remove tenancy folder(s) matching pattern
        pattern = os.path.join("tenancies", f"{tenancy_id}_*")
        for folder in glob.glob(pattern):
            shutil.rmtree(folder, ignore_errors=True)

        self.load_data()

