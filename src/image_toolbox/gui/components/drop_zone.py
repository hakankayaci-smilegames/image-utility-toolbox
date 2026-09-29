"""Sürükle & Bırak Karşılama Alanı (Drop Zone Component)."""

from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from image_toolbox.core.i18n import _


class DropZoneWidget(QFrame):
    """Görsel açılmamışken gösterilen modern sürükle-bırak karşılama bileşeni."""

    file_selected = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropZone")

        self.setStyleSheet("""
            #dropZone {
                border: 1px dashed #333338;
                border-radius: 8px;
                background-color: #151518;
            }
            #dropZone:hover {
                border-color: #3B82F6;
                background-color: #18181D;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)

        # Minimalist studio rozeti (Sıfır emoji, saf stüdyo tipografisi)
        badge_label = QLabel("CANVAS")
        badge_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            color: #71717A;
            border: 1px solid #27272A;
            border-radius: 4px;
            padding: 4px 10px;
            background-color: #18181B;
        """)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(badge_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Başlık
        self.title_label = QLabel(_("drop_zone_title"))
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #EDEDEF; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Alt açıklama
        self.sub_label = QLabel(_("drop_zone_sub"))
        self.sub_label.setStyleSheet("font-size: 13px; color: #8E8E93; background: transparent;")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_label)

        # Dosya Aç Butonu
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.open_btn = QPushButton(_("btn_open"))
        self.open_btn.setProperty("primary", True)
        self.open_btn.setFixedWidth(160)
        self.open_btn.setFixedHeight(36)
        self.open_btn.clicked.connect(self._on_open_clicked)
        btn_layout.addWidget(self.open_btn)
        layout.addLayout(btn_layout)

    def retranslate(self) -> None:
        self.title_label.setText(_("drop_zone_title"))
        self.sub_label.setText(_("drop_zone_sub"))
        self.open_btn.setText(_("btn_open"))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                ext = Path(urls[0].toLocalFile()).suffix.lower()
                if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            local_path = urls[0].toLocalFile()
            self.file_selected.emit(local_path)
            event.acceptProposedAction()

    def _on_open_clicked(self) -> None:
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            _("dialog_open_title"),
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*)",
        )
        if file_path:
            self.file_selected.emit(file_path)
