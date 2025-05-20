import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QDateEdit, QMessageBox
)
from PySide6.QtCore import QDate
from scripts.document_manager import DocumentManager
from config import MAX_FILE_SIZE_MB
from config import DOCUMENT_TYPES


# DocumentPickerDialog class to create a dialog for selecting and uploading documents
# This dialog allows users to select a file, enter a name, and choose a document type  
# for different entities (tenants, landlords, properties, tenancies) in the database.
# The dialog also handles the encryption and storage of the selected file, ensuring that sensitive information is stored securely.

class DocumentPickerDialog(QDialog): # This class inherits from QDialog to create a custom dialog
    def __init__(self, entity_type, entity_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Document")
        self.entity_type = entity_type
        self.entity_id = entity_id

        self.doc_manager = DocumentManager()

        layout = QVBoxLayout()

        # Document name
        # This is the name that will be displayed in the document list
        layout.addWidget(QLabel("Document Name:"))
        self.name_input = QLineEdit()
        self.name_input.setToolTip("Enter a name for this document (e.g., 'Passport')")
        layout.addWidget(self.name_input)

        # Document type
        # This is the type of document being uploaded
        layout.addWidget(QLabel("Document Type:"))
        self.type_input = QComboBox()

        # Entity-specific document types
        # This is a dictionary that maps entity types to their respective document types
        # The document types are defined in the config file
        self.type_input.addItems(DOCUMENT_TYPES.get(self.entity_type, ["Other"]))
        
        self.type_input.setToolTip("Choose the document type")
        layout.addWidget(self.type_input)

        # Expiry date
        # This is the date when the document expires
        # This field is only applicable for property documents
        layout.addWidget(QLabel("Expiry Date:"))
        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDate(QDate.currentDate())
        self.expiry_input.setToolTip("Only applies to property documents")
        layout.addWidget(self.expiry_input)

        if entity_type != 'property': # If the entity type is not property, hide the expiry date field
            self.expiry_input.setEnabled(False)
            self.expiry_input.setVisible(False)

        # File selection
        # This is the button that allows users to select a file to upload
        self.file_path = None
        self.select_button = QPushButton("Select File")
        self.select_button.setToolTip(f"Choose a file to upload (max size: {MAX_FILE_SIZE_MB} MB)")
        self.select_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_button)

        # Upload
        # This is the button that initiates the upload process
        # This button is disabled until a file is selected and the name is provided
        self.upload_button = QPushButton("Upload")
        self.upload_button.setToolTip("Upload this document to the system")
        self.upload_button.clicked.connect(self.upload_file)
        layout.addWidget(self.upload_button)

        self.setLayout(layout)

    # Select file button
    # This method opens a file dialog to select a file for upload
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_path = file_path
            self.select_button.setText(os.path.basename(file_path))

    # Upload file button
    # This method handles the upload process, including file size checks and database interactions
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

        # Check if name and file path are provided
        # If the name or file path is empty, show a warning message
        if not name or not self.file_path:
            QMessageBox.warning(self, "Missing Info", "Please provide a name and select a file.")
            self.upload_button.setEnabled(True)
            return

        # Upload the document
        # This method handles the encryption of the document and stores it in the appropriate folder
        success = self.doc_manager.upload_document(
            self.entity_type, self.entity_id, name, doc_type, expiry, self.file_path
        )
        # If the upload is successful, show a success message and close the dialog
        if success:
            QMessageBox.information(self, "Success", "Document uploaded successfully.")
            self.upload_button.setEnabled(True)
            self.accept()
        else: # If the upload fails, show an error message
            QMessageBox.critical(self, "Failure", "Failed to upload document.")
            self.upload_button.setEnabled(True)
