from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt
from scripts.utils.user_manager import UserManager
import os
import shutil
from datetime import datetime
from config import DB_PATH

class AdminPage(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Admin Panel")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # User Management
        user_mgmt_btn = QPushButton("Manage Users")
        user_mgmt_btn.clicked.connect(self.manage_users)
        layout.addWidget(user_mgmt_btn)

        # Activity Logs
        logs_btn = QPushButton("View Activity Logs")
        logs_btn.clicked.connect(self.view_logs)
        layout.addWidget(logs_btn)

        # System Maintenance
        cleanup_btn = QPushButton("Clean Temp Files")
        cleanup_btn.clicked.connect(self.clean_temp)
        layout.addWidget(cleanup_btn)

        # Database Backup
        backup_btn = QPushButton("Create Backup")
        backup_btn.clicked.connect(self.create_backup)
        layout.addWidget(backup_btn)

        self.setLayout(layout)

    def manage_users(self):
        dialog = UserManager(self)
        dialog.exec()

    def view_logs(self):
        QMessageBox.information(self, "Coming Soon", "Activity log viewer will be implemented here.")

    def clean_temp(self):
        try:
            shutil.rmtree("temp_preview", ignore_errors=True)
            QMessageBox.information(self, "Temp Cleaned", "Temporary preview files deleted successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not clean temp files:\n{e}")

    def create_backup(self):
        try:
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy(DB_PATH, f"{backup_dir}/backup_{timestamp}.db")
            QMessageBox.information(self, "Backup Complete", f"Database backed up as backup_{timestamp}.db")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backup failed:\n{e}")
