import os
from PySide6.QtWidgets import (
    QLineEdit, QComboBox, QTextEdit, QDateEdit,
    QGroupBox, QVBoxLayout, QLabel, QPushButton, QListWidget,
    QMessageBox, QHBoxLayout, QDialog
)
from PySide6.QtGui import QDoubleValidator, QPixmap
from PySide6.QtCore import QDate, Qt
from scripts.base_details_page import BaseDetailsPage
from scripts.document_manager import DocumentManager
from scripts.image_picker_dialog import ImagePickerDialog
from scripts.utils.form_validator import FormValidator
from scripts.document_picker_dialog import DocumentPickerDialog
from scripts.utils.file_utils import cleanup_temp_preview_folder
from scripts.utils.image_preview import TempImagePreview


class PropertyDetailsPage(BaseDetailsPage):
    def __init__(self, property_data=None, parent=None):
        super().__init__("Property Details", parent)
        self.property_data = property_data or {}
        self.doc_manager = DocumentManager()
        self.image_paths = []
        self.current_image_index = 0

        # === FORM INPUTS (LEFT PANEL) ===
        self.door_input = QLineEdit()
        self.street_input = QLineEdit()
        self.postcode_input = QLineEdit()
        self.area_input = QLineEdit()
        self.city_input = QLineEdit()
        self.bedrooms_input = QComboBox()
        self.property_type_input = QComboBox()
        self.price_input = QLineEdit()
        self.availability_date_input = QDateEdit()
        self.status_input = QComboBox()
        self.notes_input = QTextEdit()

        self.door_input.setPlaceholderText("e.g. 12A or Flat 1 Crown House")
        self.street_input.setPlaceholderText("e.g. 123 High Street")
        self.postcode_input.setPlaceholderText("e.g. AB12 3CD")
        self.area_input.setPlaceholderText("e.g. Camden")
        self.city_input.setPlaceholderText("e.g. London")
        self.price_input.setPlaceholderText("e.g. 1200.00")

        self.bedrooms_input.addItems([str(i) for i in range(1, 11)])
        self.property_type_input.addItems([
            "Flat (Purpose-built)", "Flat (Converted)", "Studio", "House (Detached)",
            "House (Semi-detached)", "House (Terraced)", "House (End-of-terrace)",
            "Bungalow", "Maisonette", "Cottage", "Villa", "Penthouse", "Mansion"
        ])
        self.status_input.addItems(["Available", "Tenanted", "Unavailable"])
        self.availability_date_input.setCalendarPopup(True)
        self.availability_date_input.setDate(QDate.currentDate())
        self.price_input.setValidator(QDoubleValidator(0, 9999999, 2))

        self.add_form_row("Door Number:", self.door_input)
        self.add_form_row("Street:", self.street_input)
        self.add_form_row("Postcode:", self.postcode_input)
        self.add_form_row("Area:", self.area_input)
        self.add_form_row("City:", self.city_input)
        self.add_form_row("Bedrooms:", self.bedrooms_input)
        self.add_form_row("Property Type:", self.property_type_input)
        self.add_form_row("Price (£):", self.price_input)
        self.add_form_row("Available From:", self.availability_date_input)
        self.add_form_row("Status:", self.status_input)
        self.add_form_row("Notes:", self.notes_input)

        # === IMAGE SECTION ===
        image_group = QGroupBox("Property Images")
        image_layout = QVBoxLayout()
        self.image_label = QLabel("No images")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(200)
        image_layout.addWidget(self.image_label)

        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("⟨")
        self.next_button = QPushButton("⟩")
        self.prev_button.clicked.connect(self.show_prev_image)
        self.next_button.clicked.connect(self.show_next_image)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        image_layout.addLayout(nav_layout)

        manage_button = QPushButton("Manage Images")
        manage_button.clicked.connect(self.open_image_picker)
        image_layout.addWidget(manage_button)

        image_group.setLayout(image_layout)
        self.add_right_section(image_group)

        # === DOCUMENT SECTION ===
        doc_group = QGroupBox("Documents")
        doc_layout = QVBoxLayout()
        self.documents_list = QListWidget()
        self.documents_list.itemDoubleClicked.connect(self.preview_document)
        doc_layout.addWidget(self.documents_list)

        upload_button = QPushButton("Upload Document")
        upload_button.clicked.connect(self.add_document)
        delete_button = QPushButton("Delete Document")
        delete_button.clicked.connect(self.delete_document)

        doc_btn_layout = QHBoxLayout()
        doc_btn_layout.addWidget(upload_button)
        doc_btn_layout.addWidget(delete_button)
        doc_layout.addLayout(doc_btn_layout)

        doc_group.setLayout(doc_layout)
        self.add_right_section(doc_group)

        if self.property_data:
            self.bind_data(self.property_data)
            self.load_property_images()
            self.load_documents()

    def bind_data(self, data: dict):
        self.door_input.setText(data.get("door_number", ""))
        self.street_input.setText(data.get("street", ""))
        self.postcode_input.setText(data.get("postcode", ""))
        self.area_input.setText(data.get("area", ""))
        self.city_input.setText(data.get("city", ""))
        self.bedrooms_input.setCurrentText(str(data.get("bedrooms", "1")))
        self.property_type_input.setCurrentText(data.get("property_type", "Flat (Purpose-built)"))
        self.price_input.setText(str(data.get("price", "")))
        self.status_input.setCurrentText(data.get("status", "Available"))
        self.notes_input.setPlainText(data.get("notes", ""))
        if data.get("availability_date"):
            try:
                self.availability_date_input.setDate(QDate.fromString(data["availability_date"], "yyyy-MM-dd"))
            except Exception:
                pass

    def collect_data(self) -> dict:
        validator = FormValidator(self)
        validator.require(self.door_input, "Door Number") \
                 .require(self.street_input, "Street") \
                 .require(self.postcode_input, "Postcode") \
                 .require(self.price_input, "Price")

        if not validator.validate():
            return None

        try:
            price = float(self.price_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Price must be a number.")
            return None

        return {
            "door_number": self.door_input.text().strip(),
            "street": self.street_input.text().strip(),
            "postcode": self.postcode_input.text().strip(),
            "area": self.area_input.text().strip(),
            "city": self.city_input.text().strip(),
            "bedrooms": int(self.bedrooms_input.currentText()),
            "property_type": self.property_type_input.currentText(),
            "price": price,
            "availability_date": self.availability_date_input.date().toString("yyyy-MM-dd"),
            "status": self.status_input.currentText(),
            "notes": self.notes_input.toPlainText().strip()
        }

    def load_property_images(self):
        prop_id = self.property_data.get("id")
        if not prop_id:
            return

        folder_name = self.doc_manager.get_folder_name("property", prop_id)
        folder = os.path.join("properties", folder_name, "property_images")

        if os.path.exists(folder):
            self.image_paths = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            self.current_image_index = 0
            self.update_image_display()
        else:
            print(f"[DEBUG] Image folder does not exist: {folder}")

    def update_image_display(self):
        if self.image_paths:
            path = self.image_paths[self.current_image_index]
            self.image_label.setPixmap(QPixmap(path).scaledToHeight(180, Qt.SmoothTransformation))
        else:
            self.image_label.setText("No images")

    def show_prev_image(self):
        if self.image_paths:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_paths)
            self.update_image_display()

    def show_next_image(self):
        if self.image_paths:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
            self.update_image_display()

    def open_image_picker(self):
        dialog = ImagePickerDialog(
            self.property_data.get("id"),
            self.door_input.text(),
            self.street_input.text(),
            self.postcode_input.text()
        )
        dialog.exec()
        self.load_property_images()

    def load_documents(self):
        if not self.property_data.get("id"):
            return
        self.documents_list.clear()
        property_id = self.property_data["id"]
        self.documents = self.doc_manager.get_documents("property", property_id)
        for doc in self.documents:
            self.documents_list.addItem(f"{doc['name']} ({doc['type']})")

    def add_document(self):
        if not self.property_data.get("id"):
            QMessageBox.warning(
                self,
                "Save Required",
                "Please save the property before uploading documents."
            )
            return
        
        dialog = DocumentPickerDialog("property", self.property_data["id"])
        if dialog.exec():
            self.load_documents()

    def delete_document(self):

        selected_item = self.documents_list.currentItem()

        if not self.property_data.get("id"):
            QMessageBox.warning(
                self,
                "Save Required",
                "Cannot delete documents before property is saved."
            )
            return

        if not selected_item:
            QMessageBox.information(self, "No Selection", "Please select a document to delete.")
            return
        
        name_part = selected_item.text().split(" (")[0]
        match = next((doc for doc in self.documents if doc["name"] == name_part), None)
        if not match:
            return
        confirm = QMessageBox.question(self, "Delete?", f"Delete document '{match['name']}'?")
        if confirm == QMessageBox.Yes:
            self.doc_manager.delete_document("property", self.property_data["id"], match["filename"])
            self.load_documents()

    def preview_document(self):
        # Clean up any existing temp files before previewing a new one
        cleanup_temp_preview_folder()

        if not self.property_data.get("id"):
            return
        item = self.documents_list.currentItem()
        if not item:
            return
        name_part = item.text().split(" (")[0]
        match = next((doc for doc in self.documents if doc["name"] == name_part), None)
        if not match:
            return
        path = self.doc_manager.decrypt_document_to_temp("property", self.property_data["id"], match["filename"])
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Missing File", "The selected document could not be found.")
            return
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            self.preview_image(path)
        elif path.lower().endswith(".pdf"):
            import webbrowser
            webbrowser.open(path)

    def preview_image(self, path):
        dialog = TempImagePreview(path, self)
        dialog.exec()

    def accept(self):
        data = self.collect_data()
        if not data:
            return

        if self.property_id:
            self.db.execute(
                """
                UPDATE properties
                SET door_number = ?, street = ?, postcode = ?, area = ?, city = ?, bedrooms = ?,
                    property_type = ?, price = ?, availability_date = ?, landlord_id = ?, status = ?, notes = ?
                WHERE property_id = ?
                """,
                (
                    data["door_number"], data["street"], data["postcode"], data["area"], data["city"],
                    data["bedrooms"], data["property_type"], data["price"], data["availability_date"],
                    data["landlord_id"], data["status"], data["notes"], self.property_id
                )
            )
        else:
            self.db.execute(
                """
                INSERT INTO properties (
                    door_number, street, postcode, area, city, bedrooms,
                    property_type, price, availability_date, landlord_id, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["door_number"], data["street"], data["postcode"], data["area"], data["city"],
                    data["bedrooms"], data["property_type"], data["price"], data["availability_date"],
                    data["landlord_id"], data["status"], data["notes"]
                )
            )
        super().accept()

