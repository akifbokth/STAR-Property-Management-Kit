from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton
)
from PySide6.QtCore import Qt


class BaseDetailsPage(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(1100)
        self.setMinimumHeight(600)

        # === Outer Layout ===
        self.main_layout = QVBoxLayout()
        self.split_layout = QHBoxLayout()

        # === Title ===
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("SectionTitle")
        self.main_layout.addWidget(title_label)

        # === Left Panel (Form) ===
        self.left_panel = QVBoxLayout()
        self.form_layout = QVBoxLayout()
        self.left_panel.addLayout(self.form_layout)

        # Save / Cancel buttons at bottom of left panel
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        self.left_panel.addLayout(button_layout)

        # === Right Panel (Images, Documents, etc.) ===
        self.right_panel = QVBoxLayout()

        # Wrap both in QWidget containers for better layout stability
        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_panel)

        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_panel)

        self.split_layout.addWidget(self.left_widget, 2)
        self.split_layout.addWidget(self.right_widget, 1)

        self.main_layout.addLayout(self.split_layout)
        self.setLayout(self.main_layout)

    def add_form_row(self, label: str, widget: QWidget):
        row_layout = QHBoxLayout()
        label_widget = QLabel(label)
        label_widget.setFixedWidth(130)
        row_layout.addWidget(label_widget)
        row_layout.addWidget(widget)
        self.form_layout.addLayout(row_layout)

    def add_right_section(self, widget: QWidget):
        self.right_panel.addWidget(widget)

    def bind_data(self, data: dict):
        raise NotImplementedError

    def collect_data(self) -> dict:
        raise NotImplementedError
