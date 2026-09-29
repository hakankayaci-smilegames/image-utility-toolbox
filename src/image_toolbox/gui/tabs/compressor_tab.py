"""Akıllı Hedef Boyutlu Sıkıştırma Sekmesi (Smart Compressor Tab)."""

from __future__ import annotations

import time
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import _
from image_toolbox.services.compressor_service import TargetSizeCompressorService


class CompressorTab(QWidget):
    """Amiral gemisi hedef boyutlu akıllı sıkıştırma kontrol sekmesi."""

    apply_requested = pyqtSignal(object)  # ImageContext

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_context: Optional[ImageContext] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Hedef Boyut ve Format Grubu
        self.cfg_group = QGroupBox(_("tab_compress"))
        cfg_layout = QGridLayout(self.cfg_group)
        cfg_layout.setSpacing(12)

        # Hedef Boyut
        self.target_label = QLabel(_("target_size_label"))
        self.target_spin = QSpinBox()
        self.target_spin.setRange(10, 50000)
        self.target_spin.setValue(350)
        self.target_spin.setSuffix(" KB")
        self.target_spin.setFixedHeight(32)

        cfg_layout.addWidget(self.target_label, 0, 0)
        cfg_layout.addWidget(self.target_spin, 0, 1)

        # Çıktı Formatı
        self.fmt_label = QLabel(_("output_format_label"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["WEBP", "JPEG"])
        self.fmt_combo.setFixedHeight(32)

        cfg_layout.addWidget(self.fmt_label, 1, 0)
        cfg_layout.addWidget(self.fmt_combo, 1, 1)

        # Metaveri Temizleme
        self.strip_exif_check = QCheckBox(_("strip_metadata_check"))
        self.strip_exif_check.setChecked(True)
        cfg_layout.addWidget(self.strip_exif_check, 2, 0, 1, 2)

        # Minimum Kalite Eşiği
        self.min_q_label = QLabel(_("min_quality_label", val=40))
        self.min_q_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_q_slider.setRange(20, 80)
        self.min_q_slider.setValue(40)
        self.min_q_slider.valueChanged.connect(
            lambda v: self.min_q_label.setText(_("min_quality_label", val=v))
        )
        cfg_layout.addWidget(self.min_q_label, 3, 0, 1, 2)
        cfg_layout.addWidget(self.min_q_slider, 4, 0, 1, 2)

        layout.addWidget(self.cfg_group)

        # 2. Çalıştır Butonu
        self.run_btn = QPushButton(_("btn_run_compress"))
        self.run_btn.setProperty("primary", True)
        self.run_btn.setFixedHeight(40)
        self.run_btn.clicked.connect(self._on_compress_clicked)
        layout.addWidget(self.run_btn)

        # 3. Canlı İstatistik ve Sonuç Kartı
        self.stats_group = QGroupBox(_("compress_report_title"))
        stats_layout = QVBoxLayout(self.stats_group)
        stats_layout.setSpacing(8)

        self.orig_size_label = QLabel("Orijinal Boyut: -")
        self.final_size_label = QLabel("Sıkıştırılmış Boyut: -")
        self.quality_found_label = QLabel("Tespit Edilen En İyi Kalite: -")
        self.iterations_label = QLabel("İkili Arama İterasyonu: -")
        self.resolution_label = QLabel("Çözünürlük Durumu: -")

        for lbl in (
            self.orig_size_label,
            self.final_size_label,
            self.quality_found_label,
            self.iterations_label,
            self.resolution_label,
        ):
            lbl.setStyleSheet("color: #CBD5E1; font-size: 13px;")
            stats_layout.addWidget(lbl)

        # Tasarruf Çubuğu
        self.savings_bar = QProgressBar()
        self.savings_bar.setRange(0, 100)
        self.savings_bar.setValue(0)
        self.savings_bar.setFormat("Tasarruf: %p%")
        stats_layout.addWidget(self.savings_bar)

        layout.addWidget(self.stats_group)
        layout.addStretch(1)

    def set_context(self, context: Optional[ImageContext]) -> None:
        self._current_context = context
        if context is not None:
            # Yaklaşık mevcut RAM boyutunu hesapla
            orig_bytes = len(context.to_bytes(context.source_format))
            self.orig_size_label.setText(
                f"Orijinal Boyut: {orig_bytes / 1024.0:.1f} KB ({context.width}x{context.height} px)"
            )
            # Varsayılan hedef boyutu orijinalin %50'si olarak öner
            suggested_kb = max(50, int(orig_bytes / 1024.0 * 0.5))
            self.target_spin.setValue(suggested_kb)

    def _on_compress_clicked(self) -> None:
        if self._current_context is None:
            return

        target_kb = self.target_spin.value()
        target_str = f"{target_kb}kb"
        fmt = self.fmt_combo.currentText()
        strip_meta = self.strip_exif_check.isChecked()
        min_q = self.min_q_slider.value()

        service = TargetSizeCompressorService(
            min_quality=min_q,
            strip_metadata=strip_meta,
        )

        orig_bytes = len(self._current_context.to_bytes(self._current_context.source_format))
        start_t = time.perf_counter()

        res_ctx = service.compress(
            self._current_context,
            target_size=target_str,
            format=fmt,
        )
        duration = time.perf_counter() - start_t

        meta = res_ctx.metadata.get("compression", {})
        final_bytes = meta.get("final_bytes", len(res_ctx.to_bytes(fmt)))
        final_kb = final_bytes / 1024.0
        final_q = meta.get("final_quality", "-")
        iters = meta.get("iterations", 0)
        scales = meta.get("fallback_scales", 0)

        self.final_size_label.setText(f"Sıkıştırılmış Boyut: {final_kb:.1f} KB ({res_ctx.width}x{res_ctx.height} px)")
        self.quality_found_label.setText(f"Tespit Edilen En İyi Kalite: {final_q} / 100")
        self.iterations_label.setText(f"İkili Arama İterasyonu: {iters} adım ({duration:.2f}s)")
        scale_msg = f"{scales} kademeli küçültme yapıldı" if scales > 0 else "Tam çözünürlük korundu"
        self.resolution_label.setText(f"Çözünürlük: {scale_msg}")

        # Tasarruf yüzdesi
        if orig_bytes > 0:
            saved_pct = max(0, int((1.0 - (final_bytes / orig_bytes)) * 100))
            self.savings_bar.setValue(saved_pct)

        self.apply_requested.emit(res_ctx)

    def retranslate(self) -> None:
        self.cfg_group.setTitle(_("tab_compress"))
        self.target_label.setText(_("target_size_label"))
        self.fmt_label.setText(_("output_format_label"))
        self.strip_exif_check.setText(_("strip_metadata_check"))
        self.min_q_label.setText(_("min_quality_label", val=self.min_q_slider.value()))
        self.run_btn.setText(_("btn_run_compress"))
        self.stats_group.setTitle(_("compress_report_title"))
        self.savings_bar.setFormat(_("label_savings", val="%p"))

