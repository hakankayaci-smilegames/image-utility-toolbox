"""Ayarlar ve Geometri Sekmesi (Adjustments & Live Tone Controls).

Boyutlandırma, kırpma, döndürme ve anında canlı tuval güncellemesi sunan
parlaklık, kontrast, renk sıcaklığı ve akıllı vibrance kontrolleri.
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import _
from image_toolbox.core.pipeline import PipelineEngine
from image_toolbox.operations import (
    ColorBalanceOperation,
    ExposureOperation,
    ResizeOperation,
    TransformOperation,
    VibranceOperation,
)


class AdjustmentsTab(QWidget):
    """Görsel boyut, yön ve anlık canlı önizlemeli pozlama/renk sekmesi."""

    apply_requested = pyqtSignal(object)
    commit_requested = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_context: Optional[ImageContext] = None

        # Canlı önizleme için hafif debounced timer
        self._live_timer = QTimer(self)
        self._live_timer.setSingleShot(True)
        self._live_timer.timeout.connect(self._run_live_adjustments)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # 1. Boyutlandırma ve Geometri Grubu
        self.geo_group = QGroupBox(_("group_geom"))
        geo_layout = QGridLayout(self.geo_group)
        geo_layout.setSpacing(10)

        self.width_label = QLabel(_("label_width"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(16, 10000)
        self.width_spin.setValue(1920)
        self.width_spin.setSuffix(" px")

        self.height_label = QLabel(_("label_height"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(16, 10000)
        self.height_spin.setValue(1080)
        self.height_spin.setSuffix(" px")

        self.lock_ratio_check = QCheckBox(_("check_lock_ratio"))
        self.lock_ratio_check.setChecked(True)

        self.mode_label = QLabel(_("label_resize_mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            _("mode_fit"),
            _("mode_fill"),
            _("mode_pad"),
            _("mode_exact"),
        ])

        geo_layout.addWidget(self.width_label, 0, 0)
        geo_layout.addWidget(self.width_spin, 0, 1)
        geo_layout.addWidget(self.height_label, 1, 0)
        geo_layout.addWidget(self.height_spin, 1, 1)
        geo_layout.addWidget(self.lock_ratio_check, 2, 0, 1, 2)
        geo_layout.addWidget(self.mode_label, 3, 0)
        geo_layout.addWidget(self.mode_combo, 3, 1)

        layout.addWidget(self.geo_group)

        # 2. Döndürme ve Yön
        self.rot_group = QGroupBox(_("group_transform"))
        rot_layout = QHBoxLayout(self.rot_group)

        self.rot_left_btn = QPushButton(_("btn_rot_left"))
        self.rot_left_btn.clicked.connect(lambda: self._apply_transform(angle=270))
        self.rot_right_btn = QPushButton(_("btn_rot_right"))
        self.rot_right_btn.clicked.connect(lambda: self._apply_transform(angle=90))
        self.flip_h_btn = QPushButton(_("btn_flip_h"))
        self.flip_h_btn.clicked.connect(lambda: self._apply_transform(flip_h=True))
        self.flip_v_btn = QPushButton(_("btn_flip_v"))
        self.flip_v_btn.clicked.connect(lambda: self._apply_transform(flip_v=True))

        for b in (self.rot_left_btn, self.rot_right_btn, self.flip_h_btn, self.flip_v_btn):
            rot_layout.addWidget(b)

        layout.addWidget(self.rot_group)

        # 3. Pozlama ve Ton Ayarları (Canlı Güncelleme)
        self.tone_group = QGroupBox(_("group_tone"))
        tone_layout = QGridLayout(self.tone_group)
        tone_layout.setSpacing(8)

        # Parlaklık
        self.bright_label = QLabel(_("label_brightness", val=0))
        self.bright_slider = QSlider(Qt.Orientation.Horizontal)
        self.bright_slider.setRange(-100, 100)
        self.bright_slider.setValue(0)
        self.bright_slider.valueChanged.connect(
            lambda v: self.bright_label.setText(_("label_brightness", val=v))
        )
        self.bright_slider.valueChanged.connect(self._trigger_live_update)

        # Kontrast
        self.contrast_label = QLabel(_("label_contrast", val="1.0"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(2, 30)
        self.contrast_slider.setValue(10)
        self.contrast_slider.valueChanged.connect(
            lambda v: self.contrast_label.setText(_("label_contrast", val=f"{v/10.0:.1f}"))
        )
        self.contrast_slider.valueChanged.connect(self._trigger_live_update)

        # Renk Sıcaklığı (Kelvin)
        self.temp_label = QLabel(_("label_temp", val=6500))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(2500, 12000)
        self.temp_slider.setValue(6500)
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(_("label_temp", val=v))
        )
        self.temp_slider.valueChanged.connect(self._trigger_live_update)

        # Vibrance
        self.vib_label = QLabel(_("label_vibrance", val="0.0"))
        self.vib_slider = QSlider(Qt.Orientation.Horizontal)
        self.vib_slider.setRange(-10, 15)
        self.vib_slider.setValue(0)
        self.vib_slider.valueChanged.connect(
            lambda v: self.vib_label.setText(_("label_vibrance", val=f"{v/10.0:.1f}"))
        )
        self.vib_slider.valueChanged.connect(self._trigger_live_update)

        tone_layout.addWidget(self.bright_label, 0, 0)
        tone_layout.addWidget(self.bright_slider, 1, 0)
        tone_layout.addWidget(self.contrast_label, 2, 0)
        tone_layout.addWidget(self.contrast_slider, 3, 0)
        tone_layout.addWidget(self.temp_label, 4, 0)
        tone_layout.addWidget(self.temp_slider, 5, 0)
        tone_layout.addWidget(self.vib_label, 6, 0)
        tone_layout.addWidget(self.vib_slider, 7, 0)

        layout.addWidget(self.tone_group)

        # Aksiyon Butonları
        btn_box = QHBoxLayout()
        self.reset_btn = QPushButton(_("btn_reset_adjust"))
        self.reset_btn.clicked.connect(self._on_reset_sliders)
        btn_box.addWidget(self.reset_btn)

        self.apply_btn = QPushButton(_("btn_apply_adjust"))
        self.apply_btn.setProperty("primary", True)
        self.apply_btn.setFixedHeight(36)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        btn_box.addWidget(self.apply_btn)

        layout.addLayout(btn_box)
        layout.addStretch(1)

        scroll.setWidget(container)
        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(scroll)

    def set_context(self, context: Optional[ImageContext]) -> None:
        self._current_context = context
        if context is not None:
            self.width_spin.setValue(context.width)
            self.height_spin.setValue(context.height)

    def _trigger_live_update(self) -> None:
        if self._current_context is None:
            return
        self._live_timer.start(25)

    def _run_live_adjustments(self) -> None:
        """Slider hareket ettiğinde anında canlı önizleme üretir."""
        if self._current_context is None:
            return

        pipeline = PipelineEngine()

        # Parlaklık / Kontrast
        b_val = float(self.bright_slider.value())
        c_val = float(self.contrast_slider.value()) / 10.0
        if b_val != 0.0 or c_val != 1.0:
            pipeline.add(ExposureOperation(brightness=b_val, contrast=c_val))

        # Kelvin Sıcaklığı
        k_val = float(self.temp_slider.value())
        if k_val != 6500.0:
            pipeline.add(ColorBalanceOperation(kelvin=k_val))

        # Vibrance
        v_val = float(self.vib_slider.value()) / 10.0
        if v_val != 0.0:
            pipeline.add(VibranceOperation(vibrance=v_val, protect_skin_tones=True))

        if len(pipeline) == 0:
            self.apply_requested.emit(self._current_context.clone())
            return

        try:
            res = pipeline.execute(self._current_context.clone())
            self.apply_requested.emit(res)
        except Exception:
            pass

    def _apply_transform(self, angle: float = 0.0, flip_h: bool = False, flip_v: bool = False) -> None:
        if self._current_context is None:
            return
        op = TransformOperation(angle=angle, flip_h=flip_h, flip_v=flip_v)
        res = op.apply(self._current_context.clone())
        self._current_context = res.clone()
        self.apply_requested.emit(res)
        self.commit_requested.emit(res)

    def _on_reset_sliders(self) -> None:
        self.bright_slider.setValue(0)
        self.contrast_slider.setValue(10)
        self.temp_slider.setValue(6500)
        self.vib_slider.setValue(0)
        if self._current_context is not None:
            self.apply_requested.emit(self._current_context.clone())

    def _on_apply_clicked(self) -> None:
        if self._current_context is None:
            return

        pipeline = PipelineEngine()
        target_w = self.width_spin.value()
        target_h = self.height_spin.value()

        # Boyutlandırma
        if (target_w, target_h) != self._current_context.size:
            mode_map = {0: "fit", 1: "fill", 2: "pad", 3: "exact"}
            mode = mode_map.get(self.mode_combo.currentIndex(), "fit")
            pipeline.add(ResizeOperation(width=target_w, height=target_h, mode=mode))

        # Parlaklık / Kontrast
        b_val = float(self.bright_slider.value())
        c_val = float(self.contrast_slider.value()) / 10.0
        if b_val != 0.0 or c_val != 1.0:
            pipeline.add(ExposureOperation(brightness=b_val, contrast=c_val))

        # Kelvin Sıcaklığı
        k_val = float(self.temp_slider.value())
        if k_val != 6500.0:
            pipeline.add(ColorBalanceOperation(kelvin=k_val))

        # Vibrance
        v_val = float(self.vib_slider.value()) / 10.0
        if v_val != 0.0:
            pipeline.add(VibranceOperation(vibrance=v_val, protect_skin_tones=True))

        res = pipeline.execute(self._current_context.clone())
        self._current_context = res.clone()
        self.apply_requested.emit(res)
        self.commit_requested.emit(res)

    def retranslate(self) -> None:
        self.geo_group.setTitle(_("group_geom"))
        self.width_label.setText(_("label_width"))
        self.height_label.setText(_("label_height"))
        self.lock_ratio_check.setText(_("check_lock_ratio"))
        self.mode_label.setText(_("label_resize_mode"))

        curr_mode = self.mode_combo.currentIndex()
        self.mode_combo.clear()
        self.mode_combo.addItems([
            _("mode_fit"),
            _("mode_fill"),
            _("mode_pad"),
            _("mode_exact"),
        ])
        self.mode_combo.setCurrentIndex(curr_mode)

        self.rot_group.setTitle(_("group_transform"))
        self.rot_left_btn.setText(_("btn_rot_left"))
        self.rot_right_btn.setText(_("btn_rot_right"))
        self.flip_h_btn.setText(_("btn_flip_h"))
        self.flip_v_btn.setText(_("btn_flip_v"))

        self.tone_group.setTitle(_("group_tone"))
        self.bright_label.setText(_("label_brightness", val=self.bright_slider.value()))
        self.contrast_label.setText(_("label_contrast", val=f"{self.contrast_slider.value()/10.0:.1f}"))
        self.temp_label.setText(_("label_temp", val=self.temp_slider.value()))
        self.vib_label.setText(_("label_vibrance", val=f"{self.vib_slider.value()/10.0:.1f}"))

        self.reset_btn.setText(_("btn_reset_adjust"))
        self.apply_btn.setText(_("btn_apply_adjust"))
