import os
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class TempImagePreview(QDialog):
    def __init__(self, img_path, parent=None):
        super().__init__(parent)
        self.img_path = img_path
        self.setWindowTitle("Image Preview")

        layout = QVBoxLayout()
        label = QLabel()
        label.setPixmap(QPixmap(img_path).scaledToWidth(600, Qt.SmoothTransformation))
        layout.addWidget(label)
        self.setLayout(layout)

    def closeEvent(self, event):
        try:
            if os.path.exists(self.img_path):
                os.remove(self.img_path)
        except Exception as e:
            print(f"[ImagePreview] Cleanup failed: {e}")
        super().closeEvent(event)
