from PySide6.QtWidgets import QMessageBox
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.payment_details_page import PaymentDetailsPage


# PaymentManager class to manage payment records
# This class inherits from BaseManager and provides a table view for payments.
# It allows for the addition, deletion, and updating of payment records.
# The payments are stored in a SQLite database and can be filtered by tenant, status, or type.

class PaymentManager(BaseManager): # This class inherits from BaseManager to create a custom table view
    def __init__(self, parent=None):
        self.db = DatabaseManager() # Database manager instance
        super().__init__(
            title="Payment Management",
            search_placeholder="Search by tenant, status or type...",
            columns=["ID", "Tenant", "Type", "Amount", "Date", "Due", "Status", "Method"],
            parent=parent
        )
        self.load_data()

    def get_data(self): # Fetch payment data from the database
        query = """
            SELECT
                p.payment_id,
                t.first_name || ' ' || t.last_name AS tenant_name,
                p.payment_type,
                p.amount,
                p.payment_date,
                p.due_date,
                p.status,
                p.method
            FROM payments p
            JOIN tenants t ON p.tenant_id = t.tenant_id
            ORDER BY p.payment_date DESC
        """
        with self.db.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in rows]

    def extract_row_values(self, item): # Extract values from the payment item for display in the table
        return [
            item["payment_id"],
            item["tenant_name"],
            item["payment_type"],
            item["amount"],
            item["payment_date"],
            item["due_date"],
            item["status"],
            item["method"]
        ]
    
    def delete_item(self, item): # Delete a payment record from the database
        payment_id = item["payment_id"] # Get the payment ID from the item

        # Delete from database
        with self.db.cursor() as cur:
            cur.execute(
                "DELETE FROM payments WHERE payment_id = ?",
                (payment_id,)
            )
        # Refresh the table
        self.load_data()

    def open_details_dialog(self, item=None): # Open the payment details dialog
        # If no item is provided, create a new payment
        dialog = PaymentDetailsPage(payment_id=item["payment_id"] if item else None)
        # Connect the payment_updated signal to reload data after update
        dialog.payment_updated.connect(self.load_data)
        dialog.exec()
