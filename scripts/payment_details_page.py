import os
from PySide6.QtWidgets import QLabel, QLineEdit, QComboBox, QPushButton, QDateEdit, QMessageBox
from PySide6.QtCore import QDate, Signal
from scripts.base_details_page import BaseDetailsPage
from scripts.database_manager import DatabaseManager
from scripts.tenant_picker_dialog import TenantPickerDialog
from scripts.tenancy_picker_dialog import TenancyPickerDialog


# PaymentDetailsPage class to create a dialog for managing payment details
# This class inherits from BaseDetailsPage and provides a form for entering payment information
# It also allows for the selection of a tenant and tenancy associated with the payment.
# The payments are stored in a SQLite database and can be updated or created.

class PaymentDetailsPage(BaseDetailsPage): # This class inherits from BaseDetailsPage to create a custom dialog
    payment_updated = Signal() # Signal emitted when payment details are updated

    def __init__(self, payment_id=None, parent=None):
        super().__init__("Payment Details", parent)
        self.db = DatabaseManager() # Database manager instance
        self.payment_id = payment_id # Get payment ID if provided
        self.is_add_mode = payment_id is None # Check if in add mode or edit mode
        self.tenant_id = None # Tenant ID to be set when a tenant is selected
        self.tenancy_id = None # Tenancy ID to be set when a tenancy is selected

        # Tenant and tenancy selection
        self.tenant_btn = QPushButton("Select Tenant")
        self.tenant_label = QLabel("No tenant selected")
        self.tenant_btn.clicked.connect(self.select_tenant)

        self.tenancy_btn = QPushButton("Select Tenancy")
        # disable tenancy picker until tenant chosen
        self.tenancy_btn.setEnabled(False)
        self.tenancy_label = QLabel("No tenancy selected")
        self.tenancy_btn.clicked.connect(self.select_tenancy)

        # Payment form inputs
        self.payment_date = QDateEdit()
        self.payment_date.setToolTip("Select payment date")
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())

        self.due_date = QDateEdit()
        self.due_date.setToolTip("Select due date")
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate())

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 1000.00")
        self.amount_input.setToolTip("Enter payment amount")

        self.method_input = QComboBox()
        self.method_input.setToolTip("Select payment method")
        self.method_input.addItems(["Cash", "Bank Transfer", "Card", "Cheque"])

        self.status_input = QComboBox()
        self.status_input.setToolTip("Select payment status")
        self.status_input.addItems(["Paid", "Unpaid"])

        self.type_input = QComboBox()
        self.type_input.setToolTip("Select payment type")
        self.type_input.addItems(["Rent", "Deposit", "Other"])

        self.notes_input = QLineEdit()

        # Left form panel
        self.add_form_row("Payment Date", self.payment_date)
        self.add_form_row("Due Date", self.due_date)
        self.add_form_row("Amount", self.amount_input)
        self.add_form_row("Method", self.method_input)
        self.add_form_row("Status", self.status_input)
        self.add_form_row("Type", self.type_input)
        self.add_form_row("Notes", self.notes_input)

        # Right panel for tenant & tenancy
        self.right_panel.addWidget(QLabel("<b>Tenant</b>"))
        self.right_panel.addWidget(self.tenant_btn)
        self.right_panel.addWidget(self.tenant_label)

        self.right_panel.addSpacing(15)

        self.right_panel.addWidget(QLabel("<b>Tenancy</b>"))
        self.right_panel.addWidget(self.tenancy_btn)
        self.right_panel.addWidget(self.tenancy_label)

        if not self.is_add_mode:
            self.load_data()

    def select_tenant(self): # Open the tenant picker dialog to select a tenant
        dialog = TenantPickerDialog(mode="single") # Open the tenant picker dialog in single selection mode 
                                                   # (only one tenant can be selected)
        dialog.tenant_selected.connect(self.set_selected_tenant) # Connect the signal to set the selected tenant
        dialog.exec()

    def set_selected_tenant(self, tenant): # Set the selected tenant and enable the tenancy button
        self.tenant_id = tenant["tenant_id"] # Get the tenant ID from the selected tenant
        self.tenant_label.setText(tenant["name"]) # Set the tenant label to the selected tenant's name

        self.tenancy_btn.setEnabled(True)  # Enable the tenancy button after selecting a tenant

    def select_tenancy(self): # Open the tenancy picker dialog to select a tenancy
        # Pass the current tenant_id so the dialog only shows matching tenancies
        dialog = TenancyPickerDialog(self, tenant_id=self.tenant_id) # Open the tenancy picker dialog
        if dialog.exec(): # If the dialog is accepted
            self.tenancy_id, label = dialog.get_selection() # Get the selected tenancy ID and label
            self.tenancy_label.setText(label) # Set the tenancy label to the selected tenancy's label

    def bind_data(self, row): # Bind the provided data to the form inputs
        self.tenant_id = row["tenant_id"]
        self.tenancy_id = row["tenancy_id"]
        self.payment_date.setDate(QDate.fromString(row["payment_date"], "yyyy-MM-dd"))
        self.due_date.setDate(QDate.fromString(row["due_date"] or row["payment_date"], "yyyy-MM-dd"))
        self.amount_input.setText(str(row["amount"]))
        self.method_input.setCurrentText(row["method"])
        self.status_input.setCurrentText(row["status"])
        self.type_input.setCurrentText(row["payment_type"])
        self.notes_input.setText(row["notes"] or "")

        tenant_name = self.db.execute( # Fetch the tenant's name from the database
            "SELECT first_name || ' ' || last_name FROM tenants WHERE tenant_id = ?",
            (self.tenant_id,), fetchone=True
        )
        self.tenant_label.setText(tenant_name[0] if tenant_name else "") # Set the tenant label to the tenant's name

        tenancy_label = self.db.execute( # Fetch the tenancy label from the database
            "SELECT start_date || ' → ' || end_date FROM tenancies WHERE tenancy_id = ?",
            (self.tenancy_id,), fetchone=True
        )
        self.tenancy_label.setText(tenancy_label[0] if tenancy_label else "") # Set the tenancy label to the tenancy's label

    def load_data(self): # Load data from the database for the given payment ID
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM payments WHERE payment_id = ?", (self.payment_id,))
            row = cur.fetchone()
            if row: # If a row is found, bind the data to the form inputs
                col_names = [desc[0] for desc in cur.description]
                self.bind_data(dict(zip(col_names, row)))

    def collect_data(self): # Collect data from the form inputs and validate them
        if not self.tenant_id or not self.tenancy_id: # Check if a tenant and tenancy are selected
            QMessageBox.warning(self, "Missing Info", "Please select both tenant and tenancy.")
            return None

        return {
            "tenancy_id": self.tenancy_id,
            "tenant_id": self.tenant_id,
            "payment_date": self.payment_date.date().toString("yyyy-MM-dd"),
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
            "amount": self.amount_input.text(),
            "method": self.method_input.currentText(),
            "status": self.status_input.currentText(),
            "payment_type": self.type_input.currentText(),
            "notes": self.notes_input.text()
        }

    def accept(self): # Override the accept method to handle form submission
        data = self.collect_data()
        if not data:
            return

        if self.is_add_mode: # If in add mode, insert a new payment record
            query = """
                INSERT INTO payments (
                    tenancy_id, tenant_id, payment_date, due_date, amount,
                    method, status, payment_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = ( # Parameters for the SQL query
                data["tenancy_id"], data["tenant_id"], data["payment_date"], data["due_date"],
                data["amount"], data["method"], data["status"], data["payment_type"],
                data["notes"]
            )

        else: # If in edit mode, update the existing payment record
            query = """
                UPDATE payments SET
                    tenancy_id = ?, tenant_id = ?, payment_date = ?, due_date = ?, amount = ?,
                    method = ?, status = ?, payment_type = ?, notes = ?
                WHERE payment_id = ?
            """
            params = ( # Parameters for the SQL query
                data["tenancy_id"], data["tenant_id"], data["payment_date"], data["due_date"],
                data["amount"], data["method"], data["status"], data["payment_type"],
                data["notes"], self.payment_id
            )

        self.db.execute(query, params) # Execute the SQL query with the parameters
        self.payment_updated.emit() # Emit the signal to notify that payment details have been updated
        super().accept()

