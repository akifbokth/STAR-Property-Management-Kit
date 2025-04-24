from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QCheckBox, QLabel, QFormLayout
import sqlite3
from scripts.setup_database import hash_password
from config import DB_PATH


class UserManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Manager")
        self.resize(500, 400)
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Username", "Is Admin", "User ID"])
        self.table.setColumnHidden(2, True)  # hide user_id
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add User")
        self.edit_btn = QPushButton("Edit User")
        self.delete_btn = QPushButton("Delete User")

        self.add_btn.clicked.connect(self.add_user)
        self.edit_btn.clicked.connect(self.edit_user)
        self.delete_btn.clicked.connect(self.delete_user)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

    def load_users(self):
        self.table.setRowCount(0)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, is_admin FROM users")
        for row_idx, (user_id, username, is_admin) in enumerate(cur.fetchall()):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(username))
            self.table.setItem(row_idx, 1, QTableWidgetItem("Yes" if is_admin else "No"))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(user_id)))
        conn.close()

    def add_user(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New User")
        layout = QFormLayout(dialog)

        username_input = QLineEdit()
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        confirm_password_input = QLineEdit()
        confirm_password_input.setEchoMode(QLineEdit.Password)
        is_admin_checkbox = QCheckBox("Admin")

        layout.addRow("Username:", username_input)
        layout.addRow("Password:", password_input)
        layout.addRow("Confirm Password:", confirm_password_input)
        layout.addRow("", is_admin_checkbox)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

        save_btn.clicked.connect(lambda: self.save_user(
            dialog,
            username_input.text(),
            password_input.text(),
            confirm_password_input.text(),
            is_admin_checkbox.isChecked()
        ))
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def save_user(self, dialog, username, password, confirm_password, is_admin):
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match. Please try again.")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                        (username, hash_password(password), int(is_admin)))
            conn.commit()
            QMessageBox.information(self, "Success", "User created successfully.")
            dialog.accept()
            self.load_users()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Username already exists.")
        finally:
            conn.close()

    def edit_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select User", "Please select a user to edit.")
            return

        username = self.table.item(row, 0).text()
        is_admin = self.table.item(row, 1).text() == "Yes"
        user_id = int(self.table.item(row, 2).text())

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit User")
        layout = QFormLayout(dialog)

        password_input = QLineEdit()
        password_input.setPlaceholderText("Leave blank to keep current password")
        password_input.setEchoMode(QLineEdit.Password)
        confirm_password_input = QLineEdit()
        confirm_password_input.setPlaceholderText("Retype password")
        confirm_password_input.setEchoMode(QLineEdit.Password)
        is_admin_checkbox = QCheckBox("Admin")
        is_admin_checkbox.setChecked(is_admin)

        layout.addRow(QLabel(f"Editing user: {username}"))
        layout.addRow("New Password:", password_input)
        layout.addRow("Confirm Password:", confirm_password_input)
        layout.addRow("", is_admin_checkbox)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        cancel_btn = QPushButton("Cancel")
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

        def save_changes():
            new_pass = password_input.text().strip()
            confirm_pass = confirm_password_input.text().strip()
            new_admin = int(is_admin_checkbox.isChecked())
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            if new_pass:
                if new_pass != confirm_pass:
                    QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
                    return
                cur.execute("UPDATE users SET password=?, is_admin=? WHERE user_id=?",
                            (hash_password(new_pass), new_admin, user_id))
            else:
                cur.execute("UPDATE users SET is_admin=? WHERE user_id=?", (new_admin, user_id))

            conn.commit()
            conn.close()
            QMessageBox.information(self, "Updated", "User updated successfully.")
            dialog.accept()
            self.load_users()

        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def delete_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select User", "Please select a user to delete.")
            return

        username = self.table.item(row, 0).text()
        user_id = int(self.table.item(row, 2).text())

        if username.lower() == "admin":
            QMessageBox.warning(self, "Action Denied", "The 'admin' user cannot be deleted.")
            return

        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete user '{username}'?")
        if confirm == QMessageBox.Yes:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Deleted", "User deleted successfully.")
            self.load_users()
