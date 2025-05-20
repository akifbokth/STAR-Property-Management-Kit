from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton
)
from PySide6.QtCore import Qt


# BaseDetailsPage is a base class for creating detail pages in a PyQt/PySide application.
# It provides a layout with a title, a form on the left side, and a section for images/documents on the right side.
# The form can be populated with various widgets, and the right section can be used for displaying images or documents.
# The class also provides methods for adding form rows, right sections, and binding/collecting data.
# This class is intended to be subclassed for specific detail pages.
# It is not meant to be instantiated directly.

class BaseDetailsPage(QDialog):# BaseDetailsPage class inherits from QDialog
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(1100)
        self.setMinimumHeight(600)

        # === Outer Layout === #
        self.main_layout = QVBoxLayout()
        self.split_layout = QHBoxLayout()

        # === Title === #
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("SectionTitle")
        self.main_layout.addWidget(title_label)

        # === Left Panel (Form) === #
        self.left_panel = QVBoxLayout()
        self.form_layout = QVBoxLayout()
        self.left_panel.addLayout(self.form_layout)

        # Save / Cancel buttons at bottom of left panel #
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        self.left_panel.addLayout(button_layout)

        # === Right Panel (Images, Documents, etc.) === #
        self.right_panel = QVBoxLayout()

        # Wrap both in QWidget containers for better layout stability #
        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_panel)

        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_panel)

        self.split_layout.addWidget(self.left_widget, 2)
        self.split_layout.addWidget(self.right_widget, 1)

        self.main_layout.addLayout(self.split_layout)
        self.setLayout(self.main_layout)

    def add_form_row(self, label: str, widget: QWidget): # This method adds a row to the form with a label and a widget.
        row_layout = QHBoxLayout()
        label_widget = QLabel(label)
        label_widget.setFixedWidth(130)
        row_layout.addWidget(label_widget)
        row_layout.addWidget(widget)
        self.form_layout.addLayout(row_layout)

    def add_right_section(self, widget: QWidget): # This method adds a widget to the right section of the layout.
        # This is useful for displaying images, documents, or any other content.
        self.right_panel.addWidget(widget)

    def bind_data(self, data: dict): # This method binds data to the form fields.
        # This is a placeholder method that should be implemented in subclasses.
        raise NotImplementedError

    def collect_data(self) -> dict: # This method collects data from the form fields and returns it as a dictionary.
        # This is a placeholder method that should be implemented in subclasses.
        raise NotImplementedError
