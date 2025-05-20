import os
import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDateEdit, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QDoubleValidator
from scripts.base_details_page import BaseDetailsPage
from scripts.database_manager import DatabaseManager
from scripts.document_manager import DocumentManager
from scripts.document_picker_dialog import DocumentPickerDialog
from scripts.tenant_picker_dialog import TenantPickerDialog
from scripts.property_picker_dialog import PropertyPickerDialog
from scripts.utils.file_utils import cleanup_temp_preview_folder
from scripts.utils.image_preview import TempImagePreview


# TenancyDetailsPage class to manage tenancy records
# This class inherits from BaseDetailsPage and provides a form for tenancy details.
# It allows for the addition, deletion, and updating of tenancy records.
# The tenancies are stored in a SQLite database and can be linked to multiple tenants.
# The class also provides functionality to upload and manage documents related to the tenancy.
# It includes a document preview feature for images and PDFs.

class TenancyDetailsPage(BaseDetailsPage): # This class inherits from BaseDetailsPage to create a custom form
    def __init__(self, tenancy_data=None, parent=None):
        super().__init__("Tenancy Details", parent)
        self.db = DatabaseManager()
        self.doc_manager = DocumentManager() # Document manager instance
        self.tenancy_data = tenancy_data or {} # Initialize tenancy data
        self.tenancy_id = self.tenancy_data.get("tenancy_id") # Get tenancy ID if available

        # === Multi-Tenant & Property Pickers === #
        self.tenant_ids = [] # List to hold tenant IDs
        self.property_id = tenancy_data.get("property_id") if tenancy_data else None # Get property ID if available

        self.tenant_button = QPushButton("Select Tenants")
        self.tenant_button.clicked.connect(self.select_tenant)
        self.tenant_display = QLineEdit()
        self.tenant_display.setReadOnly(True)
        tenant_row = QHBoxLayout()
        tenant_row.addWidget(self.tenant_display)
        tenant_row.addWidget(self.tenant_button)

        self.property_button = QPushButton("Select Property")
        self.property_button.clicked.connect(self.select_property)
        self.property_label = QLabel()

        tenant_container = QWidget() # Create a container for tenant selection
        tenant_container.setLayout(tenant_row)
        self.add_form_row("Tenants", tenant_container)
        self.tenant_display.setToolTip("Click to select tenants")
        self.add_form_row("", self.tenant_display) # Empty row for spacing
        self.add_form_row("Property", self.property_button) # Add property button
        self.add_form_row("", self.property_label) # Empty row for spacing

        # === Form Fields === #
        self.start_date_input = QDateEdit()
        self.start_date_input.setToolTip("Select tenancy start date")
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("yyyy-MM-dd")

        self.end_date_input = QDateEdit()
        self.end_date_input.setToolTip("Select tenancy end date")
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat("yyyy-MM-dd")

        self.rent_input = QLineEdit()
        self.rent_input.setPlaceholderText("e.g. 1200")
        self.rent_input.setToolTip("Enter rent amount")
        self.rent_input.setValidator(QDoubleValidator(0, 999999, 2))

        self.status_input = QComboBox()
        self.status_input.setToolTip("Select tenancy status")
        self.status_input.addItems(["Active", "Ended", "Pending"])

        self.add_form_row("Start Date", self.start_date_input)
        self.start_date_input.setDate(QDate.currentDate())
        self.add_form_row("End Date", self.end_date_input)
        self.end_date_input.setDate(QDate.currentDate().addMonths(12))
        self.add_form_row("Rent (£)", self.rent_input)
        self.add_form_row("Status", self.status_input)

        # === Document Section === #
        self.doc_list = QListWidget()
        self.right_panel.addWidget(QLabel("Supported files: PDF, PNG, JPG"))
        self.right_panel.addWidget(QLabel("Double-click to view document"))
        self.add_doc_button = QPushButton("➕ Add Document")
        self.delete_doc_button = QPushButton("🗑️ Delete Document")

        self.add_doc_button.clicked.connect(self.add_document)
        self.delete_doc_button.clicked.connect(self.delete_document)
        self.doc_list.itemDoubleClicked.connect(self.preview_document)

        self.right_panel.addWidget(QLabel("Documents:"))
        self.right_panel.addWidget(self.doc_list)
        self.right_panel.addWidget(self.add_doc_button)
        self.right_panel.addWidget(self.delete_doc_button)

        self.bind_data()
        self.load_documents()

    def select_tenant(self): # Select tenants for the tenancy
        dialog = TenantPickerDialog(mode="multi") # Open tenant picker dialog and set mode to multi to allow multiple selections
        dialog.tenants_selected.connect(self.set_selected_tenants) # Connect the signal to set selected tenants
        dialog.exec()

    def set_selected_tenants(self, tenants): # Set selected tenants
        self.tenant_ids = [int(t["tenant_id"]) for t in tenants] # Get tenant IDs
        names = ", ".join(t["name"] for t in tenants) # Join tenant names
        self.tenant_display.setText(names) # Set the display text to show selected tenants

    def select_property(self): # Select property for the tenancy
        dialog = PropertyPickerDialog(self) # Open property picker dialog
        dialog.property_selected.connect(self.set_selected_property) # Connect the signal to set selected property
        dialog.exec()

    def set_selected_property(self, prop): # Set selected property
        self.property_id = prop["property_id"] # Get property ID
        self.property_label.setText(prop["address"]) # Set the display text to show selected property


    def bind_data(self): # Bind data to the form fields
        if not self.tenancy_id: # If no tenancy ID is provided, return
            return

        # Load tenancy and property info
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT 
                    t.property_id,
                    p.door_number || ' ' || p.street || ', ' || p.postcode AS address,
                    t.start_date,
                    t.end_date,
                    t.rent_amount,
                    t.status
                FROM tenancies t
                JOIN properties p ON t.property_id = p.property_id
                WHERE t.tenancy_id = ?
            """, (self.tenancy_id,))
            row = cur.fetchone()

        if row:
            # Set and display property
            self.property_id = row[0]
            self.property_label.setText(row[1])

            # Dates, rent, status
            self.start_date_input.setDate(QDate.fromString(row[2], "yyyy-MM-dd"))
            self.end_date_input.setDate(QDate.fromString(row[3], "yyyy-MM-dd"))
            self.rent_input.setText(str(row[4]))
            self.status_input.setCurrentText(row[5])

        # Load linked tenants
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT tt.tenant_id, t.first_name || ' ' || t.last_name
                FROM tenancy_tenants tt
                JOIN tenants t ON tt.tenant_id = t.tenant_id
                WHERE tt.tenancy_id = ?
            """, (self.tenancy_id,))
            linked = cur.fetchall()

        # Store and display them
        self.tenant_ids = [row[0] for row in linked]
        names = ", ".join(row[1] for row in linked)
        self.tenant_display.setText(names)

    def collect_data(self): # Collect data from the form fields
        return {
            "property_id": self.property_id,
            "start_date": self.start_date_input.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date_input.date().toString("yyyy-MM-dd"),
            "rent_amount": self.rent_input.text(),
            "status": self.status_input.currentText()
        }

    def accept(self): # Accept the form data and save it to the database
        data = self.collect_data()
        
        if not self.tenant_ids or not self.property_id: # Check if tenants and property are selected
            QMessageBox.warning(self, "Missing Info", "Please select at least one tenant and a property.")
            return

        with self.db.cursor() as cur:
            # If editing an existing tenancy
            if self.tenancy_id:
                cur.execute("""
                    UPDATE tenancies SET
                        property_id = ?, start_date = ?, end_date = ?,
                        rent_amount = ?, status = ?
                    WHERE tenancy_id = ?
                """, (
                    data["property_id"], data["start_date"], data["end_date"],
                    data["rent_amount"], data["status"], self.tenancy_id
                ))

                # Remove old tenant links
                cur.execute("DELETE FROM tenancy_tenants WHERE tenancy_id = ?", (self.tenancy_id,))
            
            # If adding a new tenancy
            else:
                cur.execute("""
                    INSERT INTO tenancies (
                        property_id, start_date, end_date, rent_amount, status
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    data["property_id"], data["start_date"], data["end_date"],
                    data["rent_amount"], data["status"]
                ))
                self.tenancy_id = cur.lastrowid  # Get the ID of the newly created tenancy

            # Link selected tenants to the tenancy
            for tid in self.tenant_ids:
                cur.execute("INSERT INTO tenancy_tenants (tenancy_id, tenant_id) VALUES (?, ?)", (self.tenancy_id, tid))

        # Close the dialog
        super().accept()


    def load_documents(self): # Load documents related to the tenancy
        self.doc_list.clear() # Clear the document list
        if not self.tenancy_id: # If no tenancy ID is provided, return
            return

        self.documents = self.doc_manager.get_documents("tenancy", self.tenancy_id) # Get documents from the document manager
        for doc in self.documents: # Iterate through the documents
            item = QListWidgetItem(f"{doc['name']} ({doc['type']})")
            item.setData(Qt.UserRole, doc["id"])
            item.setData(Qt.UserRole + 1, doc["filename"])
            self.doc_list.addItem(item)

    def add_document(self): # Add a document to the tenancy
        if not self.tenancy_id:
            QMessageBox.warning( # Show a warning if the tenancy ID is not set
                self,
                "Save Required",
                "Please save the tenancy before uploading documents."
            )
            return

        dialog = DocumentPickerDialog("tenancy", self.tenancy_id) # Open document picker dialog
        if dialog.exec():
            self.load_documents()

    def delete_document(self): # Delete a document from the tenancy
        selected_item = self.doc_list.currentItem() # Get the currently selected item

        if not self.tenancy_id: # If no tenancy ID is provided, show a warning
            QMessageBox.warning(
                self,
                "Save Required",
                "Cannot delete documents before tenancy is saved."
            )
            return

        if not selected_item: # If no item is selected, show a warning
            QMessageBox.information(self, "No Selection", "Please select a document to delete.")
            return

        filename = selected_item.data(Qt.UserRole + 1)
        confirm = QMessageBox.question(self, "Delete?", f"Delete document '{selected_item.text()}'?")
        if confirm == QMessageBox.Yes:
            self.doc_manager.delete_document("tenancy", self.tenancy_id, filename)
            self.load_documents()

    def preview_document(self, item): # Preview a document
        filename = item.data(Qt.UserRole + 1)
        path = self.doc_manager.decrypt_document_to_temp("tenancy", self.tenancy_id, filename) # Decrypt the document to a temporary location
        if not path:
            return

        if path.lower().endswith((".png", ".jpg", ".jpeg")): # Check if the file is an image
            self.preview_image(path) # Preview the image
        elif path.lower().endswith(".pdf"): # Check if the file is a PDF
            webbrowser.open(path) # Open the PDF in the default web browser

    def preview_image(self, path): # Preview an image
        dialog = TempImagePreview(path, self)
        dialog.exec()
