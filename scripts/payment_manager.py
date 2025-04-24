from PySide6.QtWidgets import QMessageBox
from scripts.base_manager import BaseManager
from scripts.database_manager import DatabaseManager
from scripts.payment_details_page import PaymentDetailsPage


class PaymentManager(BaseManager):
    def __init__(self, parent=None):
        self.db = DatabaseManager()
        super().__init__(
            title="Payment Management",
            search_placeholder="Search by tenant, status or type...",
            columns=["ID", "Tenant", "Type", "Amount", "Date", "Due", "Status", "Method"],
            parent=parent
        )
        self.load_data()

    def get_data(self):
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

    def extract_row_values(self, item):
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

    def open_details_dialog(self, item=None):
        dialog = PaymentDetailsPage(payment_id=item["payment_id"] if item else None)
        dialog.payment_updated.connect(self.load_data)
        dialog.exec()
