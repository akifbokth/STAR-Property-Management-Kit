import os

# === Base Path ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === Core File Paths ===
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "starpmk_database.db")
ENCRYPTION_KEY_PATH = os.path.join(DB_DIR, "key.key")

# === Entity Storage Paths ===
STORAGE_PATHS = {
    "tenant": os.path.join(BASE_DIR, "tenants"),
    "property": os.path.join(BASE_DIR, "properties"),
    "landlord": os.path.join(BASE_DIR, "landlords"),
    "tenancy": os.path.join(BASE_DIR, "tenancies"),
}

# === Document Types ===
DOCUMENT_TYPES = {
    "tenant": ["ID", "Proof of Address", "Contract", "Other"],
    "landlord": ["ID", "Proof of Ownership", "Agreement", "Other"],
    "property": ["EPC", "Gas Safety", "Electrical Cert", "Inventory", "HMO Licence", "Other"],
    "tenancy": ["Tenancy Agreement", "Deposit Info", "Inspection Report", "Other"]
}

# === Temporary Preview Folder ===
TEMP_PREVIEW_DIR = os.path.join(BASE_DIR, "temp_preview")

# === Security Settings ===
MAX_FILE_SIZE_MB = 150  # Max upload size (in megabytes)

# === UI Settings ===
APP_NAME = "Star Property Management Kit"
ICON_PATH = os.path.join(BASE_DIR, "assets", "app_icon.png")

# === Optional Debugging Flags ===
ENABLE_LOGGING = True
DEBUG_MODE = True
