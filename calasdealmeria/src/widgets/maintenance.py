from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox,
    QTextEdit, QMessageBox, QDateEdit, QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from datetime import date


ESTADO_COLORS = {
    'pendiente':   ('#FFF3CD', '#856404'),
    'en_proceso':  ('#CCE5FF', '#004085'),
    'completado':  ('#D4EDDA', '#155724'),
}

PRIORIDAD_COLORS = {
    'baja':     ("#C6CFC8", '#155724'),
    'media':    ('#FFF3CD', '#856404'),
    'alta':     ('#FFE0B2', '#7B3F00'),
    'urgente':  ('#F8D7DA', '#721C24'),
}


class MantenimientoWidget(QWidget):
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
        self.estado_cb = QComboBox(); self.estado_cb.setFixedWidth(130)
        self.estado_cb.addItems(["Todos", "Pendiente", "En proceso", "Completado"])
        self.estado_cb.currentTextChanged.connect(self._load)
        bar.addWidget(self.estado_cb)

        bar.addWidget(QLabel("Prioridad:"))
        self.prioridad_cb = QComboBox(); self.prioridad_cb.setFixedWidth(120)
        self.prioridad_cb.addItems(["Todas", "Urgente", "Alta", "Media", "Baja"])
        self.prioridad_cb.currentTextChanged.connect(self._filter)
        bar.addWidget(self.prioridad_cb)

        bar.addWidget(QLabel("Buscar:"))
        self.search = QLineEdit(); self.search.setPlaceholderText("Título, apartamento, proveedor...")
        self.search.setFixedWidth(240); self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search)

        bar.addStretch()
        add_btn = QPushButton("＋  Nueva Incidencia")
        add_btn.setFixedHeight(32); add_btn.clicked.connect(self._add)
        bar.addWidget(add_btn)
        lay.addLayout(bar)

        # Stats strip
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px;")
        sf_lay = QHBoxLayout(stats_frame)
        sf_lay.setContentsMargins(16, 8, 16, 8); sf_lay.setSpacing(20)
        self.lbl_pendientes = QLabel("Pendientes: 0")
        self.lbl_pendientes.setStyleSheet("color:#856404; font-weight:bold;")
        self.lbl_proceso = QLabel("En proceso: 0")
        self.lbl_proceso.setStyleSheet("color:#004085; font-weight:bold;")
        self.lbl_completados = QLabel("Completados: 0")
        self.lbl_completados.setStyleSheet("color:#155724; font-weight:bold;")
        self.lbl_urgentes = QLabel("Urgentes/Alta: 0")
        self.lbl_urgentes.setStyleSheet("color:#721C24; font-weight:bold;")
        for lbl in [self.lbl_pendientes, self.lbl_proceso, self.lbl_completados, self.lbl_urgentes]:
            sf_lay.addWidget(lbl)
        sf_lay.addStretch()
        lay.addWidget(stats_frame)

        # Table
        self.table = QTableWidget()
        cols = ["ID", "Apartamento", "Título", "Prioridad", "Estado",
                "Coste", "Fecha Reporte", "Completado", "Proveedor"]
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
        complete_btn = QPushButton("✅  Marcar Completado")
        complete_btn.setStyleSheet("background-color:#38A169; color:white; border:none;")
        complete_btn.setFixedHeight(32); complete_btn.clicked.connect(self._mark_complete)

        edit_btn = QPushButton("✏  Editar")
        edit_btn.setStyleSheet("background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        edit_btn.setFixedHeight(32); edit_btn.clicked.connect(self._edit)

        del_btn = QPushButton("🗑  Eliminar")
        del_btn.setStyleSheet("background-color:#E53E3E; color:white; border:none;")
        del_btn.setFixedHeight(32); del_btn.clicked.connect(self._delete)

        actions.addWidget(complete_btn); actions.addWidget(edit_btn); actions.addWidget(del_btn)
        actions.addStretch()
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("color:#718096; font-size:12px;")
        actions.addWidget(self.count_lbl)
        lay.addLayout(actions)

    def _load(self):
        estado_text = self.estado_cb.currentText().lower().replace(' ', '_')
        estado = None if estado_text in ('todos', '') else estado_text
        # Fix "en proceso" → "en_proceso"
        if estado == 'en_proceso':
            estado = 'en_proceso'
        self._all = self.db.get_mantenimiento(estado=estado)
        self._update_stats()
        self._filter()

    def _update_stats(self):
        s = self.db.get_stats_mantenimiento()
        self.lbl_pendientes.setText(f"Pendientes: {s.get('pendientes', 0)}")
        self.lbl_proceso.setText(f"En proceso: {s.get('en_proceso', 0)}")
        self.lbl_completados.setText(f"Completados: {s.get('completados', 0)}")
        self.lbl_urgentes.setText(f"Urgentes/Alta: {s.get('urgentes', 0)}")

    def _filter(self):
        text = self.search.text().lower()
        prioridad = self.prioridad_cb.currentText().lower()
        if prioridad == "todas":
            prioridad = ""

        filtered = []
        for m in self._all:
            if prioridad and m.get('prioridad', '').lower() != prioridad:
                continue
            if text and text not in f"{m.get('titulo','')} {m.get('apt_nombre','')} {m.get('proveedor','')}".lower():
                continue
            filtered.append(m)
        self._populate(filtered)

    def _populate(self, data):
        self.table.setRowCount(len(data))
        for i, m in enumerate(data):
            def cell(v, align=Qt.AlignVCenter | Qt.AlignLeft):
                item = QTableWidgetItem(str(v) if v is not None else '')
                item.setTextAlignment(align)
                return item

            self.table.setItem(i, 0, cell(m['id'], Qt.AlignCenter))
            self.table.setItem(i, 1, cell(m.get('apt_nombre', '') or 'General'))
            self.table.setItem(i, 2, cell(m.get('titulo', '')))

            pri = m.get('prioridad', 'media')
            pri_item = QTableWidgetItem(pri.capitalize())
            pri_item.setTextAlignment(Qt.AlignCenter)
            pbg, pfg = PRIORIDAD_COLORS.get(pri, ('#FFFFFF', '#000000'))
            pri_item.setBackground(QColor(pbg)); pri_item.setForeground(QColor(pfg))
            f = QFont(); f.setBold(True); pri_item.setFont(f)
            self.table.setItem(i, 3, pri_item)

            estado = m.get('estado', 'pendiente')
            est_item = QTableWidgetItem(estado.replace('_', ' ').capitalize())
            est_item.setTextAlignment(Qt.AlignCenter)
            ebg, efg = ESTADO_COLORS.get(estado, ('#FFFFFF', '#000000'))
            est_item.setBackground(QColor(ebg)); est_item.setForeground(QColor(efg))
            f2 = QFont(); f2.setBold(True); est_item.setFont(f2)
            self.table.setItem(i, 4, est_item)

            coste = m.get('coste', 0) or 0
            coste_str = f"{coste:.2f} €".replace('.', ',') if coste else ''
            self.table.setItem(i, 5, cell(coste_str, Qt.AlignRight | Qt.AlignVCenter))
            self.table.setItem(i, 6, cell(m.get('fecha_reporte', '') or ''))
            self.table.setItem(i, 7, cell(m.get('fecha_completado', '') or '—'))
            self.table.setItem(i, 8, cell(m.get('proveedor', '') or ''))

        total_coste = sum(m.get('coste', 0) or 0 for m in data)
        coste_str = f"{total_coste:.2f} €".replace('.', ',')
        self.count_lbl.setText(f"Mostrando: {len(data)} | Coste total: {coste_str}")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _mark_complete(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona una incidencia.")
            return
        conn = self.db._conn()
        conn.execute(
            "UPDATE mantenimiento SET estado='completado', fecha_completado=? WHERE id=?",
            (str(date.today()), id_)
        )
        conn.commit(); conn.close()
        self._load()

    def _add(self):
        dlg = MantenimientoDialog(self.db, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load()

    def _edit(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona una incidencia.")
            return
        items = self.db.get_mantenimiento()
        m = next((x for x in items if x['id'] == id_), None)
        if m:
            dlg = MantenimientoDialog(self.db, m, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self._load()

    def _delete(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona una incidencia.")
            return
        if QMessageBox.question(
            self, "Confirmar", "¿Eliminar esta incidencia de mantenimiento?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            self.db.delete_mantenimiento(id_)
            self._load()

    def refresh(self):
        self._load()


class MantenimientoDialog(QDialog):
    def __init__(self, db, item=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.item = item
        self.setWindowTitle("Editar Incidencia" if item else "Nueva Incidencia")
        self.setMinimumWidth(500)
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
        self.apt_cb.addItem("— General / Sin apartamento específico —", None)
        for a in self.db.get_apartamentos():
            self.apt_cb.addItem(f"{a['nombre']} — {a.get('direccion','')}", a['id'])
        form.addRow("Apartamento:", self.apt_cb)

        self.titulo = QLineEdit(); self.titulo.setPlaceholderText("Descripción breve del problema")
        form.addRow("Título *:", self.titulo)

        self.descripcion = QTextEdit(); self.descripcion.setMaximumHeight(80)
        self.descripcion.setPlaceholderText("Detalle del problema, síntomas, ubicación exacta...")
        form.addRow("Descripción:", self.descripcion)

        self.prioridad = QComboBox()
        self.prioridad.addItems(["urgente", "alta", "media", "baja"])
        self.prioridad.setCurrentIndex(2)
        form.addRow("Prioridad:", self.prioridad)

        self.estado = QComboBox()
        self.estado.addItems(["pendiente", "en_proceso", "completado"])
        form.addRow("Estado:", self.estado)

        self.coste = QDoubleSpinBox()
        self.coste.setRange(0, 999999); self.coste.setSuffix(" €"); self.coste.setDecimals(2)
        form.addRow("Coste (€):", self.coste)

        self.proveedor = QLineEdit(); self.proveedor.setPlaceholderText("Nombre del técnico o empresa")
        form.addRow("Proveedor:", self.proveedor)

        self.f_reporte = QDateEdit()
        self.f_reporte.setDate(QDate.currentDate())
        self.f_reporte.setCalendarPopup(True); self.f_reporte.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha reporte:", self.f_reporte)

        self.f_completado = QDateEdit()
        self.f_completado.setDate(QDate.currentDate())
        self.f_completado.setCalendarPopup(True); self.f_completado.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha completado:", self.f_completado)

        self.notas = QTextEdit(); self.notas.setMaximumHeight(60)
        self.notas.setPlaceholderText("Notas adicionales...")
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
        self.titulo.setText(d.get('titulo', ''))
        self.descripcion.setPlainText(d.get('descripcion', '') or '')
        idx = self.prioridad.findText(d.get('prioridad', 'media'))
        self.prioridad.setCurrentIndex(max(0, idx))
        idx = self.estado.findText(d.get('estado', 'pendiente'))
        self.estado.setCurrentIndex(max(0, idx))
        self.coste.setValue(d.get('coste', 0) or 0)
        self.proveedor.setText(d.get('proveedor', '') or '')
        if d.get('fecha_reporte'):
            self.f_reporte.setDate(QDate.fromString(d['fecha_reporte'], "yyyy-MM-dd"))
        if d.get('fecha_completado'):
            self.f_completado.setDate(QDate.fromString(d['fecha_completado'], "yyyy-MM-dd"))
        self.notas.setPlainText(d.get('notas', '') or '')

    def _save(self):
        if not self.titulo.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El título es obligatorio.")
            return
        estado = self.estado.currentText()
        fecha_completado = (self.f_completado.date().toString("yyyy-MM-dd")
                            if estado == 'completado' else None)
        d = {
            'apartamento_id': self.apt_cb.currentData(),
            'titulo': self.titulo.text().strip(),
            'descripcion': self.descripcion.toPlainText().strip(),
            'prioridad': self.prioridad.currentText(),
            'estado': estado,
            'coste': self.coste.value() or 0,
            'proveedor': self.proveedor.text().strip(),
            'fecha_reporte': self.f_reporte.date().toString("yyyy-MM-dd"),
            'fecha_completado': fecha_completado,
            'notas': self.notas.toPlainText().strip(),
        }
        if self.item:
            self.db.update_mantenimiento(self.item['id'], d)
        else:
            self.db.add_mantenimiento(d)
        self.accept()
