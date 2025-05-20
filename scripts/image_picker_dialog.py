import os
import shutil
import time
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLabel, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from scripts.database_manager import DatabaseManager
from config import PROPERTIES_DIR


# ImagePickerDialog class to manage property images
# This class handles the upload, deletion, and previewing of images associated with a property.
# It uses a QListWidget to display the images and allows users to upload new images or delete existing ones.
# The images are stored in a folder named using the property ID, door number, street, and postcode.
# The images are also stored in a SQLite database with a reference to the property ID.

class ImagePickerDialog(QDialog): # This class inherits from QDialog to create a custom dialog
    def __init__(self, property_id, door_number, street, postcode):
        super().__init__()
        self.setWindowTitle("🖼️ Property Images Manager")
        self.property_id = property_id
        # Create a folder using the naming convention "ID_DoorNumber_Street_Postcode" under the "properties" folder.
        self.folder_path = self.create_property_folder(property_id, door_number, street, postcode)
        self.db = DatabaseManager()
        self.setup_ui()
        self.load_images()

    def create_property_folder(self, property_id, door_number, street, postcode): # Create a folder for the property images

        # Create a safe name for the folder using the property ID, door number, street, and postcode.
        safe_name = f"{property_id}_{door_number}_{street}_{postcode}".replace(" ", "_")
        # resources/properties/<safe_name>/property_images
        folder = os.path.join(PROPERTIES_DIR, safe_name, "property_images")
        os.makedirs(folder, exist_ok=True)
        return folder

    # Setup the UI for the dialog
    def setup_ui(self):
        layout = QVBoxLayout()

        # Image list
        self.image_list = QListWidget()
        self.image_list.itemDoubleClicked.connect(self.preview_image)

        # Buttons layout
        button_layout = QHBoxLayout()
        upload_button = QPushButton("Upload Image")
        upload_button.clicked.connect(self.upload_image)
        delete_button = QPushButton("Delete Image")
        delete_button.clicked.connect(self.delete_selected_image)

        button_layout.addWidget(upload_button)
        button_layout.addWidget(delete_button)

        layout.addWidget(self.image_list)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    # Load images from the database and display them in the list widget
    # This method retrieves the images associated with the property ID from the database
    def load_images(self):
        self.image_list.clear()
        query = """
            SELECT image_id, image_path
            FROM property_images
            WHERE property_id = ?
        """
        images = self.db.execute(query, (self.property_id,), fetchall=True)
        for image in images:
            image_id, image_path = image
            item = QListWidgetItem(os.path.basename(image_path))
            item.setData(Qt.UserRole, (image_id, image_path))
            item.setIcon(QIcon(image_path))
            self.image_list.addItem(item)

    # Upload an image to the property folder and store its path in the database
    # This method opens a file dialog to select images and copies them to the property folder
    def upload_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles) # Allow multiple file selection
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files: # Iterate through the selected files
                filename = os.path.basename(file_path)
                # Create a unique file name using a timestamp.
                dest_path = os.path.join(self.folder_path, f"{int(time.time())}_{filename}") # Create a unique file name
                shutil.copy(file_path, dest_path) # Copy the selected file to the destination path
                self.db.execute("""
                    INSERT INTO property_images (property_id, image_path, uploaded_date)
                    VALUES (?, ?, DATE('now'))
                """, (self.property_id, dest_path)) # Insert the image path into the database
        self.load_images()

    # Delete the selected image from the list and the database
    # This method removes the selected image from the database and deletes it from the file system
    def delete_selected_image(self):
        selected = self.image_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select an image to delete.")
            return
        image_id, image_path = selected.data(Qt.UserRole)
        confirm = QMessageBox.question(self, "Delete Image", "Are you sure you want to delete this image?")
        if confirm == QMessageBox.Yes:
            if os.path.exists(image_path):
                os.remove(image_path)
            self.db.execute("DELETE FROM property_images WHERE image_id = ?", (image_id,))
            self.load_images()

    # Preview the selected image in a dialog
    # This method opens a dialog to display the selected image
    def preview_image(self, item):
        _, image_path = item.data(Qt.UserRole) # Get the image path from the item data
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Image Preview")
        layout = QVBoxLayout()
        image_label = QLabel()
        pixmap = QPixmap(image_path) # Load the image using QPixmap
        image_label.setPixmap(pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)) 
        # Scale the image to fit the dialog
        layout.addWidget(image_label)
        preview_dialog.setLayout(layout)
        preview_dialog.exec()
