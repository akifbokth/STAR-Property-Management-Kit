from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import Signal, Qt
from scripts.database_manager import DatabaseManager


# PropertyPickerDialog class to select a property from the database
# This class inherits from QDialog and provides a table view for properties.
# It allows for the selection of a property based on address, city, or postcode.
# The properties are stored in a SQLite database and can be filtered by availability.

class PropertyPickerDialog(QDialog): # This class inherits from QDialog to create a custom dialog
    property_selected = Signal(dict) # Signal to emit the selected property

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Property")
        self.resize(700, 450)

        self.db = DatabaseManager() # Database manager instance
        self.setup_ui() # Setup the UI components
        self.load_properties() # Load properties from the database

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Search bar to filter properties
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by address, city or postcode...")
        self.search_input.textChanged.connect(self.load_properties)
        layout.addWidget(self.search_input)

        self.property_table = QTableWidget()
        self.property_table.setColumnCount(5)
        self.property_table.setHorizontalHeaderLabels(["ID", "Address", "City", "Postcode", "Status"])
        self.property_table.setEditTriggers(QTableWidget.NoEditTriggers) # Disable editing
        self.property_table.setSelectionBehavior(QTableWidget.SelectRows) # Select entire row
        self.property_table.setSelectionMode(QTableWidget.SingleSelection) # Single selection

        layout.addWidget(self.property_table)

        self.ok_button = QPushButton("Select Property")
        self.ok_button.clicked.connect(self.handle_selection) # Connect button to handle selection
        layout.addWidget(self.ok_button) # Add button to layout

        self.setLayout(layout)

    def load_properties(self): # Load properties from the database based on search input
        keyword = self.search_input.text().strip() # Get the search keyword
        params = [] # Initialize parameters for SQL query
        query = """
        SELECT property_id, door_number || ', ' || street, city, postcode, status
        FROM properties
        """

        if keyword: # If there is a search keyword, filter properties based on it
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

    def populate_properties(self, properties): # Populate the table with property data
        self.property_table.setRowCount(0)
        for row_num, prop in enumerate(properties): # Iterate through properties and add them to the table
            self.property_table.insertRow(row_num)
            for col_num, data in enumerate(prop): # Iterate through each property data
                item = QTableWidgetItem(str(data)) # Convert data to string for display
                self.property_table.setItem(row_num, col_num, item) # Set item in the table

    def get_selection(self): # Get the selected property from the table
        selected_row = self.property_table.currentRow() # Get the currently selected row
        if selected_row == -1: # If no row is selected, return None
            return None

        property_id = int(self.property_table.item(selected_row, 0).text()) # Get property ID
        address = self.property_table.item(selected_row, 1).text() # Get address
        city = self.property_table.item(selected_row, 2).text() # Get city
        postcode = self.property_table.item(selected_row, 3).text() # Get postcode
        status = self.property_table.item(selected_row, 4).text() # Get status

        full_address = f"{address}, {postcode}" # Combine address and postcode for full address

        return {
            "property_id": property_id,
            "address": full_address,
            "city": city,
            "postcode": postcode,
            "status": status
        }

    def handle_selection(self): # Handle the selection of a property
        selected = self.get_selection() # Get the selected property
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a property.")
            return

        self.property_selected.emit(selected) # Emit the selected property
        self.accept()
