import csv
import os
from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QComboBox, QScrollArea, QSizePolicy, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont


MESES_NOMBRE = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def fmt_eur(v):
    try:
        val = float(v or 0)
        s = f"{abs(val):,.2f} €"
        s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"-{s}" if val < 0 else s
    except Exception:
        return "0,00 €"


class SummaryCard(QFrame):
    def __init__(self, title, value="0,00 €", color="#2B6CB0", parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            QFrame {{
                background:#FFFFFF;
                border-radius:8px;
                border:1px solid #E2E8F0;
                border-top:4px solid {color};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)
        lbl = QLabel(title.upper())
        lbl.setStyleSheet("color:#718096; font-size:10px; font-weight:bold; letter-spacing:0.8px; border:none;")
        lay.addWidget(lbl)
        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(f"color:{color}; font-size:22px; font-weight:bold; border:none;")
        lay.addWidget(self.val_lbl)
        lay.addStretch()

    def update(self, v):
        self.val_lbl.setText(v)


class InformesWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background:#EEF2F7; border:none; }")

        content = QWidget()
        content.setStyleSheet("background:#EEF2F7;")
        ml = QVBoxLayout(content)
        ml.setContentsMargins(24, 20, 24, 20)
        ml.setSpacing(16)

        # Controls
        ctrl = QHBoxLayout(); ctrl.setSpacing(12)
        ctrl.addWidget(QLabel("Año:"))
        self.anyo_cb = QComboBox(); self.anyo_cb.setFixedWidth(90)
        yr = date.today().year
        for y in range(yr - 5, yr + 2):
            self.anyo_cb.addItem(str(y), y)
        self.anyo_cb.setCurrentText(str(yr))
        self.anyo_cb.currentIndexChanged.connect(self._load)
        ctrl.addWidget(self.anyo_cb)
        ctrl.addStretch()

        export_btn = QPushButton("📥  Exportar CSV")
        export_btn.setStyleSheet("background-color:#4A5568; color:white; border:none;")
        export_btn.setFixedHeight(32); export_btn.clicked.connect(self._export_csv)
        ctrl.addWidget(export_btn)
        ml.addLayout(ctrl)

        # Summary cards
        cards_row = QHBoxLayout(); cards_row.setSpacing(12)
        self.c_cobrado = SummaryCard("Total Cobrado", color="#38A169")
        self.c_gastos = SummaryCard("Total Gastos", color="#D69E2E")
        self.c_neto = SummaryCard("Beneficio Neto", color="#2B6CB0")
        self.c_pendiente = SummaryCard("Pendiente de cobro", color="#E53E3E")
        for c in [self.c_cobrado, self.c_gastos, self.c_neto, self.c_pendiente]:
            c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cards_row.addWidget(c)
        ml.addLayout(cards_row)

        # Monthly table
        table_frame = QFrame()
        table_frame.setStyleSheet("background:#FFFFFF; border-radius:8px; border:1px solid #E2E8F0;")
        tf_lay = QVBoxLayout(table_frame)
        tf_lay.setContentsMargins(16, 12, 16, 12); tf_lay.setSpacing(10)

        title_row = QHBoxLayout()
        tbl_title = QLabel("Resumen Mensual")
        tbl_title.setStyleSheet("font-size:14px; font-weight:bold; color:#2D3748; border:none;")
        title_row.addWidget(tbl_title); title_row.addStretch()
        tf_lay.addLayout(title_row)

        self.table = QTableWidget()
        cols = ["Mes", "Ingresos Cobrados", "Ingresos Esperados", "Gastos", "Neto", "% Cobro"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(320)
        tf_lay.addWidget(self.table)
        ml.addWidget(table_frame)

        # By apartment
        apt_frame = QFrame()
        apt_frame.setStyleSheet("background:#FFFFFF; border-radius:8px; border:1px solid #E2E8F0;")
        af_lay = QVBoxLayout(apt_frame)
        af_lay.setContentsMargins(16, 12, 16, 12); af_lay.setSpacing(10)
        apt_title = QLabel("Ingresos por Apartamento (año seleccionado)")
        apt_title.setStyleSheet("font-size:14px; font-weight:bold; color:#2D3748; border:none;")
        af_lay.addWidget(apt_title)
        self.apt_table = QTableWidget()
        apt_cols = ["Apartamento", "Pagos Cobrados", "Importe Cobrado", "Pendiente"]
        self.apt_table.setColumnCount(len(apt_cols))
        self.apt_table.setHorizontalHeaderLabels(apt_cols)
        self.apt_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.apt_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.apt_table.verticalHeader().setVisible(False)
        self.apt_table.setAlternatingRowColors(True)
        self.apt_table.setMaximumHeight(280)
        af_lay.addWidget(self.apt_table)
        ml.addWidget(apt_frame)
        ml.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load(self):
        yr = self.anyo_cb.currentData()
        fin = self.db.get_resumen_financiero(yr)

        self.c_cobrado.update(fmt_eur(fin.get('cobrado', 0)))
        self.c_gastos.update(fmt_eur(fin.get('gastos', 0)))
        self.c_neto.update(fmt_eur(fin.get('neto', 0)))
        self.c_pendiente.update(fmt_eur(fin.get('pendiente', 0)))

        # Monthly data
        ingresos_mes = {r['mes']: r for r in self.db.get_ingresos_por_mes(yr)}
        gastos_mes = {r['mes']: r['gastos'] for r in self.db.get_gastos_por_mes(yr)}

        self.table.setRowCount(13)  # 12 months + total
        total_cobrado = total_esperado = total_gastos = total_neto = 0.0

        for i in range(12):
            mes = i + 1
            data = ingresos_mes.get(mes, {})
            cobrado = data.get('ingresos', 0) or 0
            esperado = data.get('esperado', 0) or 0
            gasto = gastos_mes.get(mes, 0) or 0
            neto = cobrado - gasto
            pct = (cobrado / esperado * 100) if esperado > 0 else 0

            total_cobrado += cobrado
            total_esperado += esperado
            total_gastos += gasto
            total_neto += neto

            def cell(v, align=Qt.AlignVCenter | Qt.AlignRight, bold=False):
                item = QTableWidgetItem(str(v))
                item.setTextAlignment(align)
                if bold:
                    f = QFont(); f.setBold(True); item.setFont(f)
                return item

            mes_item = QTableWidgetItem(MESES_NOMBRE[i])
            mes_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            if mes == date.today().month and yr == date.today().year:
                for col_idx in range(6):
                    pass  # will set bg below
            self.table.setItem(i, 0, mes_item)
            self.table.setItem(i, 1, cell(fmt_eur(cobrado)))
            self.table.setItem(i, 2, cell(fmt_eur(esperado)))
            self.table.setItem(i, 3, cell(fmt_eur(gasto)))

            neto_item = cell(fmt_eur(neto))
            if neto >= 0:
                neto_item.setForeground(QColor('#38A169'))
            else:
                neto_item.setForeground(QColor('#E53E3E'))
            self.table.setItem(i, 4, neto_item)

            pct_item = cell(f"{pct:.0f} %")
            if pct >= 100:
                pct_item.setForeground(QColor('#38A169'))
            elif pct >= 50:
                pct_item.setForeground(QColor('#D69E2E'))
            else:
                pct_item.setForeground(QColor('#E53E3E'))
            self.table.setItem(i, 5, pct_item)

            # Highlight current month
            if mes == date.today().month and yr == date.today().year:
                for col_idx in range(6):
                    item = self.table.item(i, col_idx)
                    if item:
                        item.setBackground(QColor('#EBF8FF'))

        # Total row
        def bold_cell(v, align=Qt.AlignVCenter | Qt.AlignRight):
            item = QTableWidgetItem(str(v))
            item.setTextAlignment(align)
            f = QFont(); f.setBold(True); item.setFont(f)
            item.setBackground(QColor('#F0F4F8'))
            return item

        self.table.setItem(12, 0, bold_cell("TOTAL", Qt.AlignVCenter | Qt.AlignLeft))
        self.table.setItem(12, 1, bold_cell(fmt_eur(total_cobrado)))
        self.table.setItem(12, 2, bold_cell(fmt_eur(total_esperado)))
        self.table.setItem(12, 3, bold_cell(fmt_eur(total_gastos)))
        neto_total_item = bold_cell(fmt_eur(total_neto))
        neto_total_item.setForeground(QColor('#38A169') if total_neto >= 0 else QColor('#E53E3E'))
        self.table.setItem(12, 4, neto_total_item)
        pct_total = (total_cobrado / total_esperado * 100) if total_esperado > 0 else 0
        self.table.setItem(12, 5, bold_cell(f"{pct_total:.0f} %"))

        # By apartment
        self._load_by_apartment(yr)

    def _load_by_apartment(self, yr):
        conn = self.db._conn()
        rows = conn.execute("""
            SELECT a.nombre,
                SUM(CASE WHEN p.estado='pagado' THEN 1 ELSE 0 END) pagos_cobrados,
                COALESCE(SUM(CASE WHEN p.estado='pagado' THEN p.importe ELSE 0 END),0) cobrado,
                COALESCE(SUM(CASE WHEN p.estado IN ('pendiente','retrasado') THEN p.importe ELSE 0 END),0) pendiente
            FROM apartamentos a
            LEFT JOIN contratos c ON c.apartamento_id = a.id
            LEFT JOIN pagos p ON p.contrato_id = c.id AND p.anyo = ?
            GROUP BY a.id, a.nombre
            ORDER BY cobrado DESC
        """, (yr,)).fetchall()
        conn.close()

        self.apt_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            def cell(v, align=Qt.AlignVCenter | Qt.AlignLeft):
                item = QTableWidgetItem(str(v) if v else '—')
                item.setTextAlignment(align)
                return item
            self.apt_table.setItem(i, 0, cell(r[0]))
            self.apt_table.setItem(i, 1, cell(str(r[1] or 0), Qt.AlignCenter))
            self.apt_table.setItem(i, 2, cell(fmt_eur(r[2]), Qt.AlignRight | Qt.AlignVCenter))
            pend_item = cell(fmt_eur(r[3]), Qt.AlignRight | Qt.AlignVCenter)
            if (r[3] or 0) > 0:
                pend_item.setForeground(QColor('#E53E3E'))
            self.apt_table.setItem(i, 3, pend_item)

    def _export_csv(self):
        yr = self.anyo_cb.currentData()
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Informe CSV",
            os.path.expanduser(f"~/informe_calasdealmeria_{yr}.csv"),
            "CSV (*.csv)"
        )
        if not path:
            return
        try:
            ingresos_mes = {r['mes']: r for r in self.db.get_ingresos_por_mes(yr)}
            gastos_mes = {r['mes']: r['gastos'] for r in self.db.get_gastos_por_mes(yr)}
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Mes", "Ingresos Cobrados (€)", "Ingresos Esperados (€)",
                                 "Gastos (€)", "Neto (€)", "% Cobro"])
                for i in range(12):
                    mes = i + 1
                    d = ingresos_mes.get(mes, {})
                    cobrado = d.get('ingresos', 0) or 0
                    esperado = d.get('esperado', 0) or 0
                    gasto = gastos_mes.get(mes, 0) or 0
                    neto = cobrado - gasto
                    pct = (cobrado / esperado * 100) if esperado > 0 else 0
                    writer.writerow([
                        MESES_NOMBRE[i],
                        f"{cobrado:.2f}", f"{esperado:.2f}",
                        f"{gasto:.2f}", f"{neto:.2f}", f"{pct:.1f}%"
                    ])
            QMessageBox.information(self, "Exportado", f"Informe exportado correctamente:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo exportar: {e}")

    def refresh(self):
        self._load()
