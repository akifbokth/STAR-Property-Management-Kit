# STAR Property Management Kit

A desktop application for small to mid-sized property management teams, built with Python, PySide6, and SQLite. STAR PMK streamlines landlord, tenant, property, tenancy, payment, maintenance, and secure document workflows into a single, easy‑to‑use interface.

---

## Features

* **Landlord, Tenant, Property, Tenancy, Payment, Maintenance Management**
* **Secure Document Encryption**: AES‑encrypted storage of sensitive documents, on‑demand decryption for preview
* **Image Handling**: Upload, preview, and manage property images with an integrated carousel
* **Database Backup & Cleanup**: One‑click backup of the SQLite database and temp‑preview folder cleanup
* **Role‑Based Access**: Admin privileges included
* **Installer & Uninstaller**: Windows NSIS installer with desktop/start‑menu shortcuts and full uninstall support
* **Theming**: Dark and light modes via QSS stylesheets stored in `styles/`

---

## Prerequisites

* Windows 10 or later (for NSIS installer)
* Python 3.10+ (for development)
* [PySide6](https://pypi.org/project/PySide6/)
* SQLite3 (bundled)
* PyInstaller (for packaging)

---

## Installation (IMPORTANT)

### 1. Download the GitHub repo as a ZIP file

Click the green Code dropdown button (top right). Then select Download ZIP.

### 2. Build executables with PyInstaller (use VS Code)

#### If you don't see "Initialise Database.exe" in the folder:
```powershell
# Build init_database.exe
pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --console `
  --name init_database `
  --add-data "resources;resources" `
  init_database.py
```
#### If you don't see "main.exe" or "STAR PMK.exe" in the folder:
```powershell
# Build main.exe
pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name main `
  --icon assets\starpmk.ico `
  --add-data "resources;resources" `
  --add-data "styles;styles" `
  --add-data "assets;assets" `
  --add-data "scripts;scripts" `
  main.py
```

### 3. Build the folders and run the program

Find the `main.exe` / `STAR PMK.exe` and `init_database.exe` / `Initialise Database.exe` file in the dist\ folder.

Copy/Move them both into the root directory (where main.py and config.py are situated)

Run `init_database.exe` / `Initialise Database.exe` first to initialise the database and get the folders ready.

Then you can run `main.exe` / `STAR PMK.exe` for the actual program.

---

### Installation Wizard

If you would like a simpler installation wizard, please email me at mbokt001@gold.ac.uk and I can send you the STAR PMK Installer file (Windows only)

I cannot upload the file here as the file is too big for Github to accept.

---

## Usage

0. **Check resources\database** and make sure you have "key.key" and "starpmk_database.db", if they are not there then make sure to rerun "Initialise Database.exe"
1. **Run** `STAR PMK.exe` (or desktop shortcut).
2. **Login** with default credentials:

   * Username: `admin`
   * Password: `12345`
3. **Enjoy the program!**

---

## Configuration

* **`config.py`** holds paths (e.g., `RESOURCES_DIR`, `BACKUPS_DIR`, `ICON_PATH`) and helper `resource_path()` for PyInstaller compatibility.
* **`styles/`** contains QSS files for theming.

---

## Development

* **Project structure**:

  ```
  ├─ assets/        # Icons, logo, media
  ├─ resources/     # Database, default subfolders (landlords, properties, ...)
  ├─ scripts/       # Application code: managers, dialogs, utils
  ├─ styles/        # QSS stylesheets
  ├─ main.py        # Application entrypoint
  ├─ init_database.py # Database initialization script
  └─ config.py      # Path and constant definitions
  ```

* **Testing**: Manual black-box tests; consider adding pytest suites.

---
