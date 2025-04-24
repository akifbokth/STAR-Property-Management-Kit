import os  # This module is used for operating system dependent functionality
import sys # This module is used for system-specific parameters and functions
from PySide6.QtWidgets import ( # This module is used for creating the GUI components
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QPushButton,
    QLabel, QLineEdit, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QSettings # This module is used for managing application settings and animations
from PySide6.QtGui import QIcon # This module is used for handling icons and images
import sqlite3 # This module is used for SQL database operations
import atexit # This module is used for cleanup operations when the application exits

from scripts.dashboard_page import DashboardPage
from scripts.landlord_manager import LandlordManager
from scripts.tenant_manager import TenantManager
from scripts.property_manager import PropertyManager
from scripts.tenancy_manager import TenancyManager
from scripts.payment_manager import PaymentManager
from scripts.document_manager import DocumentManager
from scripts.maintenance_manager import MaintenanceManager
from scripts import encryption_manager
from scripts.setup_database import hash_password
from scripts.document_manager import TEMP_FILES_TO_CLEAN
from scripts.utils.file_utils import cleanup_temp_preview_folder
from scripts.admin_page import AdminPage
from config import DB_PATH, TEMP_PREVIEW_DIR, MAX_FILE_SIZE_MB

# Ensure encryption key exists
encryption_manager.generate_key()

ICON_PATHS = {
    "Dashboard": {"dark": "assets/icons/dark/dashboard_white.png", "light": "assets/icons/light/dashboard.png"},
    "Tenants": {"dark": "assets/icons/dark/tenants_white.png", "light": "assets/icons/light/tenants.png"},
    "Properties": {"dark": "assets/icons/dark/properties_white.png", "light": "assets/icons/light/properties.png"},
    "Landlords": {"dark": "assets/icons/dark/landlords_white.png", "light": "assets/icons/light/landlords.png"},
    "Tenancies": {"dark": "assets/icons/dark/tenancies_white.png", "light": "assets/icons/light/tenancies.png"},
    "Payments": {"dark": "assets/icons/dark/payments_white.png", "light": "assets/icons/light/payments.png"},
    "Maintenance": {"dark": "assets/icons/dark/maintenance_white.png", "light": "assets/icons/light/maintenance.png"},
    "Switch Theme": {"dark": "assets/icons/dark/theme_white.png", "light": "assets/icons/light/theme.png"},
    "Admin": {"dark": "assets/icons/dark/admin_white.png", "light": "assets/icons/light/admin.png"},
    "Logout": {"dark": "assets/icons/dark/logout_white.png", "light": "assets/icons/light/logout.png"},
}

def load_stylesheet(app, theme):
    path = f"styles_{theme}.qss"
    try:
        with open(path, "r") as file:
            app.setStyleSheet(file.read())
    except Exception as e:
        print(f"Error loading stylesheet: {e}")


# ======================================================
# ✅ LOGIN SCREEN
# ======================================================
class LoginScreen(QWidget):
    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller
        self.setWindowTitle("Login - Star Property Management")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("🔒 Star Property Management")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("SectionTitle")

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.authenticate_user)

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addLayout(form_layout)
        layout.addWidget(login_button)
        layout.addStretch()

        self.setLayout(layout)

    def authenticate_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        hashed_password = hash_password(password)  # Hash the password before comparing

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, username, is_admin FROM users WHERE username=? AND password=?", (username, hashed_password))
        result = cursor.fetchone()

        conn.close()

        if result:
            user = {"id": result[0], "username": result[1], "is_admin": bool(result[2])}
            self.app_controller.load_main_window(user)
            self.close()

        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password.")

# ======================================================
# ✅ STAR PROPERTY APP CONTROLLER
# ======================================================
class StarPropertyApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.settings = QSettings("StarPropertyManagement", "StarPMKit")

        # Clean the contents of the temp preview folder at startup
        # This is to ensure that any old files are removed before the app starts
        cleanup_temp_preview_folder()

        self.theme = self.settings.value("theme", "dark")
        load_stylesheet(self.app, self.theme)

        self.main_window = None
        self.login_screen = LoginScreen(self)
        self.login_screen.show()

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        load_stylesheet(self.app, self.theme)
        self.settings.setValue("theme", self.theme)

        if self.main_window:
            self.main_window.load_sidebar_items()

    def load_main_window(self, user):
        self.main_window = MainWindow(self, user)

        self.main_window.show()

    def run(self):
        sys.exit(self.app.exec())

