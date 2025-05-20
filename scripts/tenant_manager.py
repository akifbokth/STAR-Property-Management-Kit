import os
import shutil
import glob
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.tenant_details_page import TenantDetailsPage
from PySide6.QtWidgets import QDialog
from config import TENANTS_DIR


# TenantManager class inherits from BaseManager
# This class is responsible for managing the tenants in the application
# It handles the display of tenant data, including names, email addresses, phone numbers, date of birth

class TenantManager(BaseManager): # This class inherits from BaseManager
    # The class is responsible for managing tenant data
    def __init__(self):
        self.db = DatabaseManager() # Load database manager instance
        self.tenants = [] # Initialise an empty list to store tenant data
        
        super().__init__(
            title="Tenant Management",
            search_placeholder="Search tenants by name, email, phone...",
            columns=["Full Name", "Email", "Phone", "Status"]
        )
        self.load_tenants() # Load tenant data from the database
        self.load_data() # Load data into the UI table

    def load_tenants(self): # Load tenant data from the database
        # This method retrieves tenant data from the database and stores it in the self.tenants list
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT tenant_id, first_name, last_name, email, phone,
                       date_of_birth, nationality,
                       emergency_contact,
                       status
                FROM tenants
            """)
            rows = cur.fetchall() # Fetch all rows from the query
            self.tenants = [ # Create a list of dictionaries to store tenant data
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

    def get_data(self): # Get tenant data for display in the UI table
        # This method returns the tenant data to be displayed in the UI table
        return self.tenants

    def extract_row_values(self, item): # Extract values from a tenant item for display in the UI table
        # This method takes a tenant item and returns a list of values to be displayed in the UI table
        full_name = f"{item['first_name']} {item['last_name']}"
        return [full_name, item["email"], item["phone"], item["status"]]

    def filter_item(self, item, query): # Filter tenant items based on a search query
        # This method checks if the search query matches any of the tenant's details
        query = query.lower()
        return (
            query in item["first_name"].lower()
            or query in item["last_name"].lower()
            or query in item["email"].lower()
            or query in item["phone"].lower()
            or query in item["status"].lower()
        )

    def open_details_dialog(self, item): # Open the tenant details dialog for editing or adding a new tenant
        dialog = TenantDetailsPage(tenant_data=item) # Create an instance of the TenantDetailsPage dialog
        # The tenant_data parameter is passed to the dialog to pre-fill the fields if editing an existing tenant

        while True: # Loop until the dialog is either accepted or cancelled
            result = dialog.exec() # Show the dialog and wait for user input
            # The exec() method blocks until the dialog is closed
            if result == QDialog.Accepted: # If the dialog is accepted
                data = dialog.collect_data() # Collect data from the dialog
                if data is None: # If data is None, it means validation failed
                    continue  # if Validation failed, keep dialog open

                with self.db.cursor() as cur:

                    if item: # If item is not None, it means we are editing an existing tenant
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

                    else: # If item is None, it means we are adding a new tenant
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
                        new_id = cur.lastrowid # Get the ID of the newly inserted tenant
                        data["id"] = new_id # Add the new ID to the data dictionary
                        dialog.tenant_data = data # Update the tenant_data attribute of the dialog

                self.load_tenants()
                self.load_data()
                break
            else:
                break  # Dialog was cancelled

    def delete_item(self, item): # Delete a tenant item from the database
        tenant_id = item["id"] # Get the ID of the tenant to be deleted

        with self.db.cursor() as cur:
            cur.execute("DELETE FROM tenants WHERE tenant_id = ?", (tenant_id,)) # Delete the tenant from the database

        # cleanup folder in resources\tenants
        # Checks if the folder exists before attempting to delete it
        pattern = os.path.join(TENANTS_DIR, f"{tenant_id}_*") # Create a pattern to match the tenant folder
        for folder in glob.glob(pattern): # Use glob to find all folders matching the pattern
            shutil.rmtree(folder, ignore_errors=True) # Delete the folder and its contents

        self.load_tenants()
        self.load_data()

    def showEvent(self, event): # Override the showEvent method to load data when the dialog is shown
        super().showEvent(event)
        self.load_data()

