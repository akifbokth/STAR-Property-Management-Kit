from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt, Signal
import sqlite3
from config import DB_PATH


class TenantPickerDialog(QDialog):
    # Signals for different use cases
    tenant_selected = Signal(dict)   # For single tenant selection
    tenants_selected = Signal(list)  # For multiple tenants (e.g. tenancy)

    def __init__(self, mode="single", parent=None):
        super().__init__()
        self.setWindowTitle("Select Tenants")
        self.setMinimumSize(750, 400)
        self.mode = mode  # "single" or "multi"
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tenants...")
        self.search_input.textChanged.connect(self.search_tenants)
        search_layout.addWidget(self.search_input)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Phone"])
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.MultiSelection)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSortingEnabled(True)

        # Select button
        select_button = QPushButton("Select Tenants")
        select_button.clicked.connect(self.select_tenants)

        # Layout wiring
        layout.addLayout(search_layout)
        layout.addWidget(self.results_table)
        layout.addWidget(select_button)
        self.setLayout(layout)

        self.search_tenants()  # Load initial list

    def search_tenants(self):
        keyword = self.search_input.text().strip()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        if keyword:
            cur.execute("""
                SELECT tenant_id, first_name || ' ' || last_name AS name, email, phone
                FROM tenants
                WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR phone LIKE ?
            """, (f"%{keyword}%",) * 4)
        else:
            cur.execute("""
                SELECT tenant_id, first_name || ' ' || last_name AS name, email, phone
                FROM tenants
            """)

        results = cur.fetchall()
        conn.close()

        self.results_table.setRowCount(len(results))
        for row, data in enumerate(results):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, data[0])  # Store tenant_id
                self.results_table.setItem(row, col, item)

    def select_tenants(self):
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select one or more tenants.")
            return

        selected_tenants = []
        rows = set(index.row() for index in self.results_table.selectedIndexes())
        for row in rows:
            tenant_id = self.results_table.item(row, 0).text()
            name = self.results_table.item(row, 1).text()
            email = self.results_table.item(row, 2).text()
            phone = self.results_table.item(row, 3).text()
            selected_tenants.append({
                "tenant_id": tenant_id,
                "name": name,
                "email": email,
                "phone": phone
            })

        if self.mode == "single":
            self.tenant_selected.emit(selected_tenants[0])
        else:
            self.tenants_selected.emit(selected_tenants)

        self.accept()


