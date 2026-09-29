"""Palet ve EXIF Analiz Sekmesi (Palette & EXIF Analysis Tab)."""

from __future__ import annotations

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import _
from image_toolbox.operations import ExifToolOperation, PaletteExtractorOperation


class AnalysisTab(QWidget):
    """K-Means baskın renk paleti çıkarıcı ve EXIF metaveri inceleme/temizleme sekmesi."""

    apply_requested = pyqtSignal(object)
    status_requested = pyqtSignal(str, str)  # text, type

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_context: Optional[ImageContext] = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Renk Paleti Grubu
        self.pal_group = QGroupBox(_("group_palette"))
        pal_layout = QVBoxLayout(self.pal_group)
        pal_layout.setSpacing(10)

        top_row = QHBoxLayout()
        self.k_label = QLabel(_("label_k_count"))
        top_row.addWidget(self.k_label)
        self.k_spin = QSpinBox()
        self.k_spin.setRange(3, 10)
        self.k_spin.setValue(5)
        top_row.addWidget(self.k_spin)

        self.extract_btn = QPushButton(_("btn_extract_palette"))
        self.extract_btn.setProperty("primary", True)
        self.extract_btn.clicked.connect(self._extract_palette)
        top_row.addWidget(self.extract_btn)
        pal_layout.addLayout(top_row)

        # Palet Kartları Alanı
        self.palette_cards_layout = QVBoxLayout()
        self.palette_cards_layout.setSpacing(6)
        pal_layout.addLayout(self.palette_cards_layout)

        layout.addWidget(self.pal_group)

        # 2. EXIF Metaveri İnceleme ve Sterilizasyon Grubu
        self.exif_group = QGroupBox(_("group_exif"))
        exif_layout = QVBoxLayout(self.exif_group)
        exif_layout.setSpacing(10)

        # EXIF Butonları
        exif_btn_layout = QHBoxLayout()
        self.inspect_btn = QPushButton(_("btn_inspect_exif"))
        self.inspect_btn.clicked.connect(self._inspect_exif)
        self.strip_gps_btn = QPushButton(_("btn_strip_gps"))
        self.strip_gps_btn.clicked.connect(lambda: self._sanitize_exif("strip_gps"))
        self.strip_all_btn = QPushButton(_("btn_strip_all"))
        self.strip_all_btn.clicked.connect(lambda: self._sanitize_exif("strip_all"))

        for b in (self.inspect_btn, self.strip_gps_btn, self.strip_all_btn):
            exif_btn_layout.addWidget(b)
        exif_layout.addLayout(exif_btn_layout)

        # EXIF Tablosu
        self.exif_table = QTableWidget(0, 2)
        self.exif_table.setHorizontalHeaderLabels([_("header_tag"), _("header_val")])
        self.exif_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.exif_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.exif_table.setFixedHeight(220)
        exif_layout.addWidget(self.exif_table)

        layout.addWidget(self.exif_group)
        layout.addStretch(1)

        scroll.setWidget(container)
        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(scroll)

    def set_context(self, context: Optional[ImageContext]) -> None:
        self._current_context = context
        if context is not None:
            # Otomatik EXIF incelemesi başlat
            self._inspect_exif()

    def _extract_palette(self) -> None:
        if self._current_context is None:
            return

        k = self.k_spin.value()
        op = PaletteExtractorOperation(k=k)
        res = op.apply(self._current_context.clone())

        palette = res.metadata.get("palette", [])
        self._render_palette_cards(palette)
        self.status_requested.emit(f"K-Means ile {len(palette)} baskın renk çıkarıldı.", "success")

    def _render_palette_cards(self, palette: list) -> None:
        # Önceki kartları temizle
        while self.palette_cards_layout.count() > 0:
            item = self.palette_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for color_item in palette:
            hex_code = color_item["hex"]
            rgb_vals = color_item["rgb"]
            pct = color_item["percentage"]

            card = QFrame()
            card.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; border-radius: 6px;")
            card.setFixedHeight(40)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(8, 4, 8, 4)

            # Renk Kutusu
            swatch = QFrame()
            swatch.setFixedSize(28, 28)
            swatch.setStyleSheet(f"background-color: {hex_code}; border-radius: 4px; border: 1px solid #64748B;")
            c_layout.addWidget(swatch)

            # Bilgiler
            info_lbl = QLabel(f"<b>{hex_code}</b> | RGB{tuple(rgb_vals)} | %{pct}")
            info_lbl.setStyleSheet("color: #F8FAFC; font-size: 12px;")
            c_layout.addWidget(info_lbl, 1)

            # Kopyala Butonu
            copy_btn = QPushButton("Kopyala")
            copy_btn.setFixedSize(65, 26)
            copy_btn.clicked.connect(lambda _, h=hex_code: self._copy_to_clipboard(h))
            c_layout.addWidget(copy_btn)

            self.palette_cards_layout.addWidget(card)

    def _copy_to_clipboard(self, text: str) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.status_requested.emit(f"{text} panoya kopyalandı!", "info")

    def _inspect_exif(self) -> None:
        if self._current_context is None:
            return

        op = ExifToolOperation(action="inspect")
        res = op.apply(self._current_context.clone())
        exif_dict = res.metadata.get("exif_data", {})

        self.exif_table.setRowCount(0)
        if not exif_dict:
            self.exif_table.setRowCount(1)
            self.exif_table.setItem(0, 0, QTableWidgetItem("Durum"))
            self.exif_table.setItem(0, 1, QTableWidgetItem("EXIF metaverisi bulunamadı."))
            return

        for tag, val in sorted(exif_dict.items()):
            row = self.exif_table.rowCount()
            self.exif_table.insertRow(row)
            self.exif_table.setItem(row, 0, QTableWidgetItem(str(tag)))
            self.exif_table.setItem(row, 1, QTableWidgetItem(str(val)))

    def _sanitize_exif(self, action: str) -> None:
        if self._current_context is None:
            return

        op = ExifToolOperation(action=action)
        res = op.apply(self._current_context)
        self.apply_requested.emit(res)
        msg = "Tüm EXIF metaverileri temizlendi." if action == "strip_all" else "GPS verisi temizlendi."
        self.status_requested.emit(msg, "success")
        self._inspect_exif()

    def retranslate(self) -> None:
        self.pal_group.setTitle(_("group_palette"))
        self.k_label.setText(_("label_k_count"))
        self.extract_btn.setText(_("btn_extract_palette"))
        self.exif_group.setTitle(_("group_exif"))
        self.inspect_btn.setText(_("btn_inspect_exif"))
        self.strip_gps_btn.setText(_("btn_strip_gps"))
        self.strip_all_btn.setText(_("btn_strip_all"))
        self.exif_table.setHorizontalHeaderLabels([_("header_tag"), _("header_val")])

