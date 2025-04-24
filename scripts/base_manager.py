from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton,
    QAbstractItemView, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt


class BaseManager(QWidget):
    def __init__(self, title, search_placeholder, columns, parent=None):
        super().__init__(parent)

        self.items_per_page = 10
        self.current_page = 0
        self.filtered_data = []

        # === Layouts ===
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        layout.addWidget(title_label)

        # === Search Bar ===
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(search_placeholder)
        self.search_input.textChanged.connect(self.apply_search_filter)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # === Action Buttons ===
        button_layout = QHBoxLayout()
        self.add_button = QPushButton('➕ Add')
        self.edit_button = QPushButton('✏️ Edit')
        self.delete_button = QPushButton('🗑️ Delete')

        # Tooltips
        self.add_button.setToolTip("Create a new entry")
        self.edit_button.setToolTip("Edit the selected item")
        self.delete_button.setToolTip("Delete the selected item")

        # Connections
        self.add_button.clicked.connect(lambda: self.open_details_dialog(None))
        self.edit_button.clicked.connect(self.handle_edit)
        self.delete_button.clicked.connect(self.handle_delete)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        # === Table Widget ===
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels(columns)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.itemDoubleClicked.connect(self.handle_double_click)
        self.table_widget.setStyleSheet("""
            QTableWidget::item:hover {
                background-color: #cce7ff;
            }
            QTableWidget::item:selected {
                background-color: #90caf9;
                color: black;
            }
        """)
        layout.addWidget(self.table_widget)

        # === Empty State Label ===
        self.empty_label = QLabel("No data found.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: #888;
            font-style: italic;
            font-size: 14px;
            padding: 60px;
        """)
        self.empty_label.setVisible(False)

        # Use a fixed-height placeholder to preserve layout structure
        self.empty_label.setMinimumHeight(200)
        layout.addWidget(self.empty_label)


        # === Pagination ===
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.pagination_label = QLabel("")

        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.next_button.clicked.connect(self.go_to_next_page)

        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.pagination_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.next_button)

        layout.addLayout(pagination_layout)
        self.setLayout(layout)

    def apply_search_filter(self):
        query = self.search_input.text().strip().lower()
        self.current_page = 0
        self.filtered_data = [
            item for item in self.get_data()
            if self.filter_item(item, query)
        ]
        self.refresh_table()

    def refresh_table(self):
        self.filtered_data = self.get_data()
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_data = self.filtered_data[start:end]

        self.table_widget.setRowCount(0)
        if not page_data:
            self.table_widget.setVisible(False)
            self.empty_label.setVisible(True)
        else:
            self.table_widget.setVisible(True)
            self.empty_label.setVisible(False)
            self.table_widget.setRowCount(len(page_data))
            for row, item in enumerate(page_data):
                for col, value in enumerate(self.extract_row_values(item)):
                    self.table_widget.setItem(row, col, QTableWidgetItem(str(value)))

            self.table_widget.resizeColumnsToContents()
            header = self.table_widget.horizontalHeader()
            header.setStretchLastSection(True)
            header.setSectionResizeMode(QHeaderView.Stretch)

        total_pages = max(1, (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page)
        self.pagination_label.setText(f"Page {self.current_page + 1} of {total_pages}")

        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def go_to_previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_table()

    def go_to_next_page(self):
        if (self.current_page + 1) * self.items_per_page < len(self.filtered_data):
            self.current_page += 1
            self.refresh_table()

    def handle_double_click(self):
        selected_row = self.table_widget.currentRow()
        if 0 <= selected_row < len(self.filtered_data):
            self.open_details_dialog(self.filtered_data[selected_row])

    def handle_edit(self):
        selected_row = self.table_widget.currentRow()
        if 0 <= selected_row < len(self.filtered_data):
            self.open_details_dialog(self.filtered_data[selected_row])

    def handle_delete(self):
        selected_row = self.table_widget.currentRow()
        if 0 <= selected_row < len(self.filtered_data):
            item = self.filtered_data[selected_row]
            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                "Are you sure you want to delete this item?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.delete_item(item)

    def get_data(self):
        raise NotImplementedError

    def extract_row_values(self, item):
        raise NotImplementedError

    def filter_item(self, item, query):
        raise NotImplementedError

    def open_details_dialog(self, item):
        raise NotImplementedError

    def delete_item(self, item):
        raise NotImplementedError

    def load_data(self):
        self.filtered_data = self.get_data()
        self.refresh_table()
