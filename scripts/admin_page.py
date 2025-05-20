from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt
from scripts.utils.user_manager import UserManager
from config import BACKUPS_DIR, TEMP_PREVIEW_DIR, DB_PATH
import shutil, os
from datetime import datetime


# This is the admin page for the application.
# It provides various administrative functions such as user management,
# viewing activity logs, cleaning temporary files, and creating backups.
# The admin page is only accessible to users with admin privileges.

# The AdminPage class is a QWidget that contains buttons for each of the admin functions.
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
        # This button opens a dialog for managing users.
        # The UserManager class is responsible for handling user management tasks.
        user_mgmt_btn = QPushButton("Manage Users")
        user_mgmt_btn.clicked.connect(self.manage_users)
        layout.addWidget(user_mgmt_btn)

        # Activity Logs
        # This doesnt do anything yet, but it will be implemented in the future.
        logs_btn = QPushButton("View Activity Logs")
        logs_btn.clicked.connect(self.view_logs)
        layout.addWidget(logs_btn)

        # Temporary Files Cleanup
        # This button cleans up the temporary preview files.
        # The TEMP_PREVIEW_DIR is the directory where temporary files are stored.
        cleanup_btn = QPushButton("Clean Temp Files")
        cleanup_btn.clicked.connect(self.clean_temp)
        layout.addWidget(cleanup_btn)

        # Database Backup
        # This button creates a backup of the SQLite database.
        # The BACKUPS_DIR is the directory where backups are stored.
        backup_btn = QPushButton("Create Backup")
        backup_btn.clicked.connect(self.create_backup)
        layout.addWidget(backup_btn)

        self.setLayout(layout)


    def manage_users(self): # This function opens the user management dialog.
        dialog = UserManager(self)
        dialog.exec()

    def view_logs(self): # This function will be implemented in the future.
        QMessageBox.information(self, "Coming Soon", "Activity log viewer will be implemented here.")

    def clean_temp(self): # This function cleans up the temporary preview files.
        try:
            shutil.rmtree(TEMP_PREVIEW_DIR, ignore_errors=True) # Remove the temporary preview directory and its contents
            QMessageBox.information(self, "Temp Cleaned",
                                    "Temporary preview files deleted successfully.")
        except Exception as e: # Handle any exceptions that occur during cleanup
            QMessageBox.critical(self, "Error",
                                 f"Could not clean temp files:\n{e}")

    def create_backup(self): # This function creates a backup of the SQLite database.
        # It copies the database file to the BACKUPS_DIR with a timestamp.
        try:
            os.makedirs(BACKUPS_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(BACKUPS_DIR, f"backup_{timestamp}.db")
            shutil.copy(DB_PATH, dest)
            QMessageBox.information(self, "Backup Complete",
                                    f"Backup saved as:\n{dest}")
        except Exception as e: # Handle any exceptions that occur during backup
            QMessageBox.critical(self, "Error", f"Backup failed:\n{e}")