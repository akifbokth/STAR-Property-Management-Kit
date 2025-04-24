from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QGridLayout, QListWidget, QPushButton, QSizePolicy
from PySide6.QtCore import Qt
from scripts.maintenance_manager import MaintenanceManager
from scripts.database_manager import DatabaseManager
from scripts.property_details_page import PropertyDetailsPage
from scripts.tenant_details_page import TenantDetailsPage
from scripts.payment_details_page import PaymentDetailsPage
from scripts.maintenance_details_page import MaintenanceDetailsPage
from scripts.tenancy_manager import TenancyManager
from scripts.property_manager import PropertyManager
from scripts.tenant_manager import TenantManager

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("DashboardPage")
        self.db = DatabaseManager()
        self.setup_ui()

    def apply_stylesheet(self, mode="light"):
        path = "styles_light.qss" if mode == "light" else "styles_dark.qss"
        try:
            with open(path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Stylesheet not found: {path}")

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Main dashboard content
        content_layout = QVBoxLayout()
        main_layout.addLayout(content_layout, 3)

        dashboard_title_container = QWidget()
        dashboard_title_container.setObjectName("dashboard_title")
        dashboard_title_layout = QVBoxLayout(dashboard_title_container)
        dashboard_title_label = QLabel("Dashboard Overview")
        dashboard_title_label.setObjectName("SectionTitle")
        dashboard_title_layout.addWidget(dashboard_title_label)
        content_layout.addWidget(dashboard_title_container)

        stats_frame = QFrame()
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(20)
        stats_layout.setContentsMargins(20, 10, 20, 10)
        stats_layout.setAlignment(Qt.AlignCenter)

        self.cards = {
            "Total Properties": QLabel("0"),
            "Total Tenants": QLabel("0"),
            "Rent Due (30d)": QLabel("0"),
            "Outstanding Maintenance": QLabel("0"),
            "Vacant Properties": QLabel("0"),
            "Tenancies Ending Soon (30d)": QLabel("0"),
        }

        for i, (label, count_label) in enumerate(self.cards.items()):
            card = self.create_stat_card(label, count_label)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            stats_layout.addWidget(card, i // 3, i % 3)

        content_layout.addWidget(stats_frame)

        alert_title_container = QWidget()
        alert_title_container.setObjectName("alert_title")
        alert_title_layout = QVBoxLayout(alert_title_container)
        alert_title_label = QLabel("⚠️ Alerts & Reminders")
        alert_title_label.setObjectName("SectionTitle")
        alert_title_layout.addWidget(alert_title_label)
        content_layout.addWidget(alert_title_container)

        self.alerts_layout = QVBoxLayout()
        alert_frame = QFrame()
        alert_frame.setLayout(self.alerts_layout)
        alert_frame.setObjectName("AlertFrame")
        content_layout.addWidget(alert_frame)

        insight_title_container = QWidget()
        insight_title_container.setObjectName("insight_title")
        insight_title_layout = QVBoxLayout(insight_title_container)
        insight_title_label = QLabel("📈 Tenancy Insights")
        insight_title_label.setObjectName("SectionTitle")
        insight_title_layout.addWidget(insight_title_label)
        content_layout.addWidget(insight_title_container)

        self.insights_layout = QVBoxLayout()
        insight_frame = QFrame()
        insight_frame.setLayout(self.insights_layout)
        insight_frame.setObjectName("InsightFrame")
        content_layout.addWidget(insight_frame)

        sidebar_layout = QVBoxLayout()

        self.activity_feed = QListWidget()
        self.activity_feed.setObjectName("ActivityFeed")
        sidebar_layout.addWidget(self.activity_feed)

        quick_actions_title_container = QWidget()
        quick_actions_title_container.setObjectName("quick_actions_title")
        quick_actions_title_layout = QVBoxLayout(quick_actions_title_container)
        quick_actions_title_label = QLabel("⚡ Quick Actions")
        quick_actions_title_label.setObjectName("SectionTitle")
        quick_actions_title_layout.addWidget(quick_actions_title_label)
        sidebar_layout.addWidget(quick_actions_title_container)

        self.quick_actions_panel = QVBoxLayout()

        buttons = [
            ("+ Add Property", self.add_property),
            ("+ New Tenant", self.add_tenant),
            ("+ Record Payment", self.record_payment),
            ("+ Report Maintenance", self.report_maintenance)
        ]

        for text, slot in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            self.quick_actions_panel.addWidget(btn)

        sidebar_layout.addLayout(self.quick_actions_panel)

        sidebar_container = QFrame()
        sidebar_container.setObjectName("SidebarContainer")
        sidebar_container.setLayout(sidebar_layout)
        sidebar_container.setFixedWidth(300)
        main_layout.addWidget(sidebar_container, 1)

        self.load_data()
        self.load_alerts()
        self.load_insights()
        self.load_activity_feed()

    def create_stat_card(self, label_text, count_label):
        button = QPushButton()
        button.setObjectName("StatCard")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        count_label.setAlignment(Qt.AlignCenter)
        count_label.setObjectName("StatCount")

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("StatLabel")

        layout.addWidget(count_label)
        layout.addWidget(label)
        button.setLayout(layout)

        button.clicked.connect(lambda _, text=label_text: self.navigate_to(text))
        return button

    def navigate_to(self, label):
        if label == "Total Properties":
            self.pm_window = PropertyManager()
            self.pm_window.show()
            self.pm_window.setWindowTitle("Property Manager")
            self.pm_window.setWindowModality(Qt.ApplicationModal) # Ensure the window is modal 
            self.pm_window.raise_() # Bring the window to the front
            self.pm_window.resize(900, 600) # Resize the window

        elif label == "Total Tenants":
            self.tm_window = TenantManager()
            self.tm_window.show()
            self.tm_window.setWindowTitle("Tenant Manager")
            self.tm_window.setWindowModality(Qt.ApplicationModal) # Ensure the window is modal
            self.tm_window.raise_() # Bring the window to the front
            self.tm_window.resize(900, 600) # Resize the window

        elif label == "Outstanding Maintenance":
            self.mm_window = MaintenanceManager(filter_unresolved=True)
            self.mm_window.show()
            self.mm_window.setWindowTitle("Outstanding Maintenance")
            self.mm_window.setWindowModality(Qt.ApplicationModal) # Ensure the window is modal
            self.mm_window.raise_() # Bring the window to the front
            self.mm_window.resize(900, 600) # Resize the window

        elif label == "Vacant Properties":
            self.pm_window = PropertyManager(filter_vacant=True)
            self.pm_window.show()
            self.pm_window.setWindowTitle("Vacant Properties")
            self.pm_window.setWindowModality(Qt.ApplicationModal) # Ensure the window is modal
            self.pm_window.raise_() # Bring the window to the front
            self.pm_window.resize(900, 600) # Resize the window

        elif label == "Tenancies Ending Soon (30d)":
            self.tm_window = TenancyManager(filter_ending_soon=True)
            self.tm_window.show()
            self.tm_window.setWindowTitle("Tenancies Ending Soon")
            self.tm_window.setWindowModality(Qt.ApplicationModal)
            self.tm_window.raise_()
            self.tm_window.resize(900, 600) # Resize the window

    def load_data(self):
        data_queries = {
            "Total Properties": (
                "SELECT COUNT(*) FROM properties", 
                "🏘️ {}"),

            "Total Tenants": (
                "SELECT COUNT(*) FROM tenants", 
                "👥 {}"),

            "Rent Due (30d)": ("""
                SELECT COUNT(*) FROM payments 
                WHERE payment_type = 'rent' 
                AND due_date BETWEEN DATE('now') AND DATE('now', '+30 day')""", 
                "💸 {}"),

            "Outstanding Maintenance": (
                "SELECT COUNT(*) FROM maintenance WHERE LOWER(status) NOT IN ('resolved', 'voided')",
                "🔧 {}"),

            "Vacant Properties": ("""
                SELECT COUNT(*) FROM properties 
                WHERE property_id NOT IN (
                    SELECT property_id FROM tenancies 
                    WHERE DATE('now') BETWEEN start_date AND end_date)""", 
                    "📭 {}"),

            "Tenancies Ending Soon (30d)": ("""
                SELECT COUNT(*) FROM tenancies 
                WHERE end_date <= DATE('now', '+30 day')""", 
                "⏳ {}"),
        }

        for key, (query, template) in data_queries.items():
            value = self.db.fetchval(query)
            self.cards[key].setText(template.format(value))

    def load_alerts(self):
        self.clear_layout(self.alerts_layout)
        alerts = []

        overdue = self.db.fetchval("SELECT COUNT(*) FROM payments WHERE status = 'unpaid' AND due_date < DATE('now')")
        if overdue:
            alerts.append(f"🔴 {overdue} overdue payment(s) need attention.")

        expiring_docs = self.db.fetchval("""
            SELECT COUNT(*) FROM (
                SELECT expiry_date FROM tenant_documents
                UNION ALL
                SELECT expiry_date FROM landlord_documents
                UNION ALL
                SELECT expiry_date FROM property_documents
                UNION ALL
                SELECT expiry_date FROM tenancy_documents
            ) WHERE expiry_date IS NOT NULL AND expiry_date <= DATE('now', '+30 day')
        """)
        if expiring_docs:
            alerts.append(f"📁 {expiring_docs} document(s) expiring in the next 30 days.")

        open_issues = self.db.fetchval("SELECT COUNT(*) FROM maintenance WHERE LOWER(status) NOT IN ('resolved', 'closed')")
        if open_issues:
            alerts.append(f"🛠 {open_issues} unresolved maintenance issue(s).")

        if not alerts:
            label = QLabel("✅ All clear. No urgent issues.")
            self.alerts_layout.addWidget(label)
        else:
            for alert in alerts:
                label = QLabel(alert)
                label.setWordWrap(True)
                self.alerts_layout.addWidget(label)

    def load_insights(self):
        self.clear_layout(self.insights_layout)
        insights = []

        ending_tenancies = self.db.fetchval("SELECT COUNT(*) FROM tenancies WHERE end_date <= DATE('now', '+30 day')")
        if ending_tenancies:
            insights.append(f"📅 {ending_tenancies} tenancy(ies) ending within 30 days.")

        vacant_properties = self.db.fetchval("""
            SELECT COUNT(*) FROM properties p
            WHERE NOT EXISTS (
                SELECT 1 FROM tenancies t
                WHERE t.property_id = p.property_id AND DATE('now') BETWEEN t.start_date AND t.end_date
            )
        """)
        if vacant_properties:
            insights.append(f"🏠 {vacant_properties} property(ies) currently have no active tenancy.")

        if not insights:
            label = QLabel("✅ No tenancy risks or gaps detected.")
            self.insights_layout.addWidget(label)
        else:
            for insight in insights:
                label = QLabel(insight)
                label.setWordWrap(True)
                self.insights_layout.addWidget(label)

    def load_activity_feed(self):
        self.activity_feed.clear()
        activities = self.db.fetchall("""
            SELECT action, details, timestamp FROM activity_logs
            ORDER BY timestamp DESC LIMIT 10
        """)
        for action, details, timestamp in activities:
            self.activity_feed.addItem(f"[{timestamp}] {action} - {details}")

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()
        self.load_alerts()
        self.load_insights()
        self.load_activity_feed()

    def add_property(self):
        dialog = PropertyDetailsPage()
        if dialog.exec() == QDialog.Accepted:
            self.load_data()  # Refresh dashboard stats

    def add_tenant(self):
        dialog = TenantDetailsPage()
        if dialog.exec() == QDialog.Accepted:
            self.load_data()

    def record_payment(self):
        dialog = PaymentDetailsPage()
        if dialog.exec() == QDialog.Accepted:
            self.load_data()

    def report_maintenance(self):
        dialog = MaintenanceDetailsPage()
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
