import os  # This module is used for operating system dependent functionality
import sys # This module is used for system-specific parameters and functions
from PySide6.QtWidgets import ( # This module is used for creating the GUI components
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QPushButton,
    QLabel, QLineEdit, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QSettings # This module is used for managing application settings and animations
from PySide6.QtGui import QIcon # This module is used for handling icons and images
import sqlite3 # This module is used for SQL database operations
import atexit # This module is used for cleanup operations when the application exits

import config # This module contains configuration settings for the application
from scripts.dashboard_page import DashboardPage # This module contains the dashboard page of the application
from scripts.landlord_manager import LandlordManager # This module contains the landlord management functionalities
from scripts.tenant_manager import TenantManager # This module contains the tenant management functionalities
from scripts.property_manager import PropertyManager # This module contains the property management functionalities
from scripts.tenancy_manager import TenancyManager # This module contains the tenancy management functionalities
from scripts.payment_manager import PaymentManager # This module contains the payment management functionalities
from scripts.document_manager import DocumentManager # This module contains the document management functionalities
from scripts.utils.security_utils import hash_password # This module contains security-related utilities
from scripts.maintenance_manager import MaintenanceManager # This module contains the maintenance management functionalities
from scripts import encryption_manager # This module contains encryption-related functionalities
from scripts.document_manager import TEMP_FILES_TO_CLEAN # This module allows the temporary files to be cleaned
from scripts.utils.file_utils import cleanup_temp_preview_folder # This module allows the temporary files to be cleaned
from scripts.admin_page import AdminPage # This module contains the admin page functionalities
from config import DB_PATH, ICON_PATH, TEMP_PREVIEW_DIR, MAX_FILE_SIZE_MB # This module contains config settings for the application
from config import resource_path # This module contains the resource path functionalities

# ================ #
# INITIALISATION
# ================ #

required_folders = [
    config.STORAGE_PATHS["tenant"], # Ensure the tenants directory exists
    config.STORAGE_PATHS["property"], # Ensure the properties directory exists
    config.STORAGE_PATHS["landlord"], # Ensure the landlords directory exists
    config.STORAGE_PATHS["tenancy"], # Ensure the tenancies directory exists
    config.BACKUPS_DIR, # Ensure the backups directory exists
    config.TEMP_PREVIEW_DIR, # Ensure the temp preview directory exists
    ]

for folder in required_folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Ensure encryption key exists
encryption_manager.generate_key()

ICON_PATHS = { # This dictionary contains the paths to the icons used in the application
    "Dashboard": {
        "dark": resource_path("assets/icons/dark/dashboard_white.png"),
        "light": resource_path("assets/icons/light/dashboard.png"),
    },
    "Tenants": {
        "dark": resource_path("assets/icons/dark/tenants_white.png"),
        "light": resource_path("assets/icons/light/tenants.png"),
    },
    "Properties": {
        "dark": resource_path("assets/icons/dark/properties_white.png"),
        "light": resource_path("assets/icons/light/properties.png"),
    },
    "Landlords": {
        "dark": resource_path("assets/icons/dark/landlords_white.png"),
        "light": resource_path("assets/icons/light/landlords.png"),
    },
    "Tenancies": {
        "dark": resource_path("assets/icons/dark/tenancies_white.png"),
        "light": resource_path("assets/icons/light/tenancies.png"),
    },
    "Payments": {
        "dark": resource_path("assets/icons/dark/payments_white.png"),
        "light": resource_path("assets/icons/light/payments.png"),
    },
    "Maintenance": {
        "dark": resource_path("assets/icons/dark/maintenance_white.png"),
        "light": resource_path("assets/icons/light/maintenance.png"),
    },
    "Admin": {
        "dark": resource_path("assets/icons/dark/admin_white.png"),
        "light": resource_path("assets/icons/light/admin.png"),
    },
    "Switch Theme": {
        "dark": resource_path("assets/icons/dark/theme_white.png"),
        "light": resource_path("assets/icons/light/theme.png"),
    },
    "Logout": {
        "dark": resource_path("assets/icons/dark/logout_white.png"),
        "light": resource_path("assets/icons/light/logout.png"),
    },
}

# ==================== #
# STYLESHEET LOADING
# ==================== #

# Load the stylesheet based on the theme
def load_stylesheet(app, theme):
    filename = f"styles/styles_{theme}.qss"
    path = resource_path(filename)
    try:
        with open(path, "r") as file:
            app.setStyleSheet(file.read())
    except Exception as e:
        print(f"Error loading stylesheet: {e}")

# Function to get the resource path
def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    try:
        base_path = sys._MEIPASS  # PyInstaller sets this
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ============== #
# LOGIN SCREEN
# ============== #

# This class handles the login screen of the application
class LoginScreen(QWidget):
    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller
        self.setWindowTitle("Login - STAR Property Management Kit")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self): # This method sets up the UI components of the login screen
        layout = QVBoxLayout()

        title = QLabel("🔒 STAR Property Management Kit")
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

    def authenticate_user(self): # This method handles the authentication of the user
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password: # Check if username and password are provided
            # Show a warning message if either field is empty
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        hashed_password = hash_password(password)  # Hash the password before comparing

        conn = sqlite3.connect(DB_PATH) # Connect to the database
        cursor = conn.cursor() # Create a cursor object to execute SQL commands

        cursor.execute("SELECT user_id, username, is_admin FROM users WHERE username=? AND password=?", (username, hashed_password))
        result = cursor.fetchone() # Fetch the result of the query

        conn.close()

        # Check if the result is not None
        # If the result is not None, it means the user exists
        # and the password is correct
        if result:
            user = {"id": result[0], "username": result[1], "is_admin": bool(result[2])}
            self.app_controller.load_main_window(user)
            self.close()

        # If the result is None, it means the user does not exist
        # or the password is incorrect
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password.")

