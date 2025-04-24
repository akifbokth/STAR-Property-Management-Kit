from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from scripts.database_manager import DatabaseManager


class TenancyPickerDialog(QDialog):
    tenancy_selected = Signal(dict)

    def __init__(self, parent=None, tenant_id=None, tenancies=None):
        super().__init__(parent)
        self.setWindowTitle("Select Tenancy")
        self.resize(700, 400)

        self.db = DatabaseManager()
        self.tenant_id = tenant_id
        self.tenancies = tenancies

        self.setup_ui()
        self.load_tenancies()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        instructions = QLabel("Double-click a tenancy to select it.")
        layout.addWidget(instructions)

        self.tenancy_table = QTableWidget()
        self.tenancy_table.setColumnCount(5)
        self.tenancy_table.setHorizontalHeaderLabels(["ID", "Property", "Start Date", "End Date", "Status"])
        self.tenancy_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tenancy_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tenancy_table.doubleClicked.connect(self.select_tenancy)

        layout.addWidget(self.tenancy_table)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_tenancies(self):
        if self.tenant_id:
            query = """
            SELECT t.tenancy_id, p.street || ', ' || p.city || ' ' || p.postcode,
                   t.start_date, t.end_date, t.status
            FROM tenancies t
            JOIN properties p ON t.property_id = p.property_id
            JOIN tenancy_tenants tt ON tt.tenancy_id = t.tenancy_id
            WHERE tt.tenant_id = ?
            ORDER BY t.start_date DESC
            """
            tenancies = self.db.execute(query, (self.tenant_id,), fetchall=True)
        else:
            query = """
            SELECT t.tenancy_id, p.street || ', ' || p.city || ' ' || p.postcode,
                   t.start_date, t.end_date, t.status
            FROM tenancies t
            JOIN properties p ON t.property_id = p.property_id
            ORDER BY t.start_date DESC
            """
            tenancies = self.db.execute(query, fetchall=True)

        self.populate_tenancies(tenancies)

    def populate_tenancies(self, tenancies):
        self.tenancy_table.setRowCount(0)

        for row_num, tenancy in enumerate(tenancies):
            self.tenancy_table.insertRow(row_num)
            for col_num, data in enumerate(tenancy):
                item = QTableWidgetItem(str(data))
                if col_num == 4:  # Status column coloring
                    if data == "Active":
                        item.setBackground(Qt.green)
                        item.setForeground(Qt.white)
                    elif data == "Pending":
                        item.setBackground(Qt.yellow)
                    elif data == "Terminated":
                        item.setBackground(Qt.red)
                        item.setForeground(Qt.white)
                self.tenancy_table.setItem(row_num, col_num, item)

    def select_tenancy(self):
        selected_row = self.tenancy_table.currentRow()

        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a tenancy.")
            return

        tenancy_id = self.tenancy_table.item(selected_row, 0).text()
        property_address = self.tenancy_table.item(selected_row, 1).text()
        start_date = self.tenancy_table.item(selected_row, 2).text()
        end_date = self.tenancy_table.item(selected_row, 3).text()
        status = self.tenancy_table.item(selected_row, 4).text()

        selected_tenancy = {
            "tenancy_id": tenancy_id,
            "property": property_address,
            "start_date": start_date,
            "end_date": end_date,
            "status": status
        }

        # Emit the selected tenancy and close dialog
        self.tenancy_selected.emit(selected_tenancy)
        self.accept()

    def get_selection(self):
        """Return tenancy_id and formatted label from the currently selected row."""
        selected_row = self.tenancy_table.currentRow()
        if selected_row == -1:
            return None, ""

        tenancy_id = self.tenancy_table.item(selected_row, 0).text()
        property_address = self.tenancy_table.item(selected_row, 1).text()
        start_date = self.tenancy_table.item(selected_row, 2).text()
        end_date = self.tenancy_table.item(selected_row, 3).text()

        label = f"{property_address} ({start_date} → {end_date})"
        return tenancy_id, label

