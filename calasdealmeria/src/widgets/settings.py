from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QFrame, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt


class ConfiguracionWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(20)
        lay.setAlignment(Qt.AlignTop)

        # ── Landlord info ──────────────────────────────────────
        group = QGroupBox("Datos del Arrendador")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px; font-weight: bold;
                border: 1px solid #CBD5E0; border-radius: 6px;
                margin-top: 8px; padding-top: 12px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 8px; color: #2D3748;
            }
        """)
        form = QFormLayout(group)
        form.setContentsMargins(20, 16, 20, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.nombre = QLineEdit(); self.nombre.setPlaceholderText("Nombre completo")
        form.addRow("Nombre / Razón Social:", self.nombre)

        self.nif = QLineEdit(); self.nif.setPlaceholderText("NIF / NIE / CIF")
        self.nif.setMaximumWidth(200)
        form.addRow("NIF / NIE:", self.nif)

        self.direccion = QLineEdit(); self.direccion.setPlaceholderText("Dirección fiscal completa")
        form.addRow("Dirección:", self.direccion)

        self.cp_ciudad = QLineEdit(); self.cp_ciudad.setPlaceholderText("Ej: 04001 Almería")
        self.cp_ciudad.setMaximumWidth(300)
        form.addRow("C.P. y Ciudad:", self.cp_ciudad)

        self.telefono = QLineEdit(); self.telefono.setPlaceholderText("+34 000 000 000")
        self.telefono.setMaximumWidth(220)
        form.addRow("Teléfono:", self.telefono)

        self.email = QLineEdit(); self.email.setPlaceholderText("correo@ejemplo.com")
        self.email.setMaximumWidth(320)
        form.addRow("Email:", self.email)

        lay.addWidget(group)

        # ── Save button ────────────────────────────────────────
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾  Guardar Configuración")
        save_btn.setFixedHeight(36)
        save_btn.setFixedWidth(240)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        # Info note
        note = QLabel(
            "Estos datos aparecerán en los recibos de arrendamiento generados desde la sección Pagos."
        )
        note.setStyleSheet("color: #718096; font-size: 12px;")
        note.setWordWrap(True)
        lay.addWidget(note)

        lay.addStretch()

    def _load(self):
        cfg = self.db.get_configuracion()
        self.nombre.setText(cfg.get('nombre_arrendador', ''))
        self.nif.setText(cfg.get('nif_arrendador', ''))
        self.direccion.setText(cfg.get('direccion_arrendador', ''))
        self.cp_ciudad.setText(cfg.get('cp_ciudad_arrendador', ''))
        self.telefono.setText(cfg.get('telefono_arrendador', ''))
        self.email.setText(cfg.get('email_arrendador', ''))

    def _save(self):
        self.db.set_configuracion({
            'nombre_arrendador': self.nombre.text().strip(),
            'nif_arrendador': self.nif.text().strip(),
            'direccion_arrendador': self.direccion.text().strip(),
            'cp_ciudad_arrendador': self.cp_ciudad.text().strip(),
            'telefono_arrendador': self.telefono.text().strip(),
            'email_arrendador': self.email.text().strip(),
        })
        QMessageBox.information(self, "Guardado", "Configuración guardada correctamente.")

    def refresh(self):
        self._load()
