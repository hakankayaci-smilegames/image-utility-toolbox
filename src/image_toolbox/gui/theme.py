"""Pro Creative Studio / Darkroom Minimalist Nötr Koyu Tema (QSS).

Adobe Lightroom, DaVinci Resolve ve Apple Pro standartlarında nötr kömür/grafit
ve çinko paleti. Sıfır mor/lacivert yapay zeka klişesi, profesyonel stüdyo estetiği.
"""

from __future__ import annotations


DARK_THEME_QSS = """
/* Genel Zemin ve Tipografi (Neutral Charcoal / Zinc) */
QMainWindow, QDialog, QWidget {
    background-color: #121214;
    color: #EDEDEF;
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* Menü Çubuğu */
QMenuBar {
    background-color: #18181B;
    color: #EDEDEF;
    border-bottom: 1px solid #27272A;
    padding: 3px 6px;
    font-weight: 500;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #27272A;
    color: #FFFFFF;
}
QMenu {
    background-color: #18181B;
    color: #EDEDEF;
    border: 1px solid #2E2E33;
    border-radius: 6px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #27272A;
    color: #FFFFFF;
}
QMenu::separator {
    height: 1px;
    background-color: #27272A;
    margin: 4px 8px;
}

/* Durum Çubuğu (Status Bar) */
QStatusBar {
    background-color: #161618;
    color: #A1A1AA;
    border-top: 1px solid #27272A;
    font-size: 12px;
}
QStatusBar QLabel {
    color: #A1A1AA;
    padding: 3px 8px;
}

/* Sekmeler (QTabWidget) - Üst Düzey Nötr Tasarım */
QTabWidget::pane {
    border: 1px solid #27272A;
    background-color: #18181B;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background-color: #121214;
    color: #8E8E93;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    padding: 8px 14px;
    margin-right: 2px;
    font-weight: 500;
    font-size: 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #18181B;
    color: #FFFFFF;
    border-top: 1px solid #27272A;
    border-left: 1px solid #27272A;
    border-right: 1px solid #27272A;
    border-bottom: 2px solid #3B82F6;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    color: #D4D4D8;
    background-color: #161618;
}

/* Kartlar ve Paneller (QGroupBox / QFrame) */
QGroupBox {
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: 1px solid #27272A;
    border-radius: 6px;
    margin-top: 18px;
    padding: 14px;
    background-color: #18181B;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #A1A1AA;
}

/* Butonlar */
QPushButton {
    background-color: #222226;
    color: #EDEDEF;
    border: 1px solid #333338;
    border-radius: 5px;
    padding: 7px 14px;
    font-weight: 500;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #2A2A30;
    border-color: #44444C;
    color: #FFFFFF;
}
QPushButton:pressed {
    background-color: #1A1A1D;
}
QPushButton:disabled {
    background-color: #161618;
    color: #52525B;
    border-color: #222225;
}

/* Birincil Aksiyon Butonu (Pro Studio Accent - Cobalt / Neutral Highlight) */
QPushButton[primary="true"] {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    font-weight: 600;
}
QPushButton[primary="true"]:hover {
    background-color: #3B82F6;
    border-color: #60A5FA;
}
QPushButton[primary="true"]:pressed {
    background-color: #1D4ED8;
}

/* Girdi Kutuları, SpinBox ve ComboBox */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #121214;
    color: #EDEDEF;
    border: 1px solid #333338;
    border-radius: 5px;
    padding: 6px 10px;
    selection-background-color: #3B82F6;
    selection-color: #FFFFFF;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #3B82F6;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #18181B;
    color: #EDEDEF;
    border: 1px solid #27272A;
    selection-background-color: #27272A;
    selection-color: #FFFFFF;
    padding: 4px;
}

/* Kaydırma Çubukları (QSlider) */
QSlider::groove:horizontal {
    height: 4px;
    background: #27272A;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #3B82F6;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #EDEDEF;
    border: 1px solid #27272A;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: #FFFFFF;
    border-color: #3B82F6;
}

/* İlerleme Çubuğu (QProgressBar) */
QProgressBar {
    border: 1px solid #27272A;
    border-radius: 4px;
    background-color: #121214;
    text-align: center;
    color: #A1A1AA;
    font-weight: 600;
    font-size: 11px;
    height: 12px;
}
QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 3px;
}

/* CheckBox ve RadioButton */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #EDEDEF;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3E3E44;
    border-radius: 4px;
    background-color: #121214;
}
QRadioButton::indicator {
    border-radius: 8px;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #3B82F6;
    border-color: #60A5FA;
}

/* Tablolar ve Listeler */
QTableWidget, QListWidget {
    background-color: #121214;
    color: #EDEDEF;
    border: 1px solid #27272A;
    border-radius: 5px;
    gridline-color: #1E1E22;
}
QHeaderView::section {
    background-color: #18181B;
    color: #8E8E93;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #27272A;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}

/* Kaydırma Çubuğu (QScrollBar) */
QScrollBar:vertical {
    background: #121214;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #27272A;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #3F3F46;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def apply_theme(app) -> None:
    """Uygulamaya nötr profesyonel stüdyo koyu temasını uygular."""
    app.setStyleSheet(DARK_THEME_QSS)
