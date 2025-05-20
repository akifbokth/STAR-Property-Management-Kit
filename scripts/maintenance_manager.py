from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.maintenance_details_page import MaintenanceDetailsPage


# MaintenanceManager class to manage maintenance requests
# This class inherits from BaseManager and provides a table view for maintenance requests
# It allows for the addition, deletion, and updating of maintenance requests.
# The maintenance requests are stored in a SQLite database and can be filtered based on their status.

class MaintenanceManager(BaseManager): # This class inherits from BaseManager to create a custom table view
    def __init__(self, filter_unresolved=False, parent=None):
        self.db = DatabaseManager() # Database manager instance
        self.filter_unresolved = filter_unresolved # Flag to filter unresolved maintenance requests

        super().__init__(
            title="Maintenance Management",
            search_placeholder="Search by issue, status, or property...",
            columns=["Property", "Issue", "Reported", "Status"],
            parent=parent
        )
        self.load_data()

    def get_data(self): # Fetch maintenance data from the database
        base_query = """
            SELECT 
                m.maintenance_id,
                m.property_id,
                p.door_number || ' ' || p.street || ', ' || p.postcode AS address,
                m.issue,
                m.description,
                m.date_reported,
                m.status
            FROM maintenance m
            JOIN properties p ON m.property_id = p.property_id
        """

        if self.filter_unresolved: # If the filter_unresolved flag is set, filter out resolved and voided maintenance requests
            base_query += " WHERE LOWER(m.status) NOT IN ('resolved', 'voided')"

        base_query += " ORDER BY m.date_reported DESC"

        rows = self.db.execute(base_query, fetchall=True)
        col_names = [
            "maintenance_id", "property_id", "address", "issue",
            "description", "date_reported", "status"
        ]
        return [dict(zip(col_names, row)) for row in rows]

    def extract_row_values(self, item): # Extract values from the maintenance item for display in the table
        return [
            item["address"],
            item["issue"],
            item["date_reported"],
            item["status"]
        ]

    def open_details_dialog(self, item=None): # Open the maintenance details dialog
        dialog = MaintenanceDetailsPage(maintenance_data=item) # Pass the selected item data to the dialog
        dialog.maintenance_updated.connect(self.load_data) # Connect the signal to reload data after update
        dialog.exec()

    def delete_item(self, item): # Delete the selected maintenance request from the database
        maintenance_id = item["maintenance_id"] # Get the maintenance ID from the item

        with self.db.cursor() as cur:
            cur.execute(
                "DELETE FROM maintenance WHERE maintenance_id = ?", # Delete the maintenance record
                (maintenance_id,)
            )

        self.load_data() # Reload the table data