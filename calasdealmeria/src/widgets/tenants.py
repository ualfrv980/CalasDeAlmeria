from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt


def make_btn(text, style=''):
    btn = QPushButton(text)
    if style:
        btn.setStyleSheet(style)
    btn.setFixedHeight(32)
    return btn


class InquilinosWidget(QWidget):
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
        bar.addWidget(QLabel("Buscar:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Nombre, apellidos, DNI, teléfono...")
        self.search.setFixedWidth(300)
        self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search)
        bar.addStretch()
        add_btn = QPushButton("＋  Añadir Inquilino")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._add)
        bar.addWidget(add_btn)
        lay.addLayout(bar)

        self.table = QTableWidget()
        cols = ["ID", "Apellidos", "Nombre", "DNI/NIE", "Teléfono", "Email", "Teléfono 2"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit)
        lay.addWidget(self.table)

        actions = QHBoxLayout(); actions.setSpacing(8)
        edit_btn = make_btn("✏  Editar",
                            "background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        edit_btn.clicked.connect(self._edit)
        del_btn = make_btn("🗑  Eliminar",
                           "background-color:#E53E3E; color:white; border:none;")
        del_btn.clicked.connect(self._delete)
        actions.addWidget(edit_btn)
        actions.addWidget(del_btn)
        actions.addStretch()
        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet("color:#718096; font-size:12px;")
        actions.addWidget(self.summary_lbl)
        lay.addLayout(actions)

    def _load(self):
        self._all = self.db.get_inquilinos()
        self._populate(self._all)

    def _populate(self, data):
        self.table.setRowCount(len(data))
        for i, inq in enumerate(data):
            def cell(v, align=Qt.AlignVCenter | Qt.AlignLeft):
                item = QTableWidgetItem(str(v) if v is not None else '')
                item.setTextAlignment(align)
                return item
            self.table.setItem(i, 0, cell(inq['id'], Qt.AlignCenter))
            self.table.setItem(i, 1, cell(inq.get('apellidos', '') or ''))
            self.table.setItem(i, 2, cell(inq.get('nombre', '')))
            self.table.setItem(i, 3, cell(inq.get('dni_nie', '') or ''))
            self.table.setItem(i, 4, cell(inq.get('telefono', '') or ''))
            self.table.setItem(i, 5, cell(inq.get('email', '') or ''))
            self.table.setItem(i, 6, cell(inq.get('telefono2', '') or ''))
        self.summary_lbl.setText(f"Total inquilinos: {len(self._all)}")

    def _filter(self):
        text = self.search.text().lower()
        if not text:
            self._populate(self._all)
            return
        filtered = [
            inq for inq in self._all
            if text in f"{inq.get('nombre','')} {inq.get('apellidos','')} "
                       f"{inq.get('dni_nie','')} {inq.get('telefono','')}".lower()
        ]
        self._populate(filtered)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _add(self):
        dlg = InquilinoDialog(self.db, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load()

    def _edit(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un inquilino.")
            return
        inq = self.db.get_inquilino(id_)
        if inq:
            dlg = InquilinoDialog(self.db, inq, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self._load()

    def _delete(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un inquilino.")
            return
        inq = self.db.get_inquilino(id_)
        nombre = f"{inq.get('nombre','')} {inq.get('apellidos','')}".strip() if inq else ''
        if QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar al inquilino «{nombre}»?\nSe eliminarán también sus contratos y pagos.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            self.db.delete_inquilino(id_)
            self._load()

    def refresh(self):
        self._load()


class InquilinoDialog(QDialog):
    def __init__(self, db, item=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.item = item
        self.setWindowTitle("Editar Inquilino" if item else "Nuevo Inquilino")
        self.setMinimumWidth(440)
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

        self.nombre = QLineEdit(); self.nombre.setPlaceholderText("Nombre(s)")
        form.addRow("Nombre *:", self.nombre)

        self.apellidos = QLineEdit(); self.apellidos.setPlaceholderText("Apellidos")
        form.addRow("Apellidos:", self.apellidos)

        self.dni = QLineEdit(); self.dni.setPlaceholderText("DNI, NIE o pasaporte")
        form.addRow("DNI/NIE:", self.dni)

        self.telefono = QLineEdit(); self.telefono.setPlaceholderText("+34 6XX XXX XXX")
        form.addRow("Teléfono:", self.telefono)

        self.telefono2 = QLineEdit(); self.telefono2.setPlaceholderText("Teléfono alternativo")
        form.addRow("Teléfono 2:", self.telefono2)

        self.email = QLineEdit(); self.email.setPlaceholderText("correo@ejemplo.com")
        form.addRow("Email:", self.email)

        self.notas = QTextEdit(); self.notas.setMaximumHeight(80)
        self.notas.setPlaceholderText("Notas sobre el inquilino...")
        form.addRow("Notas:", self.notas)

        lay.addLayout(form)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8); btn_row.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setStyleSheet("background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        cancel.setFixedHeight(32)
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾  Guardar")
        save.setFixedHeight(32)
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _populate(self, d):
        self.nombre.setText(d.get('nombre', ''))
        self.apellidos.setText(d.get('apellidos', '') or '')
        self.dni.setText(d.get('dni_nie', '') or '')
        self.telefono.setText(d.get('telefono', '') or '')
        self.telefono2.setText(d.get('telefono2', '') or '')
        self.email.setText(d.get('email', '') or '')
        self.notas.setPlainText(d.get('notas', '') or '')

    def _save(self):
        nombre = self.nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo requerido", "El nombre es obligatorio.")
            return
        d = {
            'nombre': nombre,
            'apellidos': self.apellidos.text().strip(),
            'dni_nie': self.dni.text().strip(),
            'telefono': self.telefono.text().strip(),
            'telefono2': self.telefono2.text().strip(),
            'email': self.email.text().strip(),
            'notas': self.notas.toPlainText().strip(),
        }
        if self.item:
            self.db.update_inquilino(self.item['id'], d)
        else:
            self.db.add_inquilino(d)
        self.accept()
