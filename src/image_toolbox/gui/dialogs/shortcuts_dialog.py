"""Klavye Kısayolları Diyaloğu (Shortcuts Dialog)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from image_toolbox.core.i18n import _


class ShortcutsDialog(QDialog):
    """Kullanılabilir klavye kısayollarını gösteren diyalog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(_("action_shortcuts"))
        self.resize(460, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Kısayol Tuşu", "İşlev"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        shortcuts = [
            ("Ctrl + O", "Görsel Dosyası Aç"),
            ("Ctrl + S", "İşlenmiş Görseli Farklı Kaydet"),
            ("Ctrl + W", "Mevcut Görseli Kapat"),
            ("Ctrl + R", "Orijinal Görsele Sıfırla"),
            ("Ctrl + +", "Görseli Yakınlaştır (Zoom In)"),
            ("Ctrl + -", "Görseli Uzaklaştır (Zoom Out)"),
            ("Ctrl + 0", "Pencereye Sığdır"),
            ("Ctrl + Q", "Uygulamadan Çık"),
        ]

        for key, desc in shortcuts:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(key))
            table.setItem(row, 1, QTableWidgetItem(desc))

        layout.addWidget(table)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
