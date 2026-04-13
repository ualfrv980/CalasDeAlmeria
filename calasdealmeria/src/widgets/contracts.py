from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QTextEdit, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from datetime import date


ESTADO_COLORS = {
    'activo':     ('#D4EDDA', '#155724'),
    'finalizado': ('#E2E8F0', '#4A5568'),
    'rescindido': ('#F8D7DA', '#721C24'),
}

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


class ContratosWidget(QWidget):
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
        bar.addWidget(QLabel("Estado:"))
        self.estado_cb = QComboBox()
        self.estado_cb.addItems(["Todos", "Activo", "Finalizado", "Rescindido"])
        self.estado_cb.setFixedWidth(130)
        self.estado_cb.currentTextChanged.connect(self._load)
        bar.addWidget(self.estado_cb)

        bar.addWidget(QLabel("Buscar:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Apartamento, inquilino...")
        self.search.setFixedWidth(240)
        self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search)

        bar.addStretch()
        add_btn = QPushButton("＋  Nuevo Contrato")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._add)
        bar.addWidget(add_btn)
        lay.addLayout(bar)

        self.table = QTableWidget()
        cols = ["ID", "Apartamento", "Inquilino", "Inicio", "Fin",
                "Alquiler/mes", "Depósito", "Día pago", "Estado"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
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
        edit_btn.setFixedHeight(32)
        edit_btn.clicked.connect(self._edit)

        gen_pago_btn = QPushButton("💰  Generar Pago")
        gen_pago_btn.setStyleSheet("background-color:#38A169; color:white; border:none;")
        gen_pago_btn.setFixedHeight(32)
        gen_pago_btn.clicked.connect(self._gen_pago)

        del_btn = QPushButton("🗑  Eliminar")
        del_btn.setStyleSheet("background-color:#E53E3E; color:white; border:none;")
        del_btn.setFixedHeight(32)
        del_btn.clicked.connect(self._delete)

        actions.addWidget(edit_btn)
        actions.addWidget(gen_pago_btn)
        actions.addWidget(del_btn)
        actions.addStretch()
        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet("color:#718096; font-size:12px;")
        actions.addWidget(self.summary_lbl)
        lay.addLayout(actions)

    def _load(self):
        estado = self.estado_cb.currentText().lower()
        estado_val = None if estado == "todos" else estado
        self._all = self.db.get_contratos(estado=estado_val)
        self._filter()

    def _filter(self):
        text = self.search.text().lower()
        if not text:
            self._populate(self._all)
            return
        filtered = [
            c for c in self._all
            if text in f"{c.get('apt_nombre','')} {c.get('inq_nombre','')}".lower()
        ]
        self._populate(filtered)

    def _populate(self, data):
        self.table.setRowCount(len(data))
        for i, c in enumerate(data):
            def cell(v, align=Qt.AlignVCenter | Qt.AlignLeft):
                item = QTableWidgetItem(str(v) if v is not None else '')
                item.setTextAlignment(align)
                return item

            def eur(v):
                try:
                    s = f"{float(v):,.2f} €"
                    return s.replace(',', 'X').replace('.', ',').replace('X', '.')
                except Exception:
                    return ''

            self.table.setItem(i, 0, cell(c['id'], Qt.AlignCenter))
            self.table.setItem(i, 1, cell(c.get('apt_nombre', '') or ''))
            self.table.setItem(i, 2, cell((c.get('inq_nombre', '') or '').strip()))
            self.table.setItem(i, 3, cell(c.get('fecha_inicio', '') or ''))
            self.table.setItem(i, 4, cell(c.get('fecha_fin', '') or 'Indefinido'))
            self.table.setItem(i, 5, cell(eur(c.get('alquiler_mensual', 0)), Qt.AlignRight | Qt.AlignVCenter))
            self.table.setItem(i, 6, cell(eur(c.get('deposito', 0)), Qt.AlignRight | Qt.AlignVCenter))
            self.table.setItem(i, 7, cell(f"Día {c.get('dia_pago', 1)}", Qt.AlignCenter))

            estado = c.get('estado', 'activo')
            s_item = QTableWidgetItem(estado.capitalize())
            s_item.setTextAlignment(Qt.AlignCenter)
            bg, fg = ESTADO_COLORS.get(estado, ('#FFFFFF', '#000000'))
            s_item.setBackground(QColor(bg)); s_item.setForeground(QColor(fg))
            f = QFont(); f.setBold(True); s_item.setFont(f)
            self.table.setItem(i, 8, s_item)

        activos = sum(1 for c in self._all if c.get('estado') == 'activo')
        self.summary_lbl.setText(
            f"Total: {len(self._all)}  |  Activos: {activos}"
        )

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _add(self):
        dlg = ContratoDialog(self.db, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load()

    def _edit(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un contrato.")
            return
        c = self.db.get_contrato(id_)
        if c:
            dlg = ContratoDialog(self.db, c, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self._load()

    def _gen_pago(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un contrato activo.")
            return
        c = self.db.get_contrato(id_)
        if not c or c.get('estado') != 'activo':
            QMessageBox.warning(self, "Aviso", "Solo se pueden generar pagos para contratos activos.")
            return
        dlg = GenerarPagoDialog(self.db, c, parent=self)
        dlg.exec()

    def _delete(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un contrato.")
            return
        c = self.db.get_contrato(id_)
        info = f"Apartamento: {c.get('apt_nombre','')}, Inquilino: {c.get('inq_nombre','').strip()}" if c else ''
        if QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar el contrato?\n{info}\nSe eliminarán también sus pagos.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            self.db.delete_contrato(id_)
            self._load()

    def refresh(self):
        self._load()


class ContratoDialog(QDialog):
    def __init__(self, db, item=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.item = item
        self.setWindowTitle("Editar Contrato" if item else "Nuevo Contrato")
        self.setMinimumWidth(500)
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

        # Apartment selector
        self.apt_cb = QComboBox()
        self._apts = self.db.get_apartamentos()
        for a in self._apts:
            self.apt_cb.addItem(f"{a['nombre']} ({a.get('estado','')}) — {a.get('direccion','')}", a['id'])
        form.addRow("Apartamento *:", self.apt_cb)

        # Tenant selector
        self.inq_cb = QComboBox()
        self._inqs = self.db.get_inquilinos()
        for inq in self._inqs:
            self.inq_cb.addItem(
                f"{inq.get('apellidos','')} {inq['nombre']} — {inq.get('telefono','')}".strip(),
                inq['id']
            )
        form.addRow("Inquilino *:", self.inq_cb)

        today = QDate.currentDate()

        self.f_inicio = QDateEdit()
        self.f_inicio.setDate(today)
        self.f_inicio.setCalendarPopup(True)
        self.f_inicio.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha inicio *:", self.f_inicio)

        self.f_fin = QDateEdit()
        self.f_fin.setDate(today.addYears(1))
        self.f_fin.setCalendarPopup(True)
        self.f_fin.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha fin:", self.f_fin)

        self.alquiler = QDoubleSpinBox()
        self.alquiler.setRange(0, 99999); self.alquiler.setSuffix(" €/mes"); self.alquiler.setDecimals(2)
        form.addRow("Alquiler mensual *:", self.alquiler)

        self.deposito = QDoubleSpinBox()
        self.deposito.setRange(0, 99999); self.deposito.setSuffix(" €"); self.deposito.setDecimals(2)
        form.addRow("Depósito:", self.deposito)

        self.dia_pago = QSpinBox()
        self.dia_pago.setRange(1, 31); self.dia_pago.setValue(1)
        self.dia_pago.setSuffix("  (día del mes)")
        form.addRow("Día de pago:", self.dia_pago)

        self.estado = QComboBox()
        self.estado.addItems(["activo", "finalizado", "rescindido"])
        form.addRow("Estado:", self.estado)

        self.notas = QTextEdit(); self.notas.setMaximumHeight(72)
        self.notas.setPlaceholderText("Notas del contrato...")
        form.addRow("Notas:", self.notas)

        lay.addLayout(form)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8); btn_row.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setStyleSheet("background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        cancel.setFixedHeight(32); cancel.clicked.connect(self.reject)
        save = QPushButton("💾  Guardar")
        save.setFixedHeight(32); save.clicked.connect(self._save)
        btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _populate(self, d):
        for i in range(self.apt_cb.count()):
            if self.apt_cb.itemData(i) == d.get('apartamento_id'):
                self.apt_cb.setCurrentIndex(i); break
        for i in range(self.inq_cb.count()):
            if self.inq_cb.itemData(i) == d.get('inquilino_id'):
                self.inq_cb.setCurrentIndex(i); break
        if d.get('fecha_inicio'):
            self.f_inicio.setDate(QDate.fromString(d['fecha_inicio'], "yyyy-MM-dd"))
        if d.get('fecha_fin'):
            self.f_fin.setDate(QDate.fromString(d['fecha_fin'], "yyyy-MM-dd"))
        self.alquiler.setValue(d.get('alquiler_mensual', 0) or 0)
        self.deposito.setValue(d.get('deposito', 0) or 0)
        self.dia_pago.setValue(d.get('dia_pago', 1) or 1)
        idx = self.estado.findText(d.get('estado', 'activo'))
        self.estado.setCurrentIndex(max(0, idx))
        self.notas.setPlainText(d.get('notas', '') or '')

    def _save(self):
        if self.alquiler.value() <= 0:
            QMessageBox.warning(self, "Campo requerido", "El alquiler mensual debe ser mayor que 0.")
            return
        d = {
            'apartamento_id': self.apt_cb.currentData(),
            'inquilino_id': self.inq_cb.currentData(),
            'fecha_inicio': self.f_inicio.date().toString("yyyy-MM-dd"),
            'fecha_fin': self.f_fin.date().toString("yyyy-MM-dd"),
            'alquiler_mensual': self.alquiler.value(),
            'deposito': self.deposito.value(),
            'dia_pago': self.dia_pago.value(),
            'estado': self.estado.currentText(),
            'notas': self.notas.toPlainText().strip(),
        }
        if self.item:
            self.db.update_contrato(self.item['id'], d)
        else:
            self.db.add_contrato(d)
        self.accept()


class GenerarPagoDialog(QDialog):
    def __init__(self, db, contrato, parent=None):
        super().__init__(parent)
        self.db = db
        self.contrato = contrato
        self.setWindowTitle("Generar Pago")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(14)

        info = QLabel(
            f"<b>Apartamento:</b> {self.contrato.get('apt_nombre','')}<br>"
            f"<b>Inquilino:</b> {(self.contrato.get('inq_nombre','') or '').strip()}<br>"
            f"<b>Alquiler:</b> {self.contrato.get('alquiler_mensual',0):.2f} €"
        )
        info.setStyleSheet("background:#EEF2F7; padding:10px; border-radius:6px;")
        lay.addWidget(info)

        form = QFormLayout(); form.setSpacing(9); form.setLabelAlignment(Qt.AlignRight)

        today = date.today()
        self.mes_cb = QComboBox()
        MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                 "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        for m in MESES:
            self.mes_cb.addItem(m)
        self.mes_cb.setCurrentIndex(today.month - 1)
        form.addRow("Mes:", self.mes_cb)

        self.anyo = QSpinBox(); self.anyo.setRange(2000, 2100); self.anyo.setValue(today.year)
        form.addRow("Año:", self.anyo)

        self.importe = QDoubleSpinBox()
        self.importe.setRange(0, 99999); self.importe.setSuffix(" €"); self.importe.setDecimals(2)
        self.importe.setValue(self.contrato.get('alquiler_mensual', 0) or 0)
        form.addRow("Importe:", self.importe)

        dia = self.contrato.get('dia_pago', 1) or 1
        self.f_venc = QDateEdit()
        self.f_venc.setCalendarPopup(True)
        self.f_venc.setDisplayFormat("dd/MM/yyyy")
        try:
            venc = QDate(today.year, today.month, min(dia, 28))
        except Exception:
            venc = QDate.currentDate()
        self.f_venc.setDate(venc)
        form.addRow("Vencimiento:", self.f_venc)

        lay.addLayout(form)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8); btn_row.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setStyleSheet("background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        cancel.setFixedHeight(32); cancel.clicked.connect(self.reject)
        gen = QPushButton("✅  Generar Pago")
        gen.setFixedHeight(32); gen.clicked.connect(self._generate)
        btn_row.addWidget(cancel); btn_row.addWidget(gen)
        lay.addLayout(btn_row)

    def _generate(self):
        d = {
            'contrato_id': self.contrato['id'],
            'mes': self.mes_cb.currentIndex() + 1,
            'anyo': self.anyo.value(),
            'importe': self.importe.value(),
            'fecha_vencimiento': self.f_venc.date().toString("yyyy-MM-dd"),
            'tipo': 'alquiler',
            'estado': 'pendiente',
        }
        self.db.add_pago(d)
        QMessageBox.information(self, "Pago creado",
            f"Pago de {d['importe']:.2f} € generado para "
            f"{['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][d['mes']-1]} {d['anyo']}.")
        self.accept()
