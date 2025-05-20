import glob
import os
import shutil
from PySide6.QtWidgets import QMessageBox, QHeaderView
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.tenancy_details_page import TenancyDetailsPage


# TenancyManager class inherits from BaseManager
# This class is responsible for managing the tenancies in the application
# It handles the display of tenancy data, including tenant names, property addresses,
# start and end dates, rent amounts, and status
# It also provides functionality for adding, editing, and deleting tenancies
# The class uses a database manager to interact with the SQLite database

class TenancyManager(BaseManager): # This class inherits from BaseManager
    def __init__(self, filter_ending_soon=False, parent=None): # The filter_ending_soon parameter
                                                               # is for the dashbaord card
        self.db = DatabaseManager() # This is the database manager instance
        self.filter_ending_soon = filter_ending_soon # This is a flag to filter tenancies ending soon

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

    def get_data(self): # This method retrieves data from the database
        # The SQL query retrieves tenancy information, including tenant names and property addresses
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

        if self.filter_ending_soon: # If the filter_ending_soon flag is set, filter tenancies ending soon
            query += " WHERE tn.end_date <= DATE('now', '+30 day')"

        query += " GROUP BY tn.tenancy_id" # Group by tenancy ID to avoid duplicates

        with self.db.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in results]



    def extract_row_values(self, item): # This method extracts the values from a single row of data
        # It returns a list of values to be displayed in the table
        return [
            item["tenancy_id"],
            item["tenant_names"],
            item["property_address"],
            item["start_date"],
            item["end_date"],
            item["rent_amount"],
            item["status"]
        ]


    def open_details_dialog(self, item=None): # This method opens the details dialog for adding or editing a tenancy
        # If no item is provided, it means we are adding a new tenancy
        dialog = TenancyDetailsPage(tenancy_data=item)
        if dialog.exec():
            self.load_data()

    def delete_item(self, item): # This method deletes a tenancy from the database
        tenancy_id = item["tenancy_id"] # Get the tenancy ID from the item

        with self.db.cursor() as cur:
            cur.execute("DELETE FROM tenancies WHERE tenancy_id = ?", (tenancy_id,)) # Delete the tenancy
            cur.execute("DELETE FROM tenancy_tenants WHERE tenancy_id = ?", (tenancy_id,)) # Delete the associated tenants

        # Remove tenancy folder(s) matching pattern
        pattern = os.path.join("tenancies", f"{tenancy_id}_*")
        for folder in glob.glob(pattern): # Use glob to find all folders matching the pattern. Glod is a module for Unix style pathname pattern expansion. 
            # In simple terms, it is used to find files and directories matching a specified pattern.
            shutil.rmtree(folder, ignore_errors=True)

        self.load_data()

    def refresh_table(self):
        # Let BaseManager populate & stretch columns
        super().refresh_table()
        # Then lock ID narrow (60px) and Property wide (300px)

        # ─── CUSTOM COLUMN WIDTHS ───────────────────────── #
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_widget.setColumnWidth(0, 60)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_widget.setColumnWidth(2, 300)
        # ────────────────────────────────────────────────── #
