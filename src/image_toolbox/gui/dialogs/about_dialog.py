"""Hakkında Diyaloğu (About Dialog)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from image_toolbox import __version__
from image_toolbox.core.i18n import _


class AboutDialog(QDialog):
    """Image Utility Toolbox hakkında bilgi penceresi."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(_("action_about"))
        self.setFixedSize(420, 280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        badge_label = QLabel("PRO STUDIO")
        badge_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            color: #3B82F6;
            border: 1px solid #27272A;
            border-radius: 4px;
            padding: 4px 10px;
            background-color: #18181B;
        """)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(badge_label, 0, Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(
            f"<h2 style='color: #EDEDEF; margin: 0; text-align: center; letter-spacing: 0.5px;'>Image Utility Toolbox</h2>"
            f"<p style='color: #71717A; text-align: center; margin: 4px; font-weight: 500;'>Versiyon {__version__}</p>"
            f"<p style='color: #A1A1AA; text-align: center; font-size: 13px; line-height: 1.5; margin-top: 12px;'>"
            f"Modüler, yüksek performanslı ve arayüzden bağımsız (headless) "
            f"görüntü işleme ve sıkıştırma paketi.<br><br>"
            f"<b>Altyapı:</b> Python, PyQt6, Pillow, OpenCV-headless & NumPy"
            f"</p>"
        )
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)
