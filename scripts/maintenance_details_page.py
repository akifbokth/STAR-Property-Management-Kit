from PySide6.QtWidgets import QLineEdit, QTextEdit, QComboBox, QDateEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import QDate, Signal
from scripts.base_details_page import BaseDetailsPage
from scripts.database_manager import DatabaseManager
from scripts.property_picker_dialog import PropertyPickerDialog


# MaintenanceDetailsPage class to create a dialog for managing maintenance details
# This class inherits from BaseDetailsPage and provides a form for entering maintenance information
# It also allows for the selection of a property associated with the maintenance request.
# The maintenance requests are stored in a SQLite database and can be updated or created.

class MaintenanceDetailsPage(BaseDetailsPage): # This class inherits from BaseDetailsPage to create a custom dialog
    # Signal emitted when maintenance details are updated
    maintenance_updated = Signal()

    def __init__(self, maintenance_data=None, parent=None):
        super().__init__("Maintenance Details", parent)
        self.db = DatabaseManager() # Database manager instance
        self.maintenance_id = maintenance_data.get("maintenance_id") if maintenance_data else None # Get maintenance ID if provided
        self.property_id = None # Property ID to be set when a property is selected

        # Property selection button and label
        self.property_btn = QPushButton("Select Property")
        self.property_label = QLabel("No property selected")
        self.property_btn.clicked.connect(self.select_property)

        self.right_panel.addWidget(QLabel("<b>Property</b>"))
        self.right_panel.addWidget(self.property_btn)
        self.right_panel.addWidget(self.property_label)

        # Maintenance form inputs
        self.issue_input = QLineEdit()
        self.issue_input.setPlaceholderText("e.g. Broken window")
        self.issue_input.setToolTip("Enter the issue reported")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("e.g. The window is broken and needs repair.")
        self.description_input.setToolTip("Enter a detailed description of the issue")
        self.description_input.setMaximumHeight(100)
        self.description_input.setMinimumHeight(50)

        self.date_input = QDateEdit()
        self.date_input.setToolTip("Select the date the issue was reported")
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())

        self.status_input = QComboBox()
        self.status_input.setToolTip("Select the status of the maintenance request")
        self.status_input.addItems(["Pending", "In Progress", "Resolved", "Voided"])
        self.status_input.setCurrentText("Pending")

        self.add_form_row("Issue", self.issue_input)
        self.add_form_row("Description", self.description_input)
        self.add_form_row("Date Reported", self.date_input)
        self.add_form_row("Status", self.status_input)

        if maintenance_data:
            self.bind_data(maintenance_data)

    def select_property(self): # Open the property picker dialog to select a property
        dialog = PropertyPickerDialog()
        if dialog.exec():
            selected = dialog.get_selection()
            if selected:
                self.property_id = selected["property_id"]
                self.property_label.setText(selected["address"])

    def bind_data(self, data): # Bind the provided data to the form inputs
        self.maintenance_id = data["maintenance_id"]
        self.property_id = data["property_id"]
        self.issue_input.setText(data["issue"])
        self.description_input.setPlainText(data["description"] or "")
        self.date_input.setDate(QDate.fromString(data["date_reported"], "yyyy-MM-dd"))
        self.status_input.setCurrentText(data["status"])

        label = self.db.execute(
            "SELECT door_number || ' ' || street || ', ' || postcode FROM properties WHERE property_id = ?",
        (self.property_id,), fetchone=True)

        if label: # If the property ID is valid, set the label to the property address
            self.property_label.setText(label[0])

    def collect_data(self): # Collect data from the form inputs and validate
        if not self.property_id: # Check if a property is selected
            QMessageBox.warning(self, "Missing Property", "Please select a property.")
            return None

        return {
            "property_id": self.property_id,
            "issue": self.issue_input.text(),
            "description": self.description_input.toPlainText(),
            "date_reported": self.date_input.date().toString("yyyy-MM-dd"),
            "status": self.status_input.currentText()
        }

    def accept(self): # Override the accept method to handle form submission
        data = self.collect_data()
        if not data:
            return

        if self.maintenance_id: # If maintenance ID is provided, update the existing record
            self.db.execute(
                """
                UPDATE maintenance SET property_id = ?, issue = ?, description = ?,
                    date_reported = ?, status = ?
                WHERE maintenance_id = ?
                """,
                (
                    data["property_id"], data["issue"], data["description"],
                    data["date_reported"], data["status"], self.maintenance_id
                )
            )

        else: # If no maintenance ID is provided, create a new record
            self.db.execute(
                """
                INSERT INTO maintenance (property_id, issue, description, date_reported, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data["property_id"], data["issue"], data["description"],
                    data["date_reported"], data["status"]
                )
            )

        self.maintenance_updated.emit() # Emit the signal to notify that maintenance details have been updated
        super().accept()
