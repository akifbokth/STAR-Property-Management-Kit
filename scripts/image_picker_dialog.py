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

class ImagePickerDialog(QDialog):
    def __init__(self, property_id, door_number, street, postcode):
        super().__init__()
        self.setWindowTitle("🖼️ Property Images Manager")
        self.property_id = property_id
        # Create a folder using the naming convention "ID_DoorNumber_Street_Postcode" under the "properties" folder.
        self.folder_path = self.create_property_folder(property_id, door_number, street, postcode)
        self.db = DatabaseManager()
        self.setup_ui()
        self.load_images()

    def create_property_folder(self, property_id, door_number, street, postcode):
        # Build a safe folder name in the format "ID_DoorNumber_Street_Postcode"
        safe_name = f"{property_id}_{door_number}_{street}_{postcode}".replace(" ", "_")
        # The images will be stored in: properties/<safe_name>/property_images
        folder = os.path.join("properties", safe_name, "property_images")
        os.makedirs(folder, exist_ok=True)
        return folder

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

    def upload_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                filename = os.path.basename(file_path)
                # Create a unique file name using a timestamp.
                dest_path = os.path.join(self.folder_path, f"{int(time.time())}_{filename}")
                shutil.copy(file_path, dest_path)
                self.db.execute("""
                    INSERT INTO property_images (property_id, image_path, uploaded_date)
                    VALUES (?, ?, DATE('now'))
                """, (self.property_id, dest_path))
        self.load_images()

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

    def preview_image(self, item):
        _, image_path = item.data(Qt.UserRole)
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Image Preview")
        layout = QVBoxLayout()
        image_label = QLabel()
        pixmap = QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(image_label)
        preview_dialog.setLayout(layout)
        preview_dialog.exec()
