import os
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

# TempImagePreview is a QDialog that displays a temporary image preview.
# It is used to show images in a dialog window, and it cleans up the temporary image file when the dialog is closed.
# The image is displayed using a QLabel, and the dialog can be closed by the user.

class TempImagePreview(QDialog): # TempImagePreview class inherits from QDialog
    def __init__(self, img_path, parent=None):
        super().__init__(parent)
        self.img_path = img_path
        self.setWindowTitle("Image Preview")

        layout = QVBoxLayout() # Create a vertical layout for the dialog
        label = QLabel() # Create a label to display the image
        label.setPixmap(QPixmap(img_path).scaledToWidth(600, Qt.SmoothTransformation)) # Load the image and scale it to fit the label
        layout.addWidget(label) # Add the label to the layout
        self.setLayout(layout) # Set the layout for the dialog

    def closeEvent(self, event): # Override the close event to clean up the temporary image file
        # This is called when the dialog is closed
        try:
            if os.path.exists(self.img_path): # Check if the image file exists
                os.remove(self.img_path) # Remove the image file
        except Exception as e: # Handle any exceptions that occur during cleanup
            print(f"[ImagePreview] Cleanup failed: {e}") # Log the error if cleanup fails
        super().closeEvent(event) # Call the base class close event to ensure the dialog closes properly
