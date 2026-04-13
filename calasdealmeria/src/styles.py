def get_stylesheet() -> str:
    return """
    QMainWindow {
        background-color: #EEF2F7;
    }

    * {
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #1A202C;
    }

    /* ===== SIDEBAR ===== */
    #sidebar {
        background-color: #1A2F4E;
        border-right: 1px solid #0F1F33;
    }
    #sidebarHeader {
        background-color: #0F1F33;
    }
    #logoTitle {
        color: #FFFFFF;
        font-size: 14px;
        font-weight: bold;
    }
    #logoSubtitle {
        color: #7A99B8;
        font-size: 10px;
    }
    #sidebarSectionLabel {
        color: #4A6480;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    #sidebarVersion {
        color: #4A6480;
        font-size: 10px;
    }
    QPushButton#sidebarButton {
        background-color: transparent;
        color: #A0BAD0;
        border: none;
        border-left: 3px solid transparent;
        text-align: left;
        padding: 0px 14px;
        font-size: 13px;
        border-radius: 0px;
    }
    QPushButton#sidebarButton:hover {
        background-color: #253D58;
        color: #FFFFFF;
    }
    QPushButton#sidebarButton:checked {
        background-color: #1E4976;
        color: #FFFFFF;
        border-left: 3px solid #F6AD55;
        font-weight: bold;
    }

    /* ===== TOP BAR ===== */
    #topbar {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
    }
    #pageTitle {
        color: #1A202C;
        font-size: 18px;
        font-weight: bold;
    }

    /* ===== CONTENT ===== */
    #contentArea {
        background-color: #EEF2F7;
    }
    QStackedWidget {
        background-color: #EEF2F7;
    }

    /* ===== TABLES ===== */
    QTableWidget {
        background-color: #FFFFFF;
        gridline-color: #EDF2F7;
        selection-background-color: #D6EAF8;
        selection-color: #1A202C;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        font-size: 13px;
        outline: none;
    }
    QTableWidget::item {
        padding: 5px 8px;
        border: none;
    }
    QTableWidget::item:selected {
        background-color: #D6EAF8;
        color: #1A202C;
    }
    QHeaderView::section {
        background-color: #F0F4F8;
        color: #4A5568;
        font-weight: bold;
        font-size: 11px;
        padding: 7px 8px;
        border: none;
        border-bottom: 2px solid #CBD5E0;
        border-right: 1px solid #E2E8F0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    QTableWidget::item:alternate {
        background-color: #F7FAFC;
    }

    /* ===== BUTTONS ===== */
    QPushButton {
        background-color: #2B6CB0;
        color: white;
        border: none;
        padding: 7px 16px;
        border-radius: 5px;
        font-size: 13px;
        font-weight: bold;
        min-height: 30px;
    }
    QPushButton:hover {
        background-color: #2C5282;
    }
    QPushButton:pressed {
        background-color: #1A365D;
    }
    QPushButton:disabled {
        background-color: #A0AEC0;
        color: #EDF2F7;
    }
    QPushButton.secondary {
        background-color: #EDF2F7;
        color: #2D3748;
        border: 1px solid #CBD5E0;
    }
    QPushButton.secondary:hover {
        background-color: #E2E8F0;
    }
    QPushButton.danger {
        background-color: #E53E3E;
        color: white;
        border: none;
    }
    QPushButton.danger:hover {
        background-color: #C53030;
    }
    QPushButton.success {
        background-color: #38A169;
        color: white;
        border: none;
    }
    QPushButton.success:hover {
        background-color: #2F855A;
    }
    QPushButton.warning {
        background-color: #D69E2E;
        color: white;
        border: none;
    }
    QPushButton.warning:hover {
        background-color: #B7791F;
    }

    /* ===== INPUTS ===== */
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E0;
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 13px;
        color: #1A202C;
        min-height: 28px;
    }
    QTextEdit {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E0;
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 13px;
        color: #1A202C;
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
    QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
        border: 2px solid #3182CE;
    }
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    QAbstractItemView {
        background-color: #FFFFFF;
        color: #1A202C;
        border: 1px solid #CBD5E0;
        selection-background-color: #BEE3F8;
        selection-color: #1A202C;
        font-size: 13px;
        outline: none;
    }

    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #1A202C;
        border: 1px solid #CBD5E0;
        selection-background-color: #BEE3F8;
        selection-color: #1A202C;
        font-size: 13px;
    }
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
        width: 20px;
    }

    /* ===== DIALOGS ===== */
    QDialog {
        background-color: #F7FAFC;
        color: #1A202C;
    }

    /* ===== LABELS ===== */
    QLabel {
        background-color: transparent;
        color: #1A202C;
        font-size: 13px;
    }

    /* ===== FORM LAYOUT LABELS ===== */
    QFormLayout QLabel {
        color: #2D3748;
        font-size: 13px;
        background-color: transparent;
    }

    /* ===== SCROLLBARS ===== */
    QScrollBar:vertical {
        background-color: #F0F4F8;
        width: 8px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background-color: #CBD5E0;
        min-height: 24px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #A0AEC0;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal {
        background-color: #F0F4F8;
        height: 8px;
    }
    QScrollBar::handle:horizontal {
        background-color: #CBD5E0;
        min-width: 24px;
        border-radius: 4px;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

    /* ===== STATUS BAR ===== */
    QStatusBar {
        background-color: #FFFFFF;
        color: #718096;
        font-size: 11px;
        border-top: 1px solid #E2E8F0;
    }

    /* ===== MESSAGE BOX ===== */
    QMessageBox {
        background-color: #F7FAFC;
    }
    QMessageBox QPushButton {
        min-width: 80px;
    }
    """
