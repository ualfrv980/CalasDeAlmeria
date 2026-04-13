from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox,
    QTextEdit, QMessageBox, QDateEdit, QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from datetime import date


CATEGORIAS = ["Comunidad", "Seguro", "IBI", "Reparación", "Suministros",
              "Gestión", "Hipoteca", "Impuestos", "Otro"]

CATEGORIA_COLORS = {
    'comunidad':   '#DBEAFE',
    'seguro':      '#D1FAE5',
    'ibi':         '#FDE68A',
    'reparación':  '#FECACA',
    'suministros': '#DDD6FE',
    'gestión':     '#FED7AA',
    'hipoteca':    '#BFDBFE',
    'impuestos':   '#FEF3C7',
    'otro':        '#F3F4F6',
}


def fmt_eur(v):
    try:
        s = f"{float(v or 0):,.2f} €"
        return s.replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return "0,00 €"


class GastosWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._all = []
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(12)

        bar = QHBoxLayout(); bar.setSpacing(8)

        bar.addWidget(QLabel("Año:"))
        self.anyo_cb = QComboBox(); self.anyo_cb.setFixedWidth(80)
        yr = date.today().year
        for y in range(yr - 3, yr + 3):
            self.anyo_cb.addItem(str(y), y)
        self.anyo_cb.setCurrentText(str(yr))
        self.anyo_cb.currentIndexChanged.connect(self._load)
        bar.addWidget(self.anyo_cb)

        bar.addWidget(QLabel("Categoría:"))
        self.cat_cb = QComboBox(); self.cat_cb.setFixedWidth(130)
        self.cat_cb.addItem("Todas", "")
        for c in CATEGORIAS:
            self.cat_cb.addItem(c, c.lower())
        self.cat_cb.currentIndexChanged.connect(self._filter)
        bar.addWidget(self.cat_cb)

        bar.addWidget(QLabel("Buscar:"))
        self.search = QLineEdit(); self.search.setPlaceholderText("Descripción, apartamento...")
        self.search.setFixedWidth(220); self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search)

        bar.addStretch()
        add_btn = QPushButton("＋  Nuevo Gasto")
        add_btn.setFixedHeight(32); add_btn.clicked.connect(self._add)
        bar.addWidget(add_btn)
        lay.addLayout(bar)

        # Summary strip
        sf = QFrame()
        sf.setStyleSheet("background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px;")
        sf_lay = QHBoxLayout(sf)
        sf_lay.setContentsMargins(16, 8, 16, 8); sf_lay.setSpacing(24)
        self.lbl_total = QLabel("Total gastos: 0,00 €")
        self.lbl_total.setStyleSheet("color:#D69E2E; font-weight:bold; font-size:13px;")
        sf_lay.addWidget(self.lbl_total)
        self.lbl_cat_total = QLabel()
        self.lbl_cat_total.setStyleSheet("color:#4A5568; font-size:12px;")
        sf_lay.addWidget(self.lbl_cat_total)
        sf_lay.addStretch()
        lay.addWidget(sf)

        # Table
        self.table = QTableWidget()
        cols = ["ID", "Apartamento", "Descripción", "Importe", "Fecha", "Categoría", "Notas"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit)
        lay.addWidget(self.table)

        actions = QHBoxLayout(); actions.setSpacing(8)
        edit_btn = QPushButton("✏  Editar")
        edit_btn.setStyleSheet("background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        edit_btn.setFixedHeight(32); edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("🗑  Eliminar")
        del_btn.setStyleSheet("background-color:#E53E3E; color:white; border:none;")
        del_btn.setFixedHeight(32); del_btn.clicked.connect(self._delete)
        actions.addWidget(edit_btn); actions.addWidget(del_btn)
        actions.addStretch()
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("color:#718096; font-size:12px;")
        actions.addWidget(self.count_lbl)
        lay.addLayout(actions)

    def _load(self):
        anyo = self.anyo_cb.currentData()
        self._all = self.db.get_gastos(anyo=anyo)
        self._filter()

    def _filter(self):
        text = self.search.text().lower()
        cat = self.cat_cb.currentData()
        filtered = []
        for g in self._all:
            if cat and g.get('categoria', '').lower() != cat:
                continue
            if text and text not in f"{g.get('descripcion','')} {g.get('apt_nombre','')}".lower():
                continue
            filtered.append(g)
        self._populate(filtered)

    def _populate(self, data):
        self.table.setRowCount(len(data))
        total = 0.0
        for i, g in enumerate(data):
            def cell(v, align=Qt.AlignVCenter | Qt.AlignLeft):
                item = QTableWidgetItem(str(v) if v is not None else '')
                item.setTextAlignment(align)
                return item

            importe = g.get('importe', 0) or 0
            total += importe
            self.table.setItem(i, 0, cell(g['id'], Qt.AlignCenter))
            self.table.setItem(i, 1, cell(g.get('apt_nombre', '') or 'General'))
            self.table.setItem(i, 2, cell(g.get('descripcion', '')))
            self.table.setItem(i, 3, cell(fmt_eur(importe), Qt.AlignRight | Qt.AlignVCenter))
            self.table.setItem(i, 4, cell(g.get('fecha', '') or ''))
            cat = g.get('categoria', 'otro') or 'otro'
            cat_item = QTableWidgetItem(cat.capitalize())
            cat_item.setTextAlignment(Qt.AlignCenter)
            bg = CATEGORIA_COLORS.get(cat.lower(), '#F3F4F6')
            cat_item.setBackground(QColor(bg))
            self.table.setItem(i, 5, cat_item)
            self.table.setItem(i, 6, cell(g.get('notas', '') or ''))

        self.lbl_total.setText(f"Total gastos: {fmt_eur(total)}")
        self.count_lbl.setText(f"Registros: {len(data)}")

        # Category breakdown
        from collections import defaultdict
        by_cat = defaultdict(float)
        for g in data:
            by_cat[g.get('categoria', 'otro') or 'otro'] += g.get('importe', 0) or 0
        top3 = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:3]
        cat_text = "  |  ".join(f"{k.capitalize()}: {fmt_eur(v)}" for k, v in top3)
        self.lbl_cat_total.setText(cat_text)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _add(self):
        dlg = GastoDialog(self.db, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load()

    def _edit(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un gasto.")
            return
        gastos = self.db.get_gastos()
        g = next((x for x in gastos if x['id'] == id_), None)
        if g:
            dlg = GastoDialog(self.db, g, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self._load()

    def _delete(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un gasto.")
            return
        if QMessageBox.question(
            self, "Confirmar", "¿Eliminar este gasto?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            self.db.delete_gasto(id_)
            self._load()

    def refresh(self):
        self._load()


class GastoDialog(QDialog):
    def __init__(self, db, item=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.item = item
        self.setWindowTitle("Editar Gasto" if item else "Nuevo Gasto")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._setup_ui()
        if item:
            self._populate(item)

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(14)

        form = QFormLayout(); form.setSpacing(9); form.setLabelAlignment(Qt.AlignRight)

        self.apt_cb = QComboBox()
        self.apt_cb.addItem("— General / Sin apartamento —", None)
        for a in self.db.get_apartamentos():
            self.apt_cb.addItem(f"{a['nombre']} — {a.get('direccion','')}", a['id'])
        form.addRow("Apartamento:", self.apt_cb)

        self.descripcion = QLineEdit(); self.descripcion.setPlaceholderText("Ej: Cuota comunidad enero")
        form.addRow("Descripción *:", self.descripcion)

        self.importe = QDoubleSpinBox()
        self.importe.setRange(0, 999999); self.importe.setSuffix(" €"); self.importe.setDecimals(2)
        form.addRow("Importe *:", self.importe)

        self.fecha = QDateEdit()
        self.fecha.setDate(QDate.currentDate())
        self.fecha.setCalendarPopup(True); self.fecha.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha:", self.fecha)

        self.categoria = QComboBox()
        for c in CATEGORIAS:
            self.categoria.addItem(c, c.lower())
        form.addRow("Categoría:", self.categoria)

        self.notas = QLineEdit(); self.notas.setPlaceholderText("Notas adicionales...")
        form.addRow("Notas:", self.notas)

        lay.addLayout(form)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8); btn_row.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setStyleSheet("background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        cancel.setFixedHeight(32); cancel.clicked.connect(self.reject)
        save = QPushButton("💾  Guardar"); save.setFixedHeight(32); save.clicked.connect(self._save)
        btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _populate(self, d):
        apt_id = d.get('apartamento_id')
        if apt_id:
            for i in range(self.apt_cb.count()):
                if self.apt_cb.itemData(i) == apt_id:
                    self.apt_cb.setCurrentIndex(i); break
        self.descripcion.setText(d.get('descripcion', ''))
        self.importe.setValue(d.get('importe', 0) or 0)
        if d.get('fecha'):
            self.fecha.setDate(QDate.fromString(d['fecha'], "yyyy-MM-dd"))
        idx = self.categoria.findData((d.get('categoria', 'otro') or 'otro').lower())
        if idx >= 0: self.categoria.setCurrentIndex(idx)
        self.notas.setText(d.get('notas', '') or '')

    def _save(self):
        if not self.descripcion.text().strip():
            QMessageBox.warning(self, "Campo requerido", "La descripción es obligatoria.")
            return
        if self.importe.value() <= 0:
            QMessageBox.warning(self, "Campo requerido", "El importe debe ser mayor que 0.")
            return
        d = {
            'apartamento_id': self.apt_cb.currentData(),
            'descripcion': self.descripcion.text().strip(),
            'importe': self.importe.value(),
            'fecha': self.fecha.date().toString("yyyy-MM-dd"),
            'categoria': self.categoria.currentData(),
            'notas': self.notas.text().strip(),
        }
        if self.item:
            self.db.update_gasto(self.item['id'], d)
        else:
            self.db.add_gasto(d)
        self.accept()
