import os
from PySide6.QtWidgets import (
    QLineEdit, QComboBox, QDateEdit, QLabel, QVBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QDialog, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
import webbrowser
from scripts.base_details_page import BaseDetailsPage
from scripts.document_manager import DocumentManager
from scripts.document_picker_dialog import DocumentPickerDialog
from scripts.utils.form_validator import FormValidator
from scripts.utils.file_utils import cleanup_temp_preview_folder
from scripts.utils.image_preview import TempImagePreview
from scripts.database_manager import DatabaseManager


class TenantDetailsPage(BaseDetailsPage):
    def __init__(self, tenant_data=None, parent=None):
        super().__init__("Tenant Details", parent)
        self.tenant_data = tenant_data or {}
        self.tenant_id = tenant_data.get("id") if tenant_data else None
        self.doc_manager = DocumentManager()
        self.db = DatabaseManager()

        # === Form fields ===
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("e.g. johnsmith@mail.com")
        self.email_input.setToolTip("Enter email address")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 07123456789")
        self.phone_input.setToolTip("Enter phone number")
        self.dob_input = QDateEdit()
        self.dob_input.setToolTip("Select date of birth")
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate.currentDate())

        self.nationality_input = QLineEdit()
        self.nationality_input.setPlaceholderText("e.g. British")
        self.nationality_input.setToolTip("Enter nationality")
        self.emergency_contact_input = QLineEdit()
        self.emergency_contact_input.setPlaceholderText("Name - Phone Number")
        self.emergency_contact_input.setToolTip("Enter emergency contact's name and phone number")

        self.status_input = QComboBox()
        self.status_input.addItems(["Active", "Inactive"])
        self.status_input.setToolTip("Select tenant status")

        self.add_form_row("First Name", self.first_name_input)
        self.add_form_row("Last Name", self.last_name_input)
        self.add_form_row("Email", self.email_input)
        self.add_form_row("Phone", self.phone_input)
        self.add_form_row("Date of Birth", self.dob_input)
        self.add_form_row("Nationality", self.nationality_input)
        self.add_form_row("Emerg. Contact", self.emergency_contact_input)
        self.add_form_row("Status", self.status_input)

        # === Documents section ===
        self.doc_list = QListWidget()
        self.right_panel.addWidget(QLabel("Supported files: PDF, PNG, JPG"))
        self.right_panel.addWidget(QLabel("Double-click to view document"))
        self.add_doc_button = QPushButton("➕ Add Document")
        self.add_doc_button.setToolTip("Add a new document")
        self.add_doc_button.clicked.connect(self.add_document)
        self.delete_doc_button = QPushButton("🗑️ Delete Document")
        self.delete_doc_button.setToolTip("Delete selected document")
        self.delete_doc_button.clicked.connect(self.delete_document)
        self.doc_list.itemDoubleClicked.connect(self.preview_document)

        self.right_panel.addWidget(QLabel("Documents:"))
        self.right_panel.addWidget(self.doc_list)
        self.right_panel.addWidget(self.add_doc_button)
        self.right_panel.addWidget(self.delete_doc_button)

        self.bind_data(self.tenant_data)
        self.load_documents()

    def bind_data(self, data):
        self.first_name_input.setText(data.get("first_name", ""))
        self.last_name_input.setText(data.get("last_name", ""))
        self.email_input.setText(data.get("email", ""))
        self.phone_input.setText(data.get("phone", ""))
        self.nationality_input.setText(data.get("nationality", ""))
        self.emergency_contact_input.setText(data.get("emergency_contact", ""))
        self.status_input.setCurrentText(data.get("status", "Active"))

        dob_str = data.get("date_of_birth", "")
        if dob_str:
            self.dob_input.setDate(QDate.fromString(dob_str, "yyyy-MM-dd"))

        self.tenant_id = data.get("id")

    def collect_data(self):
        # === VALIDATION ===
        validator = FormValidator(self)
        validator.require(self.first_name_input, "First Name") \
                 .require(self.last_name_input, "Last Name") \
                 .is_email(self.email_input, "Email") \
                 .is_numeric(self.phone_input, "Phone")

        if not validator.validate():
            return None

        return {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "date_of_birth": self.dob_input.date().toString("yyyy-MM-dd"),
            "nationality": self.nationality_input.text().strip(),
            "emergency_contact": self.emergency_contact_input.text().strip(),
            "status": self.status_input.currentText()
        }

    def load_documents(self):
        self.doc_list.clear()
        tenant_id = self.tenant_data.get("id")
        if tenant_id:
            self.documents = self.doc_manager.get_documents("tenant", tenant_id)
            for doc in self.documents:
                item_text = f"{doc['name']} ({doc['type']})"
                self.doc_list.addItem(QListWidgetItem(item_text))

    def add_document(self):
        if not self.tenant_id:
            QMessageBox.warning(
                self,
                "Save Required",
                "Please save the tenant before uploading documents."
            )
            return

        dialog = DocumentPickerDialog("tenant", self.tenant_id)
        if dialog.exec():
            self.load_documents()

    def delete_document(self):
        selected_item = self.doc_list.currentItem()

        if not self.tenant_id:
            QMessageBox.warning(
                self,
                "Save Required",
                "Cannot delete documents before tenant is saved."
            )
            return

        if not selected_item:
            QMessageBox.information(self, "No Selection", "Please select a document to delete.")
            return

        name_part = selected_item.text().split(" (")[0]
        match = next((doc for doc in self.documents if doc["name"] == name_part), None)
        if not match:
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{match['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        self.doc_manager.delete_document("tenant", self.tenant_data["id"], match["filename"])
        self.load_documents()

    def preview_document(self, item):
        # Clean up any existing temp files before previewing a new one
        cleanup_temp_preview_folder()

        selected_text = item.text()
        name_part = selected_text.split(" (")[0]
        tenant_id = self.tenant_data.get("id")
        match = next((doc for doc in self.documents if doc["name"] == name_part), None)
        if not match:
            return

        decrypted_path = self.doc_manager.decrypt_document_to_temp("tenant", tenant_id, match["filename"])
        if not decrypted_path:
            return

        if decrypted_path.lower().endswith((".png", ".jpg", ".jpeg")):
            self.preview_image(decrypted_path)
        elif decrypted_path.lower().endswith(".pdf"):
            webbrowser.open(decrypted_path)

    def preview_image(self, path):
        dialog = TempImagePreview(path, self)
        dialog.exec()

    def accept(self):
        data = self.collect_data()
        if not data:
            return

        if self.tenant_id:
            self.db.execute(
                """
                UPDATE tenants
                SET first_name = ?, last_name = ?, email = ?, phone = ?, date_of_birth = ?,
                    nationality = ?, emergency_contact = ?, status = ?
                WHERE tenant_id = ?
                """,
                (
                    data["first_name"], data["last_name"], data["email"], data["phone"],
                    data["date_of_birth"], data["nationality"], data["emergency_contact"],
                    data["status"], self.tenant_id
                )
            )
        else:
            self.db.execute(
                """
                INSERT INTO tenants (
                    first_name, last_name, email, phone, date_of_birth,
                    nationality, emergency_contact, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["first_name"], data["last_name"], data["email"], data["phone"],
                    data["date_of_birth"], data["nationality"], data["emergency_contact"],
                    data["status"]
                )
            )
        super().accept()
