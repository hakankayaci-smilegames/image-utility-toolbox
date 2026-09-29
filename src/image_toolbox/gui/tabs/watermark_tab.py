"""Filigran ve İmza Sekmesi (Watermark & Branding Tab)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from image_toolbox.core.context import ImageContext
from image_toolbox.core.i18n import _
from image_toolbox.operations.watermark import WatermarkOperation


class WatermarkTab(QWidget):
    """Metin ve PNG logo filigranı ekleme sekmesi (9 çapa noktası)."""

    apply_requested = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_context: Optional[ImageContext] = None
        self._logo_path: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Metin Filigranı
        self.text_group = QGroupBox(_("group_watermark_text"))
        text_layout = QVBoxLayout(self.text_group)
        text_layout.setSpacing(10)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("© 2026 Studio")
        self.text_input.setText("© Image Utility Toolbox")
        text_layout.addWidget(self.text_input)

        layout.addWidget(self.text_group)

        # 2. Logo / Görsel Filigranı
        self.logo_group = QGroupBox(_("group_watermark_logo"))
        logo_layout = QHBoxLayout(self.logo_group)

        self.choose_logo_btn = QPushButton(_("btn_choose_logo"))
        self.choose_logo_btn.clicked.connect(self._on_choose_logo)
        self.logo_path_label = QLabel(_("no_logo_selected"))
        self.logo_path_label.setStyleSheet("color: #71717A; font-size: 12px;")

        logo_layout.addWidget(self.choose_logo_btn)
        logo_layout.addWidget(self.logo_path_label, 1)
        layout.addWidget(self.logo_group)

        # 3. 9 Çapa Noktası (Anchor Grid)
        self.anchor_group_box = QGroupBox(_("group_anchor"))
        anchor_layout = QGridLayout(self.anchor_group_box)
        anchor_layout.setSpacing(6)

        self.anchor_group = QButtonGroup(self)
        self.anchors = {}

        positions = [
            ("top-left", "anchor_tl", 0, 0),
            ("top-center", "anchor_tc", 0, 1),
            ("top-right", "anchor_tr", 0, 2),
            ("center-left", "anchor_cl", 1, 0),
            ("center", "anchor_c", 1, 1),
            ("center-right", "anchor_cr", 1, 2),
            ("bottom-left", "anchor_bl", 2, 0),
            ("bottom-center", "anchor_bc", 2, 1),
            ("bottom-right", "anchor_br", 2, 2),
        ]

        self._anchor_keys = {}
        for code, key, r, c in positions:
            rb = QRadioButton(_(key))
            if code == "bottom-right":
                rb.setChecked(True)
            self.anchor_group.addButton(rb)
            self.anchors[code] = rb
            self._anchor_keys[code] = key
            anchor_layout.addWidget(rb, r, c)

        layout.addWidget(self.anchor_group_box)

        # 4. Opaklık ve Boyut
        self.slider_group = QGroupBox(_("group_appearance"))
        slider_layout = QVBoxLayout(self.slider_group)

        self.opacity_label = QLabel(_("label_wm_opacity", val=70))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(_("label_wm_opacity", val=v))
        )

        slider_layout.addWidget(self.opacity_label)
        slider_layout.addWidget(self.opacity_slider)
        layout.addWidget(self.slider_group)

        # 5. Uygula Butonu
        self.apply_btn = QPushButton(_("btn_apply_watermark"))
        self.apply_btn.setProperty("primary", True)
        self.apply_btn.setFixedHeight(38)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        layout.addWidget(self.apply_btn)

        layout.addStretch(1)

    def set_context(self, context: Optional[ImageContext]) -> None:
        self._current_context = context

    def _on_choose_logo(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            _("dialog_logo_title"),
            "",
            "PNG Images (*.png);;All Files (*)",
        )
        if path:
            self._logo_path = path
            self.logo_path_label.setText(Path(path).name)

    def _get_selected_anchor(self) -> str:
        for code, rb in self.anchors.items():
            if rb.isChecked():
                return code
        return "bottom-right"

    def _on_apply_clicked(self) -> None:
        if self._current_context is None:
            return

        anchor = self._get_selected_anchor()
        opacity = self.opacity_slider.value() / 100.0

        if self._logo_path:
            op = WatermarkOperation(logo_path=self._logo_path, anchor=anchor, opacity=opacity)
        else:
            txt = self.text_input.text().strip() or "Image Utility Toolbox"
            op = WatermarkOperation(text=txt, anchor=anchor, opacity=opacity)

        res = op.apply(self._current_context.clone())
        self.apply_requested.emit(res)

    def retranslate(self) -> None:
        self.text_group.setTitle(_("group_watermark_text"))
        self.logo_group.setTitle(_("group_watermark_logo"))
        self.choose_logo_btn.setText(_("btn_choose_logo"))
        if not self._logo_path:
            self.logo_path_label.setText(_("no_logo_selected"))
        self.anchor_group_box.setTitle(_("group_anchor"))
        for code, key in self._anchor_keys.items():
            if code in self.anchors:
                self.anchors[code].setText(_(key))
        self.slider_group.setTitle(_("group_appearance"))
        self.opacity_label.setText(_("label_wm_opacity", val=self.opacity_slider.value()))
        self.apply_btn.setText(_("btn_apply_watermark"))

