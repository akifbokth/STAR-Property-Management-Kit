from PySide6.QtWidgets import QMessageBox
import re

# FormValidator is a utility class to validate form fields in PyQt/PySide applications.
# It provides methods to check if fields are required, if they contain valid email addresses,
# if they are numeric, and allows for custom validation functions.
# It can also show error messages using QMessageBox.

class FormValidator:
    def __init__(self, parent=None):
        self.rules = [] # List of validation rules
        # Each rule is a tuple (field_widget, check_function, error_message)
        self.parent = parent  # QWidget, used for QMessageBox if needed

    def require(self, field_widget, name="This field"): # This field is required
        self.rules.append((field_widget, lambda w: bool(w.text().strip()), f"{name} is required."))
        return self

    def is_email(self, field_widget, name="Email"): # This field must be a valid email address
        pattern = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
        self.rules.append((field_widget, lambda w: bool(pattern.match(w.text().strip())), f"{name} must be a valid email address."))
        return self

    def is_numeric(self, field_widget, name="Number"): # This field must be numeric
        self.rules.append((field_widget, lambda w: w.text().strip().isdigit(), f"{name} must be numeric."))
        return self

    def custom(self, field_widget, validator_fn, error_message): # Custom validation function
        # validator_fn should return True if valid, False otherwise
        self.rules.append((field_widget, validator_fn, error_message)) # Add custom validation rule
        return self

    def validate(self, show_message=True): # Validate all rules
        # If show_message is True, show a message box for the first invalid field
        for widget, check_fn, error in self.rules:
            if not check_fn(widget):
                if show_message:
                    QMessageBox.warning(self.parent, "Validation Error", error) # Show error message
                    widget.setFocus() # Set focus to the invalid field
                return False
        return True
