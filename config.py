import os
import sys

# === Resource path helper === #
def resource_path(rel_path: str) -> str:
    """
    Get the absolute path to a resource, whether running from source or as a PyInstaller bundle.
    """
    if getattr(sys, 'frozen', False):
        # Running as a bundled exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, rel_path)

# === Resource directories === #
RESOURCES_DIR      = resource_path("resources")
DB_DIR             = os.path.join(RESOURCES_DIR, "database")
BACKUPS_DIR        = os.path.join(RESOURCES_DIR, "backups")
TEMP_PREVIEW_DIR   = os.path.join(RESOURCES_DIR, "temp_preview")
LANDLORDS_DIR      = os.path.join(RESOURCES_DIR, "landlords")
PROPERTIES_DIR     = os.path.join(RESOURCES_DIR, "properties")
TENANTS_DIR        = os.path.join(RESOURCES_DIR, "tenants")
TENANCIES_DIR      = os.path.join(RESOURCES_DIR, "tenancies")

# === Core file paths === #
DB_PATH            = os.path.join(DB_DIR, "starpmk_database.db")
ENCRYPTION_KEY_PATH= os.path.join(DB_DIR, "key.key")
BACKUP_PATH        = os.path.join(BACKUPS_DIR, "starpmk_database_backup.db")


# === Storage paths mapping for document_manager === #
STORAGE_PATHS = {
    'landlord':  LANDLORDS_DIR,
    'property':  PROPERTIES_DIR,
    'tenant':    TENANTS_DIR,
    'tenancy':   TENANCIES_DIR,
}

# === Document Types === #
DOCUMENT_TYPES = {
    "tenant": ["ID", "Proof of Address", "Contract", "Other"],
    "landlord": ["ID", "Proof of Ownership", "Agreement", "Other"],
    "property": ["EPC", "Gas Safety", "Electrical Cert", "Inventory", "HMO Licence", "Other"],
    "tenancy": ["Tenancy Agreement", "Deposit Info", "Inspection Report", "Other"]
}

# === Security Settings === #
MAX_FILE_SIZE_MB = 150  # Max upload size (in megabytes)

# === UI Settings === #
APP_NAME = "STAR Property Management Kit"
ICON_PATH = resource_path("starpmk.ico")

# === Styles === #
STYLES_DIR = resource_path("styles")

# === Optional Debugging Flags === #
ENABLE_LOGGING = True
DEBUG_MODE = True
