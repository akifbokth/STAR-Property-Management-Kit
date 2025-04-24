import os
import webbrowser
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QComboBox, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QDialog, QVBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from scripts.base_details_page import BaseDetailsPage
from scripts.database_manager import DatabaseManager
from scripts.document_manager import DocumentManager
from scripts.document_picker_dialog import DocumentPickerDialog
from scripts.utils.form_validator import FormValidator
from scripts.utils.file_utils import cleanup_temp_preview_folder
from scripts.utils.image_preview import TempImagePreview


class LandlordDetailsPage(BaseDetailsPage):
    def __init__(self, landlord_data=None, parent=None):
        super().__init__("Landlord Details", parent)
        self.db = DatabaseManager()
        self.doc_manager = DocumentManager()
        self.landlord_data = landlord_data or {}
        self.landlord_id = self.landlord_data.get("landlord_id")

        # === Form Fields ===
        self.first_name_input = QLineEdit()
        self.first_name_input.setToolTip("Enter first name")
        self.last_name_input = QLineEdit()
        self.last_name_input.setToolTip("Enter last name")
        self.email_input = QLineEdit()
        self.email_input.setToolTip("Enter email address")
        self.phone_input = QLineEdit()
        self.phone_input.setToolTip("Enter phone number")
        self.phone_input.setPlaceholderText("e.g. 07123456789")
        self.phone_input.setMaxLength(15)
        self.address_input = QLineEdit()
        self.address_input.setToolTip("Enter landlord's home address")
        self.address_input.setPlaceholderText("Enter landlord's home address")
        self.status_input = QComboBox()
        self.status_input.setToolTip("Select landlord's status")
        self.status_input.setPlaceholderText("Select landlord's status")
        self.status_input.addItems(["Active", "Inactive"])

        self.add_form_row("First Name", self.first_name_input)
        self.add_form_row("Last Name", self.last_name_input)
        self.add_form_row("Email", self.email_input)
        self.add_form_row("Phone", self.phone_input)
        self.add_form_row("Address", self.address_input)
        self.add_form_row("Status", self.status_input)

        # === Documents Section ===
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

        self.bind_data(self.landlord_data)
        # self.load_documents()  # Delayed until after save

    def bind_data(self, data):
        self.first_name_input.setText(data.get("first_name", ""))
        self.last_name_input.setText(data.get("last_name", ""))
        self.email_input.setText(data.get("email", ""))
        self.phone_input.setText(data.get("phone", ""))
        self.address_input.setText(data.get("address", ""))
        self.status_input.setCurrentText(data.get("status", "Active"))

    def collect_data(self):
        # === VALIDATION ===
        validator = FormValidator(self)
        validator.require(self.first_name_input, "First Name") \
                 .require(self.last_name_input, "Last Name") \
                 .is_email(self.email_input, "Email") \
                 .is_numeric(self.phone_input, "Phone")

        if not validator.validate():
            return None  # Stop collection on validation failure

        return {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.text().strip(),
            "status": self.status_input.currentText()
        }

    def accept(self):
        data = self.collect_data()
        if data is None:
            return  # Don't save if invalid

        with self.db.cursor() as cur:
            if self.landlord_id:
                cur.execute(
                    "UPDATE landlords SET first_name = ?, last_name = ?, email = ?, phone = ?, address = ?, status = ? WHERE landlord_id = ?",
                    (data["first_name"], data["last_name"], data["email"], data["phone"], data["address"], data["status"], self.landlord_id)
                )
            else:
                cur.execute(
                    "INSERT INTO landlords (first_name, last_name, email, phone, address, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (data["first_name"], data["last_name"], data["email"], data["phone"], data["address"], data["status"])
                )
                self.landlord_id = cur.lastrowid

        self.load_documents()
        super().accept()

    def load_documents(self):
        self.doc_list.clear()
        if not self.landlord_id:
            return
        self.documents = self.doc_manager.get_documents("landlord", self.landlord_id)
        for doc in self.documents:
            item = QListWidgetItem(f"{doc['name']} ({doc['type']})")
            item.setData(Qt.UserRole, doc["id"])
            item.setData(Qt.UserRole + 1, doc["filename"])
            self.doc_list.addItem(item)

    def add_document(self):
        if not self.landlord_id:
            QMessageBox.warning(
                self,
                "Save Required",
                "Please save the landlord before uploading documents."
            )
            return
        dialog = DocumentPickerDialog("landlord", self.landlord_id)
        if dialog.exec():
            self.load_documents()

    def delete_document(self):

        selected_item = self.doc_list.currentItem()

        if not self.landlord_id:
            QMessageBox.warning(
                self,
                "Save Required",
                "Cannot delete documents before landlord is saved."
            )
            return

        if not selected_item:
            QMessageBox.information(self, "No Selection", "Please select a document to delete.")
            return
        
        filename = selected_item.data(Qt.UserRole + 1)
        confirm = QMessageBox.question(self, "Delete?", f"Delete document '{selected_item.text()}'?")
        if confirm == QMessageBox.Yes:
            self.doc_manager.delete_document("landlord", self.landlord_id, filename)
            self.load_documents()

    def preview_document(self, item):
        filename = item.data(Qt.UserRole + 1)
        path = self.doc_manager.decrypt_document_to_temp("landlord", self.landlord_id, filename)
        if not path:
            return
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            self.preview_image(path)
        elif path.lower().endswith(".pdf"):
            webbrowser.open(path)

    def preview_image(self, path):
        dialog = TempImagePreview(path, self)
        dialog.exec()