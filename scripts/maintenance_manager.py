from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.maintenance_details_page import MaintenanceDetailsPage


class MaintenanceManager(BaseManager):
    def __init__(self, filter_unresolved=False, parent=None):
        self.db = DatabaseManager()
        self.filter_unresolved = filter_unresolved

        super().__init__(
            title="Maintenance Management",
            search_placeholder="Search by issue, status, or property...",
            columns=["ID", "Property", "Issue", "Reported", "Status"],
            parent=parent
        )
        self.load_data()

    def get_data(self):
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

        if self.filter_unresolved:
            base_query += " WHERE LOWER(m.status) NOT IN ('resolved', 'voided')"

        base_query += " ORDER BY m.date_reported DESC"

        rows = self.db.execute(base_query, fetchall=True)
        col_names = [
            "maintenance_id", "property_id", "address", "issue",
            "description", "date_reported", "status"
        ]
        return [dict(zip(col_names, row)) for row in rows]



    def extract_row_values(self, item):
        return [
            item["maintenance_id"],
            item["address"],
            item["issue"],
            item["date_reported"],
            item["status"]
        ]

    def open_details_dialog(self, item=None):
        dialog = MaintenanceDetailsPage(maintenance_data=item)
        dialog.maintenance_updated.connect(self.load_data)
        dialog.exec()
