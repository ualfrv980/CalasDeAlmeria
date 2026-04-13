from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QTextEdit, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont


ESTADO_COLORS = {
    'libre':     ('#D1ECF1', '#0C5460'),
    'ocupado':   ('#D4EDDA', '#155724'),
    'obras':     ('#FFF3CD', '#856404'),
    'reservado': ('#E2D9F3', '#4B2D8B'),
}


def make_btn(text, cls=''):
    btn = QPushButton(text)
    if cls:
        btn.setProperty('class', cls)
        style_map = {
            'secondary': 'background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;',
            'danger':    'background-color:#E53E3E; color:white; border:none;',
            'success':   'background-color:#38A169; color:white; border:none;',
            'warning':   'background-color:#D69E2E; color:white; border:none;',
        }
        btn.setStyleSheet(style_map.get(cls, ''))
    btn.setFixedHeight(32)
    return btn


class ApartamentosWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._all = []
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(12)

        # Toolbar
        bar = QHBoxLayout(); bar.setSpacing(8)
        bar.addWidget(QLabel("Buscar:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Nombre, dirección...")
        self.search.setFixedWidth(240)
        self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search)

        bar.addWidget(QLabel("Estado:"))
        self.estado_cb = QComboBox()
        self.estado_cb.addItems(["Todos", "Libre", "Ocupado", "Obras", "Reservado"])
        self.estado_cb.setFixedWidth(120)
        self.estado_cb.currentTextChanged.connect(self._filter)
        bar.addWidget(self.estado_cb)

        bar.addStretch()
        add_btn = make_btn("＋  Añadir Apartamento")
        add_btn.clicked.connect(self._add)
        bar.addWidget(add_btn)
        lay.addLayout(bar)

        # Table
        self.table = QTableWidget()
        cols = ["ID", "Nombre", "Dirección", "Planta/Nº", "Estado",
                "Hab.", "Baños", "m²", "Alquiler/mes"]
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

        # Actions
        actions = QHBoxLayout(); actions.setSpacing(8)
        edit_btn = make_btn("✏  Editar", 'secondary')
        edit_btn.clicked.connect(self._edit)
        del_btn = make_btn("🗑  Eliminar", 'danger')
        del_btn.clicked.connect(self._delete)
        actions.addWidget(edit_btn)
        actions.addWidget(del_btn)
        actions.addStretch()
        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet("color:#718096; font-size:12px;")
        actions.addWidget(self.summary_lbl)
        lay.addLayout(actions)

    def _load(self):
        self._all = self.db.get_apartamentos()
        self._populate(self._all)

    def _populate(self, data):
        self.table.setRowCount(len(data))
        for i, apt in enumerate(data):
            def cell(v, align=Qt.AlignVCenter | Qt.AlignLeft):
                item = QTableWidgetItem(str(v) if v is not None else '')
                item.setTextAlignment(align)
                return item

            self.table.setItem(i, 0, cell(apt['id'], Qt.AlignCenter))
            self.table.setItem(i, 1, cell(apt.get('nombre', '')))
            self.table.setItem(i, 2, cell(apt.get('direccion', '') or ''))
            p = apt.get('planta', '') or ''; n = apt.get('numero', '') or ''
            self.table.setItem(i, 3, cell(f"{p}/{n}".strip('/') if p or n else ''))

            estado = apt.get('estado', 'libre')
            s_item = QTableWidgetItem(estado.capitalize())
            s_item.setTextAlignment(Qt.AlignCenter)
            bg, fg = ESTADO_COLORS.get(estado, ('#FFFFFF', '#000000'))
            s_item.setBackground(QColor(bg))
            s_item.setForeground(QColor(fg))
            f = QFont(); f.setBold(True)
            s_item.setFont(f)
            self.table.setItem(i, 4, s_item)

            self.table.setItem(i, 5, cell(apt.get('habitaciones', 1), Qt.AlignCenter))
            self.table.setItem(i, 6, cell(apt.get('banos', 1), Qt.AlignCenter))
            m2 = apt.get('metros_cuadrados')
            self.table.setItem(i, 7, cell(f"{m2:.1f}" if m2 else '', Qt.AlignRight | Qt.AlignVCenter))
            alq = apt.get('alquiler_base') or 0
            alq_str = f"{alq:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.') if alq else ''
            self.table.setItem(i, 8, cell(alq_str, Qt.AlignRight | Qt.AlignVCenter))

        total = len(self._all)
        libres = sum(1 for a in self._all if a.get('estado') == 'libre')
        ocupados = sum(1 for a in self._all if a.get('estado') == 'ocupado')
        obras = sum(1 for a in self._all if a.get('estado') == 'obras')
        self.summary_lbl.setText(
            f"Total: {total}  |  Libres: {libres}  |  Ocupados: {ocupados}  |  Obras: {obras}"
        )

    def _filter(self):
        text = self.search.text().lower()
        estado = self.estado_cb.currentText().lower()
        if estado == "todos":
            estado = ""
        filtered = []
        for a in self._all:
            if estado and a.get('estado', '').lower() != estado:
                continue
            if text and text not in f"{a.get('nombre','')} {a.get('direccion','')}".lower():
                continue
            filtered.append(a)
        self._populate(filtered)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _add(self):
        dlg = ApartamentoDialog(self.db, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load()

    def _edit(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un apartamento.")
            return
        apt = self.db.get_apartamento(id_)
        if apt:
            dlg = ApartamentoDialog(self.db, apt, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self._load()

    def _delete(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un apartamento.")
            return
        apt = self.db.get_apartamento(id_)
        name = apt.get('nombre', '') if apt else ''
        if QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar el apartamento «{name}»?\nSe eliminarán todos sus datos asociados.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            self.db.delete_apartamento(id_)
            self._load()

    def refresh(self):
        self._load()


class ApartamentoDialog(QDialog):
    def __init__(self, db, item=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.item = item
        self.setWindowTitle("Editar Apartamento" if item else "Nuevo Apartamento")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._setup_ui()
        if item:
            self._populate(item)

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(9)
        form.setLabelAlignment(Qt.AlignRight)

        self.nombre = QLineEdit(); self.nombre.setPlaceholderText("Ej: Apartamento 1A")
        form.addRow("Nombre *:", self.nombre)

        self.direccion = QLineEdit(); self.direccion.setPlaceholderText("Calle, número, ciudad...")
        form.addRow("Dirección:", self.direccion)

        row_pn = QHBoxLayout(); row_pn.setSpacing(8)
        self.planta = QLineEdit(); self.planta.setPlaceholderText("Ej: 3ª")
        self.numero = QLineEdit(); self.numero.setPlaceholderText("Ej: B")
        row_pn.addWidget(self.planta); row_pn.addWidget(QLabel("Nº:")); row_pn.addWidget(self.numero)
        form.addRow("Planta:", row_pn)

        row_hb = QHBoxLayout(); row_hb.setSpacing(8)
        self.habitaciones = QSpinBox(); self.habitaciones.setRange(0, 20); self.habitaciones.setValue(1)
        self.banos = QSpinBox(); self.banos.setRange(0, 10); self.banos.setValue(1)
        row_hb.addWidget(self.habitaciones); row_hb.addWidget(QLabel("Baños:")); row_hb.addWidget(self.banos)
        form.addRow("Habitaciones:", row_hb)

        self.metros = QDoubleSpinBox()
        self.metros.setRange(0, 9999); self.metros.setSuffix(" m²"); self.metros.setDecimals(1)
        form.addRow("Superficie:", self.metros)

        self.estado = QComboBox()
        self.estado.addItems(["libre", "ocupado", "obras", "reservado"])
        form.addRow("Estado:", self.estado)

        self.alquiler = QDoubleSpinBox()
        self.alquiler.setRange(0, 99999); self.alquiler.setSuffix(" €/mes"); self.alquiler.setDecimals(2)
        form.addRow("Alquiler base:", self.alquiler)

        self.descripcion = QTextEdit(); self.descripcion.setMaximumHeight(72)
        self.descripcion.setPlaceholderText("Descripción del apartamento...")
        form.addRow("Descripción:", self.descripcion)

        self.notas = QTextEdit(); self.notas.setMaximumHeight(54)
        self.notas.setPlaceholderText("Notas internas...")
        form.addRow("Notas:", self.notas)

        lay.addLayout(form)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        btn_row.addStretch()
        cancel = make_btn("Cancelar", 'secondary')
        cancel.clicked.connect(self.reject)
        save = make_btn("💾  Guardar")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _populate(self, d):
        self.nombre.setText(d.get('nombre', ''))
        self.direccion.setText(d.get('direccion', '') or '')
        self.planta.setText(d.get('planta', '') or '')
        self.numero.setText(d.get('numero', '') or '')
        self.habitaciones.setValue(d.get('habitaciones', 1) or 1)
        self.banos.setValue(d.get('banos', 1) or 1)
        self.metros.setValue(d.get('metros_cuadrados', 0) or 0)
        idx = self.estado.findText(d.get('estado', 'libre'))
        self.estado.setCurrentIndex(max(0, idx))
        self.alquiler.setValue(d.get('alquiler_base', 0) or 0)
        self.descripcion.setPlainText(d.get('descripcion', '') or '')
        self.notas.setPlainText(d.get('notas', '') or '')

    def _get_data(self):
        return {
            'nombre': self.nombre.text().strip(),
            'direccion': self.direccion.text().strip(),
            'planta': self.planta.text().strip(),
            'numero': self.numero.text().strip(),
            'habitaciones': self.habitaciones.value(),
            'banos': self.banos.value(),
            'metros_cuadrados': self.metros.value() or None,
            'estado': self.estado.currentText(),
            'alquiler_base': self.alquiler.value() or None,
            'descripcion': self.descripcion.toPlainText().strip(),
            'notas': self.notas.toPlainText().strip(),
        }

    def _save(self):
        d = self._get_data()
        if not d['nombre']:
            QMessageBox.warning(self, "Campo requerido", "El nombre es obligatorio.")
            return
        if self.item:
            self.db.update_apartamento(self.item['id'], d)
        else:
            self.db.add_apartamento(d)
        self.accept()
