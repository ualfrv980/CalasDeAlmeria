from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from datetime import date


def fmt_eur(val):
    """Format a number as Spanish euro string."""
    try:
        v = float(val or 0)
        s = f"{abs(v):,.2f} €"
        s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"-{s}" if v < 0 else s
    except Exception:
        return "0,00 €"


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "0", subtitle: str = "",
                 color: str = "#2B6CB0", parent=None):
        super().__init__(parent)
        self.setFixedHeight(108)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
                border-left: 5px solid {color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(3)

        lbl = QLabel(title.upper())
        lbl.setStyleSheet("color:#718096; font-size:10px; font-weight:bold; letter-spacing:0.8px; border:none;")
        layout.addWidget(lbl)

        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(f"color:{color}; font-size:26px; font-weight:bold; border:none;")
        layout.addWidget(self.val_lbl)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color:#A0AEC0; font-size:11px; border:none;")
            layout.addWidget(sub)

        layout.addStretch()

    def update_value(self, v: str):
        self.val_lbl.setText(v)


class DashboardWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #EEF2F7; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: #EEF2F7;")
        ml = QVBoxLayout(content)
        ml.setContentsMargins(24, 20, 24, 20)
        ml.setSpacing(16)

        # Row 1: Apartment stats
        row1 = QHBoxLayout(); row1.setSpacing(12)
        self.c_total = StatCard("Total Apartamentos", color="#2B6CB0", subtitle="en cartera")
        self.c_ocup = StatCard("Ocupados", color="#38A169", subtitle="con inquilino activo")
        self.c_libres = StatCard("Disponibles", color="#3182CE", subtitle="listos para alquilar")
        self.c_obras = StatCard("En Obras", color="#D69E2E", subtitle="en reforma")
        for c in [self.c_total, self.c_ocup, self.c_libres, self.c_obras]:
            c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row1.addWidget(c)
        ml.addLayout(row1)

        # Row 2: Financial stats
        row2 = QHBoxLayout(); row2.setSpacing(12)
        self.c_cobrado = StatCard("Cobrado este año", color="#38A169")
        self.c_pend = StatCard("Pendiente de cobro", color="#E53E3E")
        self.c_gastos = StatCard("Gastos este año", color="#D69E2E")
        self.c_neto = StatCard("Beneficio Neto", color="#2B6CB0")
        for c in [self.c_cobrado, self.c_pend, self.c_gastos, self.c_neto]:
            c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row2.addWidget(c)
        ml.addLayout(row2)

        # Row 3: Tables
        row3 = QHBoxLayout(); row3.setSpacing(16)

        # Pending payments
        pagos_frame = self._make_section("💰  Pagos Pendientes — Mes Actual")
        self.pagos_table = self._make_mini_table(
            ["Apartamento", "Inquilino", "Importe", "Vencimiento"]
        )
        pagos_frame.layout().addWidget(self.pagos_table)
        row3.addWidget(pagos_frame)

        # Urgent maintenance
        mant_frame = self._make_section("🔧  Mantenimiento Urgente / Alta Prioridad")
        self.mant_table = self._make_mini_table(
            ["Apartamento", "Título", "Prioridad", "Estado"]
        )
        mant_frame.layout().addWidget(self.mant_table)
        row3.addWidget(mant_frame)

        ml.addLayout(row3)
        ml.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _make_section(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background:#FFFFFF; border-radius:8px; border:1px solid #E2E8F0; }"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size:13px; font-weight:bold; color:#2D3748; border:none;")
        layout.addWidget(lbl)
        return frame

    def _make_mini_table(self, headers: list) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setMaximumHeight(200)
        t.setAlternatingRowColors(True)
        return t

    def refresh(self):
        # Apartment stats
        s = self.db.get_stats_apartamentos()
        self.c_total.update_value(str(s.get('total', 0)))
        self.c_ocup.update_value(str(s.get('ocupados', 0)))
        self.c_libres.update_value(str(s.get('libres', 0)))
        self.c_obras.update_value(str(s.get('en_obras', 0)))

        # Financial
        f = self.db.get_resumen_financiero()
        self.c_cobrado.update_value(fmt_eur(f.get('cobrado', 0)))
        self.c_pend.update_value(fmt_eur(f.get('pendiente', 0)))
        self.c_gastos.update_value(fmt_eur(f.get('gastos', 0)))
        self.c_neto.update_value(fmt_eur(f.get('neto', 0)))

        # Pending payments this month
        today = date.today()
        pagos = self.db.get_pagos(estado='pendiente', anyo=today.year, mes=today.month)
        self.pagos_table.setRowCount(len(pagos))
        for i, p in enumerate(pagos):
            self.pagos_table.setItem(i, 0, QTableWidgetItem(p.get('apt_nombre', '') or ''))
            self.pagos_table.setItem(i, 1, QTableWidgetItem((p.get('inq_nombre', '') or '').strip()))
            self.pagos_table.setItem(i, 2, QTableWidgetItem(fmt_eur(p.get('importe', 0))))
            self.pagos_table.setItem(i, 3, QTableWidgetItem(p.get('fecha_vencimiento', '') or ''))
            color = QColor('#FFF5F5')
            for col in range(4):
                item = self.pagos_table.item(i, col)
                if item:
                    item.setBackground(color)

        # Urgent maintenance
        mant = self.db.get_mantenimiento()
        urgent = [m for m in mant if m['prioridad'] in ('urgente', 'alta') and m['estado'] != 'completado']
        self.mant_table.setRowCount(len(urgent))
        pri_colors = {'urgente': '#FED7D7', 'alta': '#FEEBC8'}
        for i, m in enumerate(urgent):
            self.mant_table.setItem(i, 0, QTableWidgetItem(m.get('apt_nombre', '') or 'General'))
            self.mant_table.setItem(i, 1, QTableWidgetItem(m.get('titulo', '')))
            pri_item = QTableWidgetItem(m.get('prioridad', '').capitalize())
            pri_item.setBackground(QColor(pri_colors.get(m.get('prioridad', ''), '#FFFFFF')))
            self.mant_table.setItem(i, 2, pri_item)
            self.mant_table.setItem(i, 3, QTableWidgetItem(
                m.get('estado', '').replace('_', ' ').capitalize()
            ))
