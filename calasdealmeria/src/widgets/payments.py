from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QSpinBox, QDoubleSpinBox, QComboBox,
    QMessageBox, QDateEdit, QLineEdit, QFrame, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from datetime import date
import os
import subprocess
import sys


ESTADO_COLORS = {
    'pagado':    ('#D4EDDA', '#155724'),
    'pendiente': ('#FFF3CD', '#856404'),
    'retrasado': ('#F8D7DA', '#721C24'),
}

MESES_NOMBRE = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def fmt_eur(v):
    try:
        s = f"{float(v or 0):,.2f} €"
        return s.replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return "0,00 €"


class PagosWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._all = []
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(12)

        # Filters
        bar = QHBoxLayout(); bar.setSpacing(8)

        bar.addWidget(QLabel("Año:"))
        self.anyo_cb = QComboBox(); self.anyo_cb.setFixedWidth(80)
        yr = date.today().year
        for y in range(yr - 3, yr + 3):
            self.anyo_cb.addItem(str(y), y)
        self.anyo_cb.setCurrentText(str(yr))
        self.anyo_cb.currentIndexChanged.connect(self._load)
        bar.addWidget(self.anyo_cb)

        bar.addWidget(QLabel("Mes:"))
        self.mes_cb = QComboBox(); self.mes_cb.setFixedWidth(120)
        self.mes_cb.addItem("Todos", 0)
        for i, m in enumerate(MESES_NOMBRE, 1):
            self.mes_cb.addItem(m, i)
        self.mes_cb.setCurrentIndex(date.today().month)
        self.mes_cb.currentIndexChanged.connect(self._load)
        bar.addWidget(self.mes_cb)

        bar.addWidget(QLabel("Estado:"))
        self.estado_cb = QComboBox(); self.estado_cb.setFixedWidth(120)
        self.estado_cb.addItems(["Todos", "Pagado", "Pendiente", "Retrasado"])
        self.estado_cb.currentIndexChanged.connect(self._load)
        bar.addWidget(self.estado_cb)

        bar.addWidget(QLabel("Buscar:"))
        self.search = QLineEdit(); self.search.setPlaceholderText("Apartamento, inquilino...")
        self.search.setFixedWidth(200); self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search)

        bar.addStretch()
        add_btn = QPushButton("＋  Nuevo Pago")
        add_btn.setFixedHeight(32); add_btn.clicked.connect(self._add)
        bar.addWidget(add_btn)
        lay.addLayout(bar)

        # Summary strip
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet(
            "background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px;"
        )
        sf_lay = QHBoxLayout(self.summary_frame)
        sf_lay.setContentsMargins(16, 8, 16, 8); sf_lay.setSpacing(24)
        self.lbl_cobrado = QLabel("Cobrado: 0,00 €")
        self.lbl_cobrado.setStyleSheet("color:#38A169; font-weight:bold; font-size:13px;")
        self.lbl_pendiente = QLabel("Pendiente: 0,00 €")
        self.lbl_pendiente.setStyleSheet("color:#D69E2E; font-weight:bold; font-size:13px;")
        self.lbl_retrasado = QLabel("Retrasado: 0,00 €")
        self.lbl_retrasado.setStyleSheet("color:#E53E3E; font-weight:bold; font-size:13px;")
        for lbl in [self.lbl_cobrado, self.lbl_pendiente, self.lbl_retrasado]:
            sf_lay.addWidget(lbl)
        sf_lay.addStretch()
        lay.addWidget(self.summary_frame)

        # Table
        self.table = QTableWidget()
        cols = ["ID", "Apartamento", "Inquilino", "Mes", "Año", "Importe",
                "Vencimiento", "Fecha Pago", "Tipo", "Estado", "Método"]
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

        # Actions
        actions = QHBoxLayout(); actions.setSpacing(8)
        mark_btn = QPushButton("✅  Marcar Pagado")
        mark_btn.setStyleSheet("background-color:#38A169; color:white; border:none;")
        mark_btn.setFixedHeight(32); mark_btn.clicked.connect(self._mark_paid)

        edit_btn = QPushButton("✏  Editar")
        edit_btn.setStyleSheet("background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        edit_btn.setFixedHeight(32); edit_btn.clicked.connect(self._edit)

        del_btn = QPushButton("🗑  Eliminar")
        del_btn.setStyleSheet("background-color:#E53E3E; color:white; border:none;")
        del_btn.setFixedHeight(32); del_btn.clicked.connect(self._delete)

        receipt_btn = QPushButton("🧾  Generar Recibo PDF")
        receipt_btn.setStyleSheet("background-color:#6B46C1; color:white; border:none;")
        receipt_btn.setFixedHeight(32); receipt_btn.clicked.connect(self._generate_receipt)

        actions.addWidget(mark_btn); actions.addWidget(edit_btn); actions.addWidget(del_btn)
        actions.addWidget(receipt_btn)
        actions.addStretch()
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("color:#718096; font-size:12px;")
        actions.addWidget(self.count_lbl)
        lay.addLayout(actions)

    def _load(self):
        anyo = self.anyo_cb.currentData()
        mes = self.mes_cb.currentData()
        estado_text = self.estado_cb.currentText().lower()
        estado = None if estado_text == "todos" else estado_text
        self._all = self.db.get_pagos(
            anyo=anyo,
            mes=mes if mes else None,
            estado=estado
        )
        self._filter()

    def _filter(self):
        text = self.search.text().lower()
        if not text:
            self._populate(self._all)
            return
        filtered = [
            p for p in self._all
            if text in f"{p.get('apt_nombre','')} {p.get('inq_nombre','')}".lower()
        ]
        self._populate(filtered)

    def _populate(self, data):
        self.table.setRowCount(len(data))
        cobrado = pendiente = retrasado = 0.0
        for i, p in enumerate(data):
            def cell(v, align=Qt.AlignVCenter | Qt.AlignLeft):
                item = QTableWidgetItem(str(v) if v is not None else '')
                item.setTextAlignment(align)
                return item

            estado = p.get('estado', 'pendiente')
            importe = p.get('importe', 0) or 0
            if estado == 'pagado': cobrado += importe
            elif estado == 'pendiente': pendiente += importe
            elif estado == 'retrasado': retrasado += importe

            self.table.setItem(i, 0, cell(p['id'], Qt.AlignCenter))
            self.table.setItem(i, 1, cell(p.get('apt_nombre', '') or ''))
            self.table.setItem(i, 2, cell((p.get('inq_nombre', '') or '').strip()))
            mes = p.get('mes', 0) or 0
            self.table.setItem(i, 3, cell(MESES_NOMBRE[mes - 1] if 1 <= mes <= 12 else str(mes)))
            self.table.setItem(i, 4, cell(str(p.get('anyo', '')), Qt.AlignCenter))
            self.table.setItem(i, 5, cell(fmt_eur(importe), Qt.AlignRight | Qt.AlignVCenter))
            self.table.setItem(i, 6, cell(p.get('fecha_vencimiento', '') or ''))
            self.table.setItem(i, 7, cell(p.get('fecha_pago', '') or '—'))
            self.table.setItem(i, 8, cell(p.get('tipo', '').capitalize()))

            s_item = QTableWidgetItem(estado.capitalize())
            s_item.setTextAlignment(Qt.AlignCenter)
            bg, fg = ESTADO_COLORS.get(estado, ('#FFFFFF', '#000000'))
            s_item.setBackground(QColor(bg)); s_item.setForeground(QColor(fg))
            f = QFont(); f.setBold(True); s_item.setFont(f)
            self.table.setItem(i, 9, s_item)

            self.table.setItem(i, 10, cell(p.get('metodo', '') or ''))

        self.lbl_cobrado.setText(f"Cobrado: {fmt_eur(cobrado)}")
        self.lbl_pendiente.setText(f"Pendiente: {fmt_eur(pendiente)}")
        self.lbl_retrasado.setText(f"Retrasado: {fmt_eur(retrasado)}")
        self.count_lbl.setText(f"Total registros: {len(data)}")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _mark_paid(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un pago.")
            return
        dlg = MarcarPagadoDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.db.marcar_pagado(id_, dlg.fecha, dlg.metodo)
            self._load()

    def _add(self):
        dlg = PagoDialog(self.db, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load()

    def _edit(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un pago.")
            return
        pagos = self.db.get_pagos()
        p = next((x for x in pagos if x['id'] == id_), None)
        if p:
            dlg = PagoDialog(self.db, p, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self._load()

    def _delete(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un pago.")
            return
        if QMessageBox.question(
            self, "Confirmar", "¿Eliminar este registro de pago?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            self.db.delete_pago(id_)
            self._load()

    def _generate_receipt(self):
        id_ = self._selected_id()
        if id_ is None:
            QMessageBox.information(self, "Aviso", "Selecciona un pago para generar el recibo.")
            return

        # Get full payment data
        pagos = self.db.get_pagos()
        pago = next((p for p in pagos if p['id'] == id_), None)
        if not pago:
            return

        contrato = self.db.get_contrato(pago['contrato_id'])
        if not contrato:
            QMessageBox.warning(self, "Error", "No se encontro el contrato asociado.")
            return

        inquilino = self.db.get_inquilino(contrato['inquilino_id'])
        apartamento = self.db.get_apartamento(contrato['apartamento_id'])
        if not inquilino or not apartamento:
            QMessageBox.warning(self, "Error", "No se encontraron los datos del inquilino o apartamento.")
            return

        cfg = self.db.get_configuracion()

        # Suggest file name
        from src.invoice import MESES
        mes_num = pago.get('mes', 1) or 1
        mes_nombre = MESES[mes_num - 1] if 1 <= mes_num <= 12 else str(mes_num)
        anyo = pago.get('anyo', date.today().year)
        inq_apellido = (inquilino.get('apellidos', '') or inquilino.get('nombre', '')).replace(' ', '_')
        default_name = f"Recibo_{mes_nombre}_{anyo}_{inq_apellido}.pdf"

        docs_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        default_path = os.path.join(docs_dir, default_name)

        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar recibo PDF", default_path, "PDF (*.pdf)"
        )
        if not path:
            return

        try:
            from src.invoice import generate_receipt
            generate_receipt(pago, contrato, inquilino, apartamento, cfg, path)
        except ImportError as e:
            QMessageBox.critical(
                self, "Libreria no encontrada",
                str(e) + "\n\nInstala reportlab con:\n  pip install reportlab"
            )
            return
        except Exception as e:
            QMessageBox.critical(self, "Error al generar PDF", str(e))
            return

        reply = QMessageBox.question(
            self, "Recibo generado",
            f"Recibo guardado en:\n{path}\n\n¿Abrir el archivo ahora?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])

    def refresh(self):
        self._load()


class MarcarPagadoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Cobro")
        self.setMinimumWidth(320)
        self.setModal(True)
        self.fecha = ''
        self.metodo = ''
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(14)

        form = QFormLayout(); form.setSpacing(9); form.setLabelAlignment(Qt.AlignRight)

        self.f_pago = QDateEdit()
        self.f_pago.setDate(QDate.currentDate())
        self.f_pago.setCalendarPopup(True)
        self.f_pago.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha de cobro:", self.f_pago)

        self.metodo_cb = QComboBox()
        self.metodo_cb.addItems(["Efectivo", "Transferencia bancaria", "Bizum", "Cheque", "Otro"])
        form.addRow("Método de pago:", self.metodo_cb)
        lay.addLayout(form)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8); btn_row.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setStyleSheet("background-color:#EDF2F7; color:#2D3748; border:1px solid #CBD5E0;")
        cancel.setFixedHeight(32); cancel.clicked.connect(self.reject)
        ok = QPushButton("✅  Confirmar Cobro")
        ok.setStyleSheet("background-color:#38A169; color:white; border:none;")
        ok.setFixedHeight(32); ok.clicked.connect(self._confirm)
        btn_row.addWidget(cancel); btn_row.addWidget(ok)
        lay.addLayout(btn_row)

    def _confirm(self):
        self.fecha = self.f_pago.date().toString("yyyy-MM-dd")
        self.metodo = self.metodo_cb.currentText()
        self.accept()


class PagoDialog(QDialog):
    def __init__(self, db, item=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.item = item
        self.setWindowTitle("Editar Pago" if item else "Nuevo Pago")
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

        self.contrato_cb = QComboBox()
        self._contratos = self.db.get_contratos()
        for c in self._contratos:
            label = f"{c.get('apt_nombre','')} — {(c.get('inq_nombre','') or '').strip()} ({c.get('estado','')})"
            self.contrato_cb.addItem(label, c['id'])
        form.addRow("Contrato *:", self.contrato_cb)

        today = date.today()
        self.mes_cb = QComboBox()
        for m in MESES_NOMBRE:
            self.mes_cb.addItem(m)
        self.mes_cb.setCurrentIndex(today.month - 1)
        form.addRow("Mes:", self.mes_cb)

        self.anyo = QSpinBox(); self.anyo.setRange(2000, 2100); self.anyo.setValue(today.year)
        form.addRow("Año:", self.anyo)

        self.importe = QDoubleSpinBox()
        self.importe.setRange(0, 99999); self.importe.setSuffix(" €"); self.importe.setDecimals(2)
        form.addRow("Importe *:", self.importe)

        self.f_venc = QDateEdit(); self.f_venc.setDate(QDate.currentDate())
        self.f_venc.setCalendarPopup(True); self.f_venc.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Vencimiento:", self.f_venc)

        self.f_pago = QDateEdit(); self.f_pago.setDate(QDate.currentDate())
        self.f_pago.setCalendarPopup(True); self.f_pago.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha pago:", self.f_pago)

        self.tipo = QComboBox()
        self.tipo.addItems(["alquiler", "deposito", "extra", "devolucion"])
        form.addRow("Tipo:", self.tipo)

        self.estado = QComboBox()
        self.estado.addItems(["pendiente", "pagado", "retrasado"])
        form.addRow("Estado:", self.estado)

        self.metodo = QComboBox()
        self.metodo.addItems(["", "Efectivo", "Transferencia bancaria", "Bizum", "Cheque", "Otro"])
        form.addRow("Método:", self.metodo)

        self.notas = QLineEdit(); self.notas.setPlaceholderText("Notas...")
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
        for i in range(self.contrato_cb.count()):
            if self.contrato_cb.itemData(i) == d.get('contrato_id'):
                self.contrato_cb.setCurrentIndex(i); break
        mes = d.get('mes', 1) or 1
        self.mes_cb.setCurrentIndex(max(0, mes - 1))
        self.anyo.setValue(d.get('anyo', date.today().year) or date.today().year)
        self.importe.setValue(d.get('importe', 0) or 0)
        if d.get('fecha_vencimiento'):
            self.f_venc.setDate(QDate.fromString(d['fecha_vencimiento'], "yyyy-MM-dd"))
        if d.get('fecha_pago'):
            self.f_pago.setDate(QDate.fromString(d['fecha_pago'], "yyyy-MM-dd"))
        idx = self.tipo.findText(d.get('tipo', 'alquiler'))
        self.tipo.setCurrentIndex(max(0, idx))
        idx = self.estado.findText(d.get('estado', 'pendiente'))
        self.estado.setCurrentIndex(max(0, idx))
        idx = self.metodo.findText(d.get('metodo', ''))
        if idx >= 0: self.metodo.setCurrentIndex(idx)
        self.notas.setText(d.get('notas', '') or '')

    def _save(self):
        if self.importe.value() <= 0:
            QMessageBox.warning(self, "Campo requerido", "El importe debe ser mayor que 0.")
            return
        fecha_pago = self.f_pago.date().toString("yyyy-MM-dd") if self.estado.currentText() == 'pagado' else None
        d = {
            'contrato_id': self.contrato_cb.currentData(),
            'mes': self.mes_cb.currentIndex() + 1,
            'anyo': self.anyo.value(),
            'importe': self.importe.value(),
            'fecha_vencimiento': self.f_venc.date().toString("yyyy-MM-dd"),
            'fecha_pago': fecha_pago,
            'tipo': self.tipo.currentText(),
            'estado': self.estado.currentText(),
            'metodo': self.metodo.currentText(),
            'notas': self.notas.text().strip(),
        }
        if self.item:
            self.db.update_pago(self.item['id'], d)
        else:
            self.db.add_pago(d)
        self.accept()
