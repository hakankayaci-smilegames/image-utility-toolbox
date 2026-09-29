"""Filtreler ve Sanatsal Efektler Sekmesi (Filters & Contextual Effects Tab).

Her efekt seçildiğinde yalnızca o efekte özel parametre kontrol barları açılır.
Slider'lar 0.1 dahi hareket ettiğinde tuvalde canlı ve anlık (real-time live)
önizleme gerçekleştirilir.
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import _
from image_toolbox.operations import (
    ArtisticPresetsOperation,
    BlurOperation,
    BordersOperation,
    EdgeSketchOperation,
    HistogramOperation,
    SharpnessOperation,
    VignetteOperation,
)


class EffectsTab(QWidget):
    """Ayrılmış parametre barları ve anında canlı önizlemeli sanatsal efektler sekmesi."""

    apply_requested = pyqtSignal(object)
    commit_requested = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_context: Optional[ImageContext] = None
        self._last_result_context: Optional[ImageContext] = None
        self._active_effect_index: int = 0

        # Canlı reaktif önizleme için hafif debounced timer (25ms)
        self._live_timer = QTimer(self)
        self._live_timer.setSingleShot(True)
        self._live_timer.timeout.connect(self._run_live_effect)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # 1. Efekt Seçici Butonlar Grubu
        self.selector_group = QGroupBox(_("group_presets"))
        sel_layout = QGridLayout(self.selector_group)
        sel_layout.setSpacing(6)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.effect_buttons = [
            QPushButton(_("effect_sepia")),
            QPushButton(_("effect_vintage")),
            QPushButton(_("effect_cyanotype")),
            QPushButton(_("effect_cyberpunk")),
            QPushButton(_("effect_vignette")),
            QPushButton(_("effect_sharpness")),
            QPushButton(_("effect_blur")),
            QPushButton(_("effect_clahe")),
            QPushButton(_("effect_sketch")),
            QPushButton(_("effect_borders")),
        ]

        for i, btn in enumerate(self.effect_buttons):
            btn.setCheckable(True)
            self.btn_group.addButton(btn, i)
            row, col = divmod(i, 2)
            sel_layout.addWidget(btn, row, col)

        self.effect_buttons[0].setChecked(True)
        self.btn_group.idClicked.connect(self._on_effect_selected)
        layout.addWidget(self.selector_group)

        # 2. Seçili Efekte Özel Dinamik Parametre Paneli (QStackedWidget)
        self.params_group = QGroupBox(_("group_effect_params"))
        params_layout = QVBoxLayout(self.params_group)
        params_layout.setContentsMargins(12, 16, 12, 12)
        params_layout.setSpacing(10)

        self.stack = QStackedWidget()

        # Sayfa 0: Sepia
        self.page_sepia = self._create_sepia_page()
        self.stack.addWidget(self.page_sepia)

        # Sayfa 1: Vintage
        self.page_vintage = self._create_vintage_page()
        self.stack.addWidget(self.page_vintage)

        # Sayfa 2: Cyanotype
        self.page_cyanotype = self._create_cyanotype_page()
        self.stack.addWidget(self.page_cyanotype)

        # Sayfa 3: Cyberpunk
        self.page_cyberpunk = self._create_cyberpunk_page()
        self.stack.addWidget(self.page_cyberpunk)

        # Sayfa 4: Vignette
        self.page_vignette = self._create_vignette_page()
        self.stack.addWidget(self.page_vignette)

        # Sayfa 5: Sharpness
        self.page_sharpness = self._create_sharpness_page()
        self.stack.addWidget(self.page_sharpness)

        # Sayfa 6: Blur
        self.page_blur = self._create_blur_page()
        self.stack.addWidget(self.page_blur)

        # Sayfa 7: CLAHE
        self.page_clahe = self._create_clahe_page()
        self.stack.addWidget(self.page_clahe)

        # Sayfa 8: Sketch
        self.page_sketch = self._create_sketch_page()
        self.stack.addWidget(self.page_sketch)

        # Sayfa 9: Borders
        self.page_borders = self._create_borders_page()
        self.stack.addWidget(self.page_borders)

        params_layout.addWidget(self.stack)
        layout.addWidget(self.params_group)

        # 3. Aksiyon Butonları (Sıfırla ve Sabitle)
        action_layout = QHBoxLayout()
        self.clear_btn = QPushButton(_("btn_clear_effect"))
        self.clear_btn.setFixedHeight(34)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        action_layout.addWidget(self.clear_btn)

        self.commit_btn = QPushButton(_("btn_commit_effect"))
        self.commit_btn.setProperty("primary", True)
        self.commit_btn.setFixedHeight(34)
        self.commit_btn.clicked.connect(self._on_commit_clicked)
        action_layout.addWidget(self.commit_btn)

        layout.addLayout(action_layout)
        layout.addStretch(1)

        scroll.setWidget(container)
        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(scroll)

    # ----------------- Sayfa Oluşturucular -----------------

    def _create_sepia_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        self.sepia_lbl = QLabel(_("label_intensity", val=100))
        self.sepia_slider = QSlider(Qt.Orientation.Horizontal)
        self.sepia_slider.setRange(0, 100)
        self.sepia_slider.setValue(100)
        self.sepia_slider.valueChanged.connect(lambda v: self.sepia_lbl.setText(_("label_intensity", val=v)))
        self.sepia_slider.valueChanged.connect(self._trigger_live_update)
        l.addWidget(self.sepia_lbl)
        l.addWidget(self.sepia_slider)
        return p

    def _create_vintage_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        self.vin_int_lbl = QLabel(_("label_intensity", val=90))
        self.vin_int_slider = QSlider(Qt.Orientation.Horizontal)
        self.vin_int_slider.setRange(0, 100)
        self.vin_int_slider.setValue(90)
        self.vin_int_slider.valueChanged.connect(lambda v: self.vin_int_lbl.setText(_("label_intensity", val=v)))
        self.vin_int_slider.valueChanged.connect(self._trigger_live_update)

        self.vin_grain_lbl = QLabel(_("label_grain", val=40))
        self.vin_grain_slider = QSlider(Qt.Orientation.Horizontal)
        self.vin_grain_slider.setRange(0, 100)
        self.vin_grain_slider.setValue(40)
        self.vin_grain_slider.valueChanged.connect(lambda v: self.vin_grain_lbl.setText(_("label_grain", val=v)))
        self.vin_grain_slider.valueChanged.connect(self._trigger_live_update)

        l.addWidget(self.vin_int_lbl)
        l.addWidget(self.vin_int_slider)
        l.addWidget(self.vin_grain_lbl)
        l.addWidget(self.vin_grain_slider)
        return p

    def _create_cyanotype_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        self.cyan_lbl = QLabel(_("label_intensity", val=100))
        self.cyan_slider = QSlider(Qt.Orientation.Horizontal)
        self.cyan_slider.setRange(0, 100)
        self.cyan_slider.setValue(100)
        self.cyan_slider.valueChanged.connect(lambda v: self.cyan_lbl.setText(_("label_intensity", val=v)))
        self.cyan_slider.valueChanged.connect(self._trigger_live_update)
        l.addWidget(self.cyan_lbl)
        l.addWidget(self.cyan_slider)
        return p

    def _create_cyberpunk_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        self.cyber_lbl = QLabel(_("label_intensity", val=100))
        self.cyber_slider = QSlider(Qt.Orientation.Horizontal)
        self.cyber_slider.setRange(0, 100)
        self.cyber_slider.setValue(100)
        self.cyber_slider.valueChanged.connect(lambda v: self.cyber_lbl.setText(_("label_intensity", val=v)))
        self.cyber_slider.valueChanged.connect(self._trigger_live_update)
        l.addWidget(self.cyber_lbl)
        l.addWidget(self.cyber_slider)
        return p

    def _create_vignette_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)

        self.vig_op_lbl = QLabel(_("label_opacity", val=70))
        self.vig_op_slider = QSlider(Qt.Orientation.Horizontal)
        self.vig_op_slider.setRange(0, 100)
        self.vig_op_slider.setValue(70)
        self.vig_op_slider.valueChanged.connect(lambda v: self.vig_op_lbl.setText(_("label_opacity", val=v)))
        self.vig_op_slider.valueChanged.connect(self._trigger_live_update)

        self.vig_rad_lbl = QLabel(_("label_radius", val="0.8"))
        self.vig_rad_slider = QSlider(Qt.Orientation.Horizontal)
        self.vig_rad_slider.setRange(10, 150)
        self.vig_rad_slider.setValue(80)
        self.vig_rad_slider.valueChanged.connect(lambda v: self.vig_rad_lbl.setText(_("label_radius", val=f"{v/100:.2f}")))
        self.vig_rad_slider.valueChanged.connect(self._trigger_live_update)

        self.vig_fea_lbl = QLabel(_("label_feather", val=50))
        self.vig_fea_slider = QSlider(Qt.Orientation.Horizontal)
        self.vig_fea_slider.setRange(10, 100)
        self.vig_fea_slider.setValue(50)
        self.vig_fea_slider.valueChanged.connect(lambda v: self.vig_fea_lbl.setText(_("label_feather", val=v)))
        self.vig_fea_slider.valueChanged.connect(self._trigger_live_update)

        l.addWidget(self.vig_op_lbl)
        l.addWidget(self.vig_op_slider)
        l.addWidget(self.vig_rad_lbl)
        l.addWidget(self.vig_rad_slider)
        l.addWidget(self.vig_fea_lbl)
        l.addWidget(self.vig_fea_slider)
        return p

    def _create_sharpness_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)

        self.sharp_amt_lbl = QLabel(_("label_amount", val="1.5"))
        self.sharp_amt_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharp_amt_slider.setRange(1, 50)
        self.sharp_amt_slider.setValue(15)
        self.sharp_amt_slider.valueChanged.connect(lambda v: self.sharp_amt_lbl.setText(_("label_amount", val=f"{v/10:.1f}")))
        self.sharp_amt_slider.valueChanged.connect(self._trigger_live_update)

        self.sharp_rad_lbl = QLabel(_("label_radius", val="1.2"))
        self.sharp_rad_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharp_rad_slider.setRange(5, 50)
        self.sharp_rad_slider.setValue(12)
        self.sharp_rad_slider.valueChanged.connect(lambda v: self.sharp_rad_lbl.setText(_("label_radius", val=f"{v/10:.1f}")))
        self.sharp_rad_slider.valueChanged.connect(self._trigger_live_update)

        self.sharp_cla_lbl = QLabel(_("label_clarity", val="0.3"))
        self.sharp_cla_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharp_cla_slider.setRange(-10, 10)
        self.sharp_cla_slider.setValue(3)
        self.sharp_cla_slider.valueChanged.connect(lambda v: self.sharp_cla_lbl.setText(_("label_clarity", val=f"{v/10:.1f}")))
        self.sharp_cla_slider.valueChanged.connect(self._trigger_live_update)

        l.addWidget(self.sharp_amt_lbl)
        l.addWidget(self.sharp_amt_slider)
        l.addWidget(self.sharp_rad_lbl)
        l.addWidget(self.sharp_rad_slider)
        l.addWidget(self.sharp_cla_lbl)
        l.addWidget(self.sharp_cla_slider)
        return p

    def _create_blur_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)

        self.blur_mode_lbl = QLabel(_("label_blur_mode"))
        self.blur_mode_combo = QComboBox()
        self.blur_mode_combo.addItems(["Gaussian", "Box", "Motion", "Tilt-Shift"])
        self.blur_mode_combo.currentIndexChanged.connect(self._on_blur_mode_changed)

        self.blur_rad_lbl = QLabel(_("label_blur_radius", val=5))
        self.blur_rad_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_rad_slider.setRange(1, 40)
        self.blur_rad_slider.setValue(5)
        self.blur_rad_slider.valueChanged.connect(lambda v: self.blur_rad_lbl.setText(_("label_blur_radius", val=v)))
        self.blur_rad_slider.valueChanged.connect(self._trigger_live_update)

        self.blur_ang_lbl = QLabel(_("label_motion_angle", val=0))
        self.blur_ang_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_ang_slider.setRange(0, 360)
        self.blur_ang_slider.setValue(0)
        self.blur_ang_slider.valueChanged.connect(lambda v: self.blur_ang_lbl.setText(_("label_motion_angle", val=v)))
        self.blur_ang_slider.valueChanged.connect(self._trigger_live_update)
        self.blur_ang_lbl.setVisible(False)
        self.blur_ang_slider.setVisible(False)

        l.addWidget(self.blur_mode_lbl)
        l.addWidget(self.blur_mode_combo)
        l.addWidget(self.blur_rad_lbl)
        l.addWidget(self.blur_rad_slider)
        l.addWidget(self.blur_ang_lbl)
        l.addWidget(self.blur_ang_slider)
        return p

    def _on_blur_mode_changed(self, idx: int) -> None:
        is_motion = (idx == 2)
        self.blur_ang_lbl.setVisible(is_motion)
        self.blur_ang_slider.setVisible(is_motion)
        self._trigger_live_update()

    def _create_clahe_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)

        self.clahe_clip_lbl = QLabel(_("label_clip_limit", val="2.5"))
        self.clahe_clip_slider = QSlider(Qt.Orientation.Horizontal)
        self.clahe_clip_slider.setRange(10, 80)
        self.clahe_clip_slider.setValue(25)
        self.clahe_clip_slider.valueChanged.connect(lambda v: self.clahe_clip_lbl.setText(_("label_clip_limit", val=f"{v/10:.1f}")))
        self.clahe_clip_slider.valueChanged.connect(self._trigger_live_update)

        self.clahe_grid_lbl = QLabel(_("label_grid_size", val=8))
        self.clahe_grid_slider = QSlider(Qt.Orientation.Horizontal)
        self.clahe_grid_slider.setRange(2, 16)
        self.clahe_grid_slider.setValue(8)
        self.clahe_grid_slider.valueChanged.connect(lambda v: self.clahe_grid_lbl.setText(_("label_grid_size", val=v)))
        self.clahe_grid_slider.valueChanged.connect(self._trigger_live_update)

        l.addWidget(self.clahe_clip_lbl)
        l.addWidget(self.clahe_clip_slider)
        l.addWidget(self.clahe_grid_lbl)
        l.addWidget(self.clahe_grid_slider)
        return p

    def _create_sketch_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)

        self.sketch_mode_lbl = QLabel(_("label_sketch_mode"))
        self.sketch_mode_combo = QComboBox()
        self.sketch_mode_combo.addItems(["Sketch", "Sobel", "Canny"])
        self.sketch_mode_combo.currentIndexChanged.connect(self._trigger_live_update)

        l.addWidget(self.sketch_mode_lbl)
        l.addWidget(self.sketch_mode_combo)
        return p

    def _create_borders_page(self) -> QWidget:
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)

        self.border_style_lbl = QLabel(_("label_border_mode"))
        self.border_style_combo = QComboBox()
        self.border_style_combo.addItems(["Solid", "Polaroid", "Rounded"])
        self.border_style_combo.currentIndexChanged.connect(self._trigger_live_update)

        self.border_w_lbl = QLabel(_("label_border_width", val=20))
        self.border_w_slider = QSlider(Qt.Orientation.Horizontal)
        self.border_w_slider.setRange(5, 80)
        self.border_w_slider.setValue(20)
        self.border_w_slider.valueChanged.connect(lambda v: self.border_w_lbl.setText(_("label_border_width", val=v)))
        self.border_w_slider.valueChanged.connect(self._trigger_live_update)

        self.border_rad_lbl = QLabel(_("label_corner_radius", val=25))
        self.border_rad_slider = QSlider(Qt.Orientation.Horizontal)
        self.border_rad_slider.setRange(5, 80)
        self.border_rad_slider.setValue(25)
        self.border_rad_slider.valueChanged.connect(lambda v: self.border_rad_lbl.setText(_("label_corner_radius", val=v)))
        self.border_rad_slider.valueChanged.connect(self._trigger_live_update)

        l.addWidget(self.border_style_lbl)
        l.addWidget(self.border_style_combo)
        l.addWidget(self.border_w_lbl)
        l.addWidget(self.border_w_slider)
        l.addWidget(self.border_rad_lbl)
        l.addWidget(self.border_rad_slider)
        return p

    # ----------------- Kontrol ve Canlı Önizleme -----------------

    def set_context(self, context: Optional[ImageContext]) -> None:
        self._current_context = context
        self._last_result_context = context.clone() if context is not None else None

    def _on_effect_selected(self, btn_id: int) -> None:
        self._active_effect_index = btn_id
        self.stack.setCurrentIndex(btn_id)
        self._trigger_live_update()

    def _trigger_live_update(self) -> None:
        """Hafif debouncing ile canlı güncelleme tetikler."""
        if self._current_context is None:
            return
        self._live_timer.start(25)

    def _run_live_effect(self) -> None:
        """Seçili efekte ait parametrelerle görseli anında işler ve tuvale gönderir."""
        if self._current_context is None:
            return

        idx = self._active_effect_index
        working_ctx = self._current_context.clone()

        try:
            if idx == 0:  # Sepia
                intensity = self.sepia_slider.value() / 100.0
                op = ArtisticPresetsOperation(preset="sepia", intensity=intensity)
                res = op.apply(working_ctx)

            elif idx == 1:  # Vintage
                intensity = self.vin_int_slider.value() / 100.0
                grain = self.vin_grain_slider.value() / 100.0
                op = ArtisticPresetsOperation(preset="vintage", intensity=intensity, grain=grain)
                res = op.apply(working_ctx)

            elif idx == 2:  # Cyanotype
                intensity = self.cyan_slider.value() / 100.0
                op = ArtisticPresetsOperation(preset="cyanotype", intensity=intensity)
                res = op.apply(working_ctx)

            elif idx == 3:  # Cyberpunk
                intensity = self.cyber_slider.value() / 100.0
                op = ArtisticPresetsOperation(preset="cyberpunk", intensity=intensity)
                res = op.apply(working_ctx)

            elif idx == 4:  # Vignette
                op = VignetteOperation(
                    opacity=self.vig_op_slider.value() / 100.0,
                    radius=self.vig_rad_slider.value() / 100.0,
                    feather=self.vig_fea_slider.value() / 100.0,
                )
                res = op.apply(working_ctx)

            elif idx == 5:  # Sharpness
                op = SharpnessOperation(
                    amount=self.sharp_amt_slider.value() / 10.0,
                    radius=self.sharp_rad_slider.value() / 10.0,
                    clarity=self.sharp_cla_slider.value() / 10.0,
                )
                res = op.apply(working_ctx)

            elif idx == 6:  # Blur
                modes = ["gaussian", "box", "motion", "tilt_shift"]
                mode = modes[self.blur_mode_combo.currentIndex()]
                rad = float(self.blur_rad_slider.value())
                ang = float(self.blur_ang_slider.value())
                op = BlurOperation(mode=mode, radius=rad, angle=ang)
                res = op.apply(working_ctx)

            elif idx == 7:  # CLAHE
                op = HistogramOperation(
                    mode="clahe",
                    clip_limit=self.clahe_clip_slider.value() / 10.0,
                    tile_grid_size=self.clahe_grid_slider.value(),
                )
                res = op.apply(working_ctx)

            elif idx == 8:  # Sketch
                modes = ["sketch", "sobel", "canny"]
                mode = modes[self.sketch_mode_combo.currentIndex()]
                op = EdgeSketchOperation(mode=mode)
                res = op.apply(working_ctx)

            elif idx == 9:  # Borders
                modes = ["solid", "polaroid", "rounded_corners"]
                mode = modes[self.border_style_combo.currentIndex()]
                op = BordersOperation(
                    mode=mode,
                    width=self.border_w_slider.value(),
                    radius=self.border_rad_slider.value(),
                )
                res = op.apply(working_ctx)
            else:
                return

            self._last_result_context = res.clone()
            self.apply_requested.emit(res)
        except Exception:
            pass

    def _on_clear_clicked(self) -> None:
        """Seçili efekt önizlemesini sıfırlayıp son sabitlenen duruma döner."""
        self._live_timer.stop()
        if self._current_context is not None:
            self._last_result_context = self._current_context.clone()
            self.apply_requested.emit(self._current_context.clone())
        self._live_timer.stop()

    def _on_commit_clicked(self) -> None:
        """Mevcut efekti temel alarak sabitler (Üstüne yeni efektler ekleyebilmek için)."""
        if self._last_result_context is not None:
            self._current_context = self._last_result_context.clone()
            self.commit_requested.emit(self._current_context.clone())
    def _apply_preset(self, preset_name: str) -> None:
        """Programatik veya test için preset uygular."""
        name_map = {"sepia": 0, "vintage": 1, "cyanotype": 2, "cyberpunk": 3}
        if preset_name in name_map:
            idx = name_map[preset_name]
            self.effect_buttons[idx].setChecked(True)
            self._on_effect_selected(idx)
            self._run_live_effect()

    def _apply_vignette(self) -> None:
        self.effect_buttons[4].setChecked(True)
        self._on_effect_selected(4)
        self._run_live_effect()

    def _apply_sharpness(self) -> None:
        self.effect_buttons[5].setChecked(True)
        self._on_effect_selected(5)
        self._run_live_effect()

    def _apply_blur(self) -> None:
        self.effect_buttons[6].setChecked(True)
        self._on_effect_selected(6)
        self._run_live_effect()

    def _apply_clahe(self) -> None:
        self.effect_buttons[7].setChecked(True)
        self._on_effect_selected(7)
        self._run_live_effect()

    def _apply_sketch(self) -> None:
        self.effect_buttons[8].setChecked(True)
        self._on_effect_selected(8)
        self._run_live_effect()

    def _apply_border(self, mode: str = "solid") -> None:
        self.effect_buttons[9].setChecked(True)
        self._on_effect_selected(9)
        modes = {"solid": 0, "polaroid": 1, "rounded_corners": 2}
        if mode in modes:
            self.border_style_combo.setCurrentIndex(modes[mode])
        self._run_live_effect()

    def retranslate(self) -> None:
        """Dili dinamik olarak günceller."""
        self.selector_group.setTitle(_("group_presets"))
        self.params_group.setTitle(_("group_effect_params"))

        keys = [
            "effect_sepia", "effect_vintage", "effect_cyanotype", "effect_cyberpunk",
            "effect_vignette", "effect_sharpness", "effect_blur", "effect_clahe",
            "effect_sketch", "effect_borders"
        ]
        for btn, k in zip(self.effect_buttons, keys):
            btn.setText(_(k))

        self.clear_btn.setText(_("btn_clear_effect"))
        self.commit_btn.setText(_("btn_commit_effect"))

        self.sepia_lbl.setText(_("label_intensity", val=self.sepia_slider.value()))
        self.vin_int_lbl.setText(_("label_intensity", val=self.vin_int_slider.value()))
        self.vin_grain_lbl.setText(_("label_grain", val=self.vin_grain_slider.value()))
        self.cyan_lbl.setText(_("label_intensity", val=self.cyan_slider.value()))
        self.cyber_lbl.setText(_("label_intensity", val=self.cyber_slider.value()))
        self.vig_op_lbl.setText(_("label_opacity", val=self.vig_op_slider.value()))
        self.vig_rad_lbl.setText(_("label_radius", val=f"{self.vig_rad_slider.value()/100:.2f}"))
        self.vig_fea_lbl.setText(_("label_feather", val=self.vig_fea_slider.value()))
        self.sharp_amt_lbl.setText(_("label_amount", val=f"{self.sharp_amt_slider.value()/10:.1f}"))
        self.sharp_rad_lbl.setText(_("label_radius", val=f"{self.sharp_rad_slider.value()/10:.1f}"))
        self.sharp_cla_lbl.setText(_("label_clarity", val=f"{self.sharp_cla_slider.value()/10:.1f}"))
        self.blur_mode_lbl.setText(_("label_blur_mode"))
        self.blur_rad_lbl.setText(_("label_blur_radius", val=self.blur_rad_slider.value()))
        self.blur_ang_lbl.setText(_("label_motion_angle", val=self.blur_ang_slider.value()))
        self.clahe_clip_lbl.setText(_("label_clip_limit", val=f"{self.clahe_clip_slider.value()/10:.1f}"))
        self.clahe_grid_lbl.setText(_("label_grid_size", val=self.clahe_grid_slider.value()))
        self.sketch_mode_lbl.setText(_("label_sketch_mode"))
        self.border_style_lbl.setText(_("label_border_mode"))
        self.border_w_lbl.setText(_("label_border_width", val=self.border_w_slider.value()))
        self.border_rad_lbl.setText(_("label_corner_radius", val=self.border_rad_slider.value()))
