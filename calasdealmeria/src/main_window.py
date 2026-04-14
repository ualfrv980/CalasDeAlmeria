from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from src.styles import get_stylesheet
from src.backup import make_backup
from src.widgets.dashboard import DashboardWidget
from src.widgets.apartments import ApartamentosWidget
from src.widgets.tenants import InquilinosWidget
from src.widgets.contracts import ContratosWidget
from src.widgets.payments import PagosWidget
from src.widgets.maintenance import MantenimientoWidget
from src.widgets.expenses import GastosWidget
from src.widgets.reports import InformesWidget


class SidebarButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_text}   {label}")
        self.setFixedHeight(46)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("sidebarButton")


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Calas de Almería — Gestión Inmobiliaria")
        self.setMinimumSize(1100, 650)
        self.resize(1380, 820)
        self.setStyleSheet(get_stylesheet())
        self._setup_ui()
        self._nav_click(0)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(215)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo
        header = QFrame()
        header.setObjectName("sidebarHeader")
        header.setFixedHeight(70)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(16, 10, 16, 10)
        h_layout.setSpacing(2)
        title_lbl = QLabel("Calas de Almería")
        title_lbl.setObjectName("logoTitle")
        sub_lbl = QLabel("Gestión Inmobiliaria")
        sub_lbl.setObjectName("logoSubtitle")
        h_layout.addWidget(title_lbl)
        h_layout.addWidget(sub_lbl)
        sb_layout.addWidget(header)

        section_lbl = QLabel("  MENÚ PRINCIPAL")
        section_lbl.setObjectName("sidebarSectionLabel")
        section_lbl.setFixedHeight(32)
        sb_layout.addWidget(section_lbl)

        nav_items = [
            ("🏠", "Dashboard"),
            ("🏢", "Apartamentos"),
            ("👤", "Inquilinos"),
            ("📋", "Contratos"),
            ("💰", "Pagos"),
            ("🔧", "Mantenimiento"),
            ("📊", "Gastos"),
            ("📈", "Informes"),
        ]

        self.nav_buttons = []
        for i, (icon, label) in enumerate(nav_items):
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda checked, idx=i: self._nav_click(idx))
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()

        ver_lbl = QLabel("  v1.0.0  |  Fran Ruiz")
        ver_lbl.setObjectName("sidebarVersion")
        ver_lbl.setFixedHeight(30)
        sb_layout.addWidget(ver_lbl)

        main_layout.addWidget(sidebar)

        # ── Content area ─────────────────────────────────────
        content_area = QWidget()
        content_area.setObjectName("contentArea")
        c_layout = QVBoxLayout(content_area)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(24, 0, 24, 0)
        self.page_title_lbl = QLabel("Dashboard")
        self.page_title_lbl.setObjectName("pageTitle")
        tb_layout.addWidget(self.page_title_lbl)
        tb_layout.addStretch()
        c_layout.addWidget(topbar)

        # Pages
        self.stack = QStackedWidget()
        self.dashboard_w = DashboardWidget(self.db)
        self.apartamentos_w = ApartamentosWidget(self.db)
        self.inquilinos_w = InquilinosWidget(self.db)
        self.contratos_w = ContratosWidget(self.db)
        self.pagos_w = PagosWidget(self.db)
        self.mantenimiento_w = MantenimientoWidget(self.db)
        self.gastos_w = GastosWidget(self.db)
        self.informes_w = InformesWidget(self.db)

        for w in [self.dashboard_w, self.apartamentos_w, self.inquilinos_w,
                  self.contratos_w, self.pagos_w, self.mantenimiento_w,
                  self.gastos_w, self.informes_w]:
            self.stack.addWidget(w)

        c_layout.addWidget(self.stack)
        main_layout.addWidget(content_area)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bienvenido a Calas de Almería — Gestión Inmobiliaria")

    _page_titles = [
        "Dashboard", "Apartamentos", "Inquilinos", "Contratos",
        "Pagos", "Mantenimiento", "Gastos", "Informes",
    ]

    def closeEvent(self, event):
        ok, msg = make_backup(self.db.db_path)
        if ok:
            self.status_bar.showMessage(msg)
        event.accept()

    def _nav_click(self, idx: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        self.page_title_lbl.setText(self._page_titles[idx])
        page = self.stack.currentWidget()
        if hasattr(page, 'refresh'):
            page.refresh()
        self.status_bar.showMessage(f"Sección: {self._page_titles[idx]}")