# ======================================================
# ✅ MAIN WINDOW (AFTER LOGIN)
# ======================================================
class MainWindow(QMainWindow):
    def __init__(self, main_app, user):
        super().__init__()
        self.main_app = main_app
        self.user = user
        self.setWindowTitle("Star Property Management")
        self.resize(1200, 800)
        self.showMaximized()  # Open the main window in full screen

        # Central widget & layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)

        # Sidebar setup
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(200)
        self.sidebar.setIconSize(QSize(24, 24))
        self.sidebar.currentRowChanged.connect(self.handle_navigation)

        # Sidebar layout (no toggle button anymore)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.addWidget(self.sidebar)

        sidebar_container = QWidget()
        sidebar_container.setLayout(sidebar_layout)
        sidebar_container.setFixedWidth(200)

        # Pages for stacked widget
        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.tenant_page = TenantManager()
        self.property_page = PropertyManager()
        self.landlord_page = LandlordManager()
        self.tenancy_page = TenancyManager()
        self.payment_page = PaymentManager()
        self.maintenance_page = MaintenanceManager()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.tenant_page)
        self.stack.addWidget(self.property_page)
        self.stack.addWidget(self.landlord_page)
        self.stack.addWidget(self.tenancy_page)
        self.stack.addWidget(self.payment_page)
        self.stack.addWidget(self.maintenance_page)

        self.stack.setCurrentWidget(self.dashboard_page)

        if self.user["is_admin"]:
            self.admin_page = AdminPage(self.user)
            self.stack.addWidget(self.admin_page)

        # Add sidebar and pages to main layout
        main_layout.addWidget(sidebar_container)
        main_layout.addWidget(self.stack)

        # Build sidebar items once
        self.load_sidebar_items()

        self.sidebar.setCurrentRow(0)
        self.stack.setCurrentIndex(0)


    def create_label_page(self, text):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("PageLabel")
        layout.addWidget(label)
        page.setLayout(layout)
        return page

    def load_sidebar_items(self):
        self.sidebar.clear()
        theme = self.main_app.theme

        for name in ICON_PATHS.keys():
            if name == "Admin":
                continue  # Skip admin here; it will be added separately if user is admin
            icon_path = ICON_PATHS[name][theme]
            icon = QIcon(icon_path)
            item = QListWidgetItem(icon, f" {name}")
            self.sidebar.addItem(item)

        if self.user["is_admin"]:
            icon_path = ICON_PATHS["Admin"][theme]
            icon = QIcon(icon_path)
            admin_item = QListWidgetItem(icon, " Admin")
            self.sidebar.addItem(admin_item)

    def refresh_current_page(self):
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, 'load_data'): # Check if the current widget has a load_data method
            current_widget.load_data() # Call the load_data method to refresh the data


    def handle_navigation(self, index):
        item = self.sidebar.item(index)
        if not item:
            return

        text = item.text().strip()

        if text == "Dashboard":
            self.stack.setCurrentWidget(self.dashboard_page)

        elif text == "Tenants":
            self.stack.setCurrentWidget(self.tenant_page)
            self.tenant_page.load_data() 

        elif text == "Properties":
            self.stack.setCurrentWidget(self.property_page)
            self.property_page.load_data()

        elif text == "Landlords":
            self.stack.setCurrentWidget(self.landlord_page)
            self.landlord_page.load_data()

        elif text == "Tenancies":
            self.stack.setCurrentWidget(self.tenancy_page)
            self.tenancy_page.load_data()

        elif text == "Payments":
            self.stack.setCurrentWidget(self.payment_page)
            self.payment_page.load_data()

        elif text == "Maintenance":
            self.stack.setCurrentWidget(self.maintenance_page)
            self.maintenance_page.load_data()

        elif text == "Switch Theme":
            self.main_app.toggle_theme()
            self.load_sidebar_items()

        elif text == "Logout":
            self.close()

        elif text == "Admin" and self.user["is_admin"]:
            self.stack.setCurrentWidget(self.admin_page)



# ======================================================
# ✅ APPLICATION ENTRY POINT
# ======================================================
if __name__ == "__main__":
    app = StarPropertyApp()
    app.run()

    def clean_temp_files():
        for path in TEMP_FILES_TO_CLEAN:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"[WARN] Failed to delete temp file: {e}")

    atexit.register(clean_temp_files)
