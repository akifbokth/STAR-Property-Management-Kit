import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QDateEdit, QMessageBox
)
from PySide6.QtCore import QDate
from scripts.document_manager import DocumentManager
from config import MAX_FILE_SIZE_MB
from config import DOCUMENT_TYPES



class DocumentPickerDialog(QDialog):
    def __init__(self, entity_type, entity_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Document")
        self.entity_type = entity_type
        self.entity_id = entity_id

        self.doc_manager = DocumentManager()

        layout = QVBoxLayout()

        # Document name
        layout.addWidget(QLabel("Document Name:"))
        self.name_input = QLineEdit()
        self.name_input.setToolTip("Enter a name for this document (e.g., 'Passport')")
        layout.addWidget(self.name_input)

        # Document type
        layout.addWidget(QLabel("Document Type:"))
        self.type_input = QComboBox()

        # Entity-specific document types
        self.type_input.addItems(DOCUMENT_TYPES.get(self.entity_type, ["Other"]))
        
        self.type_input.setToolTip("Choose the document type")
        layout.addWidget(self.type_input)

        # Expiry date
        layout.addWidget(QLabel("Expiry Date:"))
        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDate(QDate.currentDate())
        self.expiry_input.setToolTip("Only applies to property documents")
        layout.addWidget(self.expiry_input)

        if entity_type != 'property':
            self.expiry_input.setEnabled(False)
            self.expiry_input.setVisible(False)

        # File selection
        self.file_path = None
        self.select_button = QPushButton("Select File")
        self.select_button.setToolTip(f"Choose a file to upload (max size: {MAX_FILE_SIZE_MB} MB)")
        self.select_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_button)

        # Upload
        self.upload_button = QPushButton("Upload")
        self.upload_button.setToolTip("Upload this document to the system")
        self.upload_button.clicked.connect(self.upload_file)
        layout.addWidget(self.upload_button)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_path = file_path
            self.select_button.setText(os.path.basename(file_path))

    def upload_file(self):
        self.upload_button.setEnabled(False)

        name = self.name_input.text().strip()
        doc_type = self.type_input.currentText()
        expiry = self.expiry_input.date().toString("yyyy-MM-dd") if self.entity_type == "property" else None

        # Check file size
        if os.path.getsize(self.file_path) > MAX_FILE_SIZE_MB * 1024 * 1024:
            QMessageBox.warning(self, 'File Too Large', f'File exceeds {MAX_FILE_SIZE_MB} MB limit.')
            self.upload_button.setEnabled(True)
            return

        if not name or not self.file_path:
            QMessageBox.warning(self, "Missing Info", "Please provide a name and select a file.")
            self.upload_button.setEnabled(True)
            return

        success = self.doc_manager.upload_document(
            self.entity_type, self.entity_id, name, doc_type, expiry, self.file_path
        )

        if success:
            QMessageBox.information(self, "Success", "Document uploaded successfully.")
            self.upload_button.setEnabled(True)
            self.accept()
        else:
            QMessageBox.critical(self, "Failure", "Failed to upload document.")
            self.upload_button.setEnabled(True)