# ========================= #
# STAR PMK APP CONTROLLER
# ========================= #

# This class handles the main application logic and flow
class STARPMKApp:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.app.setWindowIcon(QIcon(ICON_PATH)) # Set the application icon

        self.settings = QSettings("STARPropertyManagementKit", "STARPMK")

        # Clean the contents of the temp preview folder at startup
        # This is to ensure that any old files are removed before the app starts
        cleanup_temp_preview_folder()

        self.theme = self.settings.value("theme", "dark") # Load the theme from settings or default to dark
        load_stylesheet(self.app, self.theme) # Load the stylesheet based on the theme

        self.main_window = None # This will hold the main window instance
        self.login_screen = LoginScreen(self) # Create an instance of the login screen
        self.login_screen.show() # Show the login screen

    def toggle_theme(self): # This method toggles the theme between light and dark
        self.theme = "light" if self.theme == "dark" else "dark"
        load_stylesheet(self.app, self.theme)
        self.settings.setValue("theme", self.theme)

        if self.main_window: # If the main window is open, reload the sidebar items
            self.main_window.load_sidebar_items() # This is to ensure that the icons are updated based on the new theme

    def load_main_window(self, user): # This method loads the main window after successful login
        self.main_window = MainWindow(self, user) # Create an instance of the main window
        self.main_window.show()

    def run(self): # This method runs the application
        sys.exit(self.app.exec()) # This is to ensure that the application exits cleanly

# ============================ #
# MAIN WINDOW (AFTER LOGIN)
# ============================ #

# This class handles the main window of the application after login
class MainWindow(QMainWindow):
    def __init__(self, main_app, user):
        super().__init__() # Initialize the main window
        self.main_app = main_app
        self.user = user
        self.setWindowTitle("STAR Property Management Kit")
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

        # Sidebar layout
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

        # Add admin page to sidebar if user is admin
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

    def create_label_page(self, text): # This method creates labels for the stacked widget
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("PageLabel")
        layout.addWidget(label)
        page.setLayout(layout)
        return page

    def load_sidebar_items(self): # This method loads the sidebar items
        self.sidebar.clear() # Clear existing items
        theme = self.main_app.theme

        for name in ICON_PATHS.keys(): # Iterate through the icon paths
            if name == "Admin":
                continue  # Skip admin here; it will be added separately if user is admin
            icon_path = ICON_PATHS[name][theme]
            icon = QIcon(icon_path)
            item = QListWidgetItem(icon, f" {name}")
            self.sidebar.addItem(item)

        if self.user["is_admin"]: # If the user is an admin, add the admin item
            icon_path = ICON_PATHS["Admin"][theme]
            icon = QIcon(icon_path)
            admin_item = QListWidgetItem(icon, " Admin")
            self.sidebar.addItem(admin_item)

    def refresh_current_page(self): # This method refreshes the current page
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, 'load_data'): # Check if the current widget has a load_data method
            current_widget.load_data() # Call the load_data method to refresh the data


    def handle_navigation(self, index): # This method handles the navigation between different pages
        item = self.sidebar.item(index) # Get the current item in the sidebar
        if not item: # If the item is None, return
            return

        text = item.text().strip() # Get the text of the current item

        if text == "Dashboard": # If the item is "Dashboard", set the current widget to the dashboard page
            self.stack.setCurrentWidget(self.dashboard_page)

        elif text == "Tenants": # If the item is "Tenants", set the current widget to the tenant page
            self.stack.setCurrentWidget(self.tenant_page)
            self.tenant_page.load_data() 

        elif text == "Properties": # If the item is "Properties", set the current widget to the property page
            self.stack.setCurrentWidget(self.property_page)
            self.property_page.load_data()

        elif text == "Landlords": # If the item is "Landlords", set the current widget to the landlord page
            self.stack.setCurrentWidget(self.landlord_page)
            self.landlord_page.load_data()

        elif text == "Tenancies": # If the item is "Tenancies", set the current widget to the tenancy page
            self.stack.setCurrentWidget(self.tenancy_page)
            self.tenancy_page.load_data()

        elif text == "Payments": # If the item is "Payments", set the current widget to the payment page
            self.stack.setCurrentWidget(self.payment_page)
            self.payment_page.load_data()

        elif text == "Maintenance": # If the item is "Maintenance", set the current widget to the maintenance page
            self.stack.setCurrentWidget(self.maintenance_page)
            self.maintenance_page.load_data()

        elif text == "Switch Theme": # If the item is "Switch Theme", toggle the theme
            self.main_app.toggle_theme()
            self.load_sidebar_items()

        elif text == "Logout": # If the item is "Logout", show a confirmation dialog
            reply = QMessageBox.question(self, "Logout", "Are you sure you want to logout?", QMessageBox.Yes | QMessageBox.No)
            self.close()

        elif text == "Admin" and self.user["is_admin"]: # If the item is "Admin" and the user is an admin, set the current widget to the admin page
            self.stack.setCurrentWidget(self.admin_page)



# ========================= #
# APPLICATION ENTRY POINT
# ========================= #

# This is the main entry point of the application
# It creates an instance of the STARPMKApp class and runs the application
if __name__ == "__main__":

    app = STARPMKApp()
    app.run()

    def clean_temp_files(): # This function cleans up temporary files when the application exits
        for path in TEMP_FILES_TO_CLEAN:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"[WARN] Failed to delete temp file: {e}")
# This is to ensure that any temporary files are removed when the application exits
    atexit.register(clean_temp_files)

