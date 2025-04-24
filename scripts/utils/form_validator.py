from PySide6.QtWidgets import QMessageBox
import re

class FormValidator:
    def __init__(self, parent=None):
        self.rules = []
        self.parent = parent  # QWidget, used for QMessageBox if needed

    def require(self, field_widget, name="This field"):
        self.rules.append((field_widget, lambda w: bool(w.text().strip()), f"{name} is required."))
        return self

    def is_email(self, field_widget, name="Email"):
        pattern = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
        self.rules.append((field_widget, lambda w: bool(pattern.match(w.text().strip())), f"{name} must be a valid email address."))
        return self

    def is_numeric(self, field_widget, name="Number"):
        self.rules.append((field_widget, lambda w: w.text().strip().isdigit(), f"{name} must be numeric."))
        return self

    def custom(self, field_widget, validator_fn, error_message):
        self.rules.append((field_widget, validator_fn, error_message))
        return self

    def validate(self, show_message=True):
        for widget, check_fn, error in self.rules:
            if not check_fn(widget):
                if show_message:
                    QMessageBox.warning(self.parent, "Validation Error", error)
                    widget.setFocus()
                return False
        return True
