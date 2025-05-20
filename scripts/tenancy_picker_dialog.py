from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from scripts.database_manager import DatabaseManager


# TenancyPickerDialog class inherits from QDialog
# This class is responsible for displaying a dialog to select a tenancy
# It shows a list of tenancies in a table format
# The user can double-click a tenancy to select it
# The class uses a database manager to interact with the SQLite database
# The dialog can be used to select a tenancy for various purposes, such as assigning a tenant to a property
# or viewing tenancy details

class TenancyPickerDialog(QDialog): # This class inherits from QDialog
    # Signal emitted when a tenancy is selected
    tenancy_selected = Signal(dict)

    def __init__(self, parent=None, tenant_id=None, tenancies=None): 
        # The tenant_id parameter is for filtering tenancies by tenant
        # The tenancies parameter is for pre-populating the dialog with specific tenancies
        super().__init__(parent)
        self.setWindowTitle("Select Tenancy")
        self.resize(700, 400)

        self.db = DatabaseManager() # Load database manager instance
        self.tenant_id = tenant_id # Store tenant ID for filtering
        self.tenancies = tenancies # Store tenancies for pre-population

        self.setup_ui() # Setup the UI components
        self.load_tenancies() # Load tenancies from the database

    def setup_ui(self):
        layout = QVBoxLayout(self)

        instructions = QLabel("Double-click a tenancy to select it.")
        layout.addWidget(instructions)

        self.tenancy_table = QTableWidget()
        self.tenancy_table.setColumnCount(5)
        self.tenancy_table.setHorizontalHeaderLabels(["ID", "Property", "Start Date", "End Date", "Status"])
        self.tenancy_table.setEditTriggers(QTableWidget.NoEditTriggers) # Disable editing of table cells
        self.tenancy_table.setSelectionBehavior(QTableWidget.SelectRows) # Selects entire row on click
        self.tenancy_table.doubleClicked.connect(self.select_tenancy) # Connect double-click event to select_tenancy method

        layout.addWidget(self.tenancy_table)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_tenancies(self): # Load tenancies from the database

        if self.tenant_id: # If tenant_id is provided, filter tenancies by tenant
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

        else: # If no tenant_id is provided, load all tenancies
            query = """
            SELECT t.tenancy_id, p.street || ', ' || p.city || ' ' || p.postcode,
                   t.start_date, t.end_date, t.status
            FROM tenancies t
            JOIN properties p ON t.property_id = p.property_id
            ORDER BY t.start_date DESC
            """
            tenancies = self.db.execute(query, fetchall=True)

        self.populate_tenancies(tenancies) # Populate the table with the loaded tenancies

    def populate_tenancies(self, tenancies): # Populate the table with tenancies
        self.tenancy_table.setRowCount(0)

        for row_num, tenancy in enumerate(tenancies): # Iterate through the tenancies
            self.tenancy_table.insertRow(row_num) # Insert a new row in the table
            for col_num, data in enumerate(tenancy): # Iterate through the data in each tenancy
                item = QTableWidgetItem(str(data))
                if col_num == 4:  # If the column is the status column, apply color coding
                    if data == "Active":
                        item.setBackground(Qt.green)
                        item.setForeground(Qt.white)
                    elif data == "Pending":
                        item.setBackground(Qt.yellow)
                    elif data == "Ended":
                        item.setBackground(Qt.red)
                        item.setForeground(Qt.white)
                self.tenancy_table.setItem(row_num, col_num, item)

    def select_tenancy(self): # This method is called when a tenancy is double-clicked
        # Get the selected row from the table
        selected_row = self.tenancy_table.currentRow()

        if selected_row == -1: # If no row is selected, show a warning message
            QMessageBox.warning(self, "No Selection", "Please select a tenancy.")
            return

        tenancy_id = self.tenancy_table.item(selected_row, 0).text()
        property_address = self.tenancy_table.item(selected_row, 1).text()
        start_date = self.tenancy_table.item(selected_row, 2).text()
        end_date = self.tenancy_table.item(selected_row, 3).text()
        status = self.tenancy_table.item(selected_row, 4).text()

        selected_tenancy = { # Create a dictionary to hold the selected tenancy details
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
        # Return tenancy_id and formatted label from the currently selected row
        selected_row = self.tenancy_table.currentRow()
        if selected_row == -1: # If no row is selected, return None
            return None, ""

        tenancy_id = self.tenancy_table.item(selected_row, 0).text()
        property_address = self.tenancy_table.item(selected_row, 1).text()
        start_date = self.tenancy_table.item(selected_row, 2).text()
        end_date = self.tenancy_table.item(selected_row, 3).text()

        label = f"{property_address} ({start_date} → {end_date})" # Format the label for display
        return tenancy_id, label # Return the tenancy ID and formatted label

