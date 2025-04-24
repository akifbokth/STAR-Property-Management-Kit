from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import Signal, Qt
from scripts.database_manager import DatabaseManager


class PropertyPickerDialog(QDialog):
    property_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Property")
        self.resize(700, 450)

        self.db = DatabaseManager()
        self.setup_ui()
        self.load_properties()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 🔍 Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by address, city or postcode...")
        self.search_input.textChanged.connect(self.load_properties)
        layout.addWidget(self.search_input)

        self.property_table = QTableWidget()
        self.property_table.setColumnCount(5)
        self.property_table.setHorizontalHeaderLabels(["ID", "Address", "City", "Postcode", "Status"])
        self.property_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.property_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.property_table.setSelectionMode(QTableWidget.SingleSelection)

        layout.addWidget(self.property_table)

        self.ok_button = QPushButton("Select Property")
        self.ok_button.clicked.connect(self.handle_selection)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def load_properties(self):
        keyword = self.search_input.text().strip()
        params = []
        query = """
        SELECT property_id, door_number || ', ' || street, city, postcode, status
        FROM properties
        """

        if keyword:
            query += """
                WHERE
                    street LIKE ? OR
                    city LIKE ? OR
                    postcode LIKE ?
            """
            like = f"%{keyword}%"
            params = [like, like, like]

        query += " ORDER BY city"

        properties = self.db.execute(query, params, fetchall=True)
        self.populate_properties(properties)

    def populate_properties(self, properties):
        self.property_table.setRowCount(0)
        for row_num, prop in enumerate(properties):
            self.property_table.insertRow(row_num)
            for col_num, data in enumerate(prop):
                item = QTableWidgetItem(str(data))
                self.property_table.setItem(row_num, col_num, item)

    def get_selection(self):
        selected_row = self.property_table.currentRow()
        if selected_row == -1:
            return None

        property_id = int(self.property_table.item(selected_row, 0).text())
        address = self.property_table.item(selected_row, 1).text()  # Already formatted as "Door, Street"
        city = self.property_table.item(selected_row, 2).text()
        postcode = self.property_table.item(selected_row, 3).text()
        status = self.property_table.item(selected_row, 4).text()

        full_address = f"{address}, {postcode}"

        return {
            "property_id": property_id,
            "address": full_address,
            "city": city,
            "postcode": postcode,
            "status": status
        }



    def handle_selection(self):
        selected = self.get_selection()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a property.")
            return

        self.property_selected.emit(selected)
        self.accept()
