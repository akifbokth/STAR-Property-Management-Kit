# STAR Property Management Kit

A desktop application for small to mid-sized property management teams, built with Python, PySide6, and SQLite. STAR PMK streamlines landlord, tenant, property, tenancy, payment, maintenance, and secure document workflows into a single, easy‑to‑use interface.

---

## Features

* **Landlord, Tenant, Property, Tenancy, Payment, Maintenance Management**
* **Secure Document Encryption**: AES‑encrypted storage of sensitive documents, on‑demand decryption for preview
* **Image Handling**: Upload, preview, and manage property images with an integrated carousel
* **Database Backup & Cleanup**: One‑click backup of the SQLite database and temp‑preview folder cleanup
* **Role‑Based Access**: Admin privileges with protection against demoting the last administrator
* **Installer & Uninstaller**: Windows NSIS installer with desktop/start‑menu shortcuts and full uninstall support
* **Theming**: Dark and light modes via QSS stylesheets stored in `styles/`

---

## Prerequisites

* Windows 10 or later (for NSIS installer)
* Python 3.10+ (for development)
* [PySide6](https://pypi.org/project/PySide6/)
* SQLite3 (bundled)
* NSIS (for building the installer)
* PyInstaller (for packaging)

---

## Installation (IMPORTANT)

### 1. Clone the repository

```bash
git clone https://github.com/YourOrg/STAR-PMK.git
cd STAR-PMK
```

### 2. Initialize the database (development)

```bash
python init_database.py
```

### 3. Run in development mode

```bash
python main.py
```

### 4. Build executables with PyInstaller

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

### 5. Build the folders and run the program

Find the main.exe and init_database.exe file in the dist\ folder.

Run init_database.exe first to initialise the database and get the folders ready.

Then you can run main.exe for the actual program.

### 6. Installation Wizard
---

## Usage

1. **Run** `STAR PMK.exe` (or desktop shortcut).
2. **Login** with default credentials:

   * Username: `admin`
   * Password: `12345`
3. Enjoy the program!

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
