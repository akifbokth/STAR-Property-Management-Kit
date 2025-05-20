from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtWidgets import QMessageBox, QLineEdit, QCheckBox, QLabel, QFormLayout, QAbstractItemView
import sqlite3
from scripts.utils.security_utils import hash_password
from config import DB_PATH

# UserManager is a QDialog that manages user accounts in the application.
# It allows the admin to add, edit, and delete users, as well as manage their permissions.
# The user data is stored in a SQLite database, and the password is hashed for security.
# The dialog provides a table view of the users, and buttons for adding, editing, and deleting users.
# The dialog also includes input validation to ensure that the username and password fields are filled out correctly.

class UserManager(QDialog): # UserManager class inherits from QDialog
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Manager")
        self.resize(500, 400)
        self.setup_ui()
        self.load_users()

    def setup_ui(self): # Setup the UI for the UserManager dialog
        layout = QVBoxLayout(self) # Create a vertical layout for the dialog

        self.table = QTableWidget()
        self.table.setColumnCount(3) # Set the number of columns in the table
        self.table.setHorizontalHeaderLabels(["Username", "Is Admin", "User ID"]) # Set the header labels for the table

        # Prevent in-place editing of table cells
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Disable editing of table cells
        self.table.setColumnHidden(2, True)  # hide user_id
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add User") # Button to add a new user
        self.edit_btn = QPushButton("Edit User") # Button to edit an existing user
        self.delete_btn = QPushButton("Delete User") # Button to delete a user

        self.add_btn.clicked.connect(self.add_user) # Connect the add button to the add_user method
        self.edit_btn.clicked.connect(self.edit_user) # Connect the edit button to the edit_user method
        self.delete_btn.clicked.connect(self.delete_user) # Connect the delete button to the delete_user method

        btn_layout.addWidget(self.add_btn) # Add the add button to the button layout
        btn_layout.addWidget(self.edit_btn) # Add the edit button to the button layout
        btn_layout.addWidget(self.delete_btn) # Add the delete button to the button layout
        layout.addLayout(btn_layout) # Add the button layout to the main layout

    def load_users(self): # Load the user data from the database and populate the table
        self.table.setRowCount(0) # Clear the table before loading new data
        conn = sqlite3.connect(DB_PATH) # Connect to the SQLite database
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, is_admin FROM users") # Execute a query to get all users

        for row_idx, (user_id, username, is_admin) in enumerate(cur.fetchall()): # Fetch all user data
            self.table.insertRow(row_idx) # Insert a new row in the table for each user
            self.table.setItem(row_idx, 0, QTableWidgetItem(username))
            self.table.setItem(row_idx, 1, QTableWidgetItem("Yes" if is_admin else "No")) # Set the admin status
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(user_id)))
        conn.close()

# The add_user method opens a dialog to create a new user account.
# It collects the username, password, and admin status from the user.

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


# The save_user method is called when the user clicks the "Save" button in the add_user dialog.
# It validates the input, hashes the password, and saves the new user to the database.
# It also handles errors such as missing fields or password mismatch.

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

# The edit_user method opens a dialog to edit an existing user account.
# It pre-fills the dialog with the current user data and allows the admin to change the password and admin status.

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

        # Save changes to the database
        def save_changes():
            new_pass = password_input.text().strip()
            confirm_pass = confirm_password_input.text().strip()
            new_admin = int(is_admin_checkbox.isChecked())

            # Prevent removing admin rights from the last admin
            if not is_admin_checkbox.isChecked():
                conn_check = sqlite3.connect(DB_PATH)
                cur_check = conn_check.cursor()
                cur_check.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
                admin_count = cur_check.fetchone()[0]
                conn_check.close()
                # If this is the only admin, block unchecking
                if admin_count <= 1 and is_admin:
                    QMessageBox.warning(
                        self,
                        "Action Denied",
                        "Cannot remove admin rights from the last administrator."
                    )
                    return

            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            # Update user details in the database
            # If password is provided, update it
            # If not, just update the admin status
            if new_pass:
                if new_pass != confirm_pass: # Check if passwords match
                    QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
                    return
                cur.execute(
                    "UPDATE users SET password = ?, is_admin = ? WHERE user_id = ?",
                    (hash_password(new_pass), new_admin, user_id)
                )
            else: # If no new password, just update the admin status
                cur.execute(
                    "UPDATE users SET is_admin = ? WHERE user_id = ?",
                    (new_admin, user_id)
                )

            conn.commit()
            conn.close()
            QMessageBox.information(self, "Updated", "User updated successfully.")
            dialog.accept() # Close the dialog
            self.load_users() # Reload the user list

        save_btn.clicked.connect(save_changes) # Save changes if save button is clicked
        cancel_btn.clicked.connect(dialog.reject) # Close the dialog if cancel is clicked
        dialog.exec()


# The delete_user method deletes a user account from the database.
# It checks if the user is the admin account and prevents deletion if so.
# It also confirms the deletion with the admin before proceeding.
# The method also handles errors such as trying to delete the admin account.

    def delete_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select User", "Please select a user to delete.")
            return

        username = self.table.item(row, 0).text()
        user_id = int(self.table.item(row, 2).text())

        if username.lower() == "admin": # Prevent deletion of the admin account
            QMessageBox.warning(self, "Action Denied", "The 'admin' user cannot be deleted.")
            return

        # Confirm deletion with the admin
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete user '{username}'?")
        if confirm == QMessageBox.Yes:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Deleted", "User deleted successfully.")
            self.load_users()
