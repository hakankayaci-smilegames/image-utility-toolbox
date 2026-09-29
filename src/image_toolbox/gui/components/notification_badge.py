"""Durum Bildirim Şeridi (Notification Badge / Banner Component)."""

from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
)


class NotificationBadge(QFrame):
    """Kullanıcıya engellemeden (non-blocking) geri bildirim sunan modern durum şeridi."""

    STYLES = {
        "success": {
            "bg": "#141C16",
            "border": "#10B981",
            "icon": "✓",
            "text": "#E2FBE8",
        },
        "info": {
            "bg": "#121A26",
            "border": "#3B82F6",
            "icon": "•",
            "text": "#E0EDFE",
        },
        "warning": {
            "bg": "#221A0F",
            "border": "#F59E0B",
            "icon": "!",
            "text": "#FEF3C7",
        },
        "error": {
            "bg": "#231215",
            "border": "#EF4444",
            "icon": "✕",
            "text": "#FEE2E2",
        },
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setVisible(False)
        self.setFixedHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel("✓")
        self.icon_label.setStyleSheet("font-weight: bold; font-size: 14px; background: transparent;")
        layout.addWidget(self.icon_label)

        self.message_label = QLabel("")
        self.message_label.setStyleSheet("font-size: 13px; font-weight: 500; background: transparent;")
        layout.addWidget(self.message_label, 1)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #CBD5E1;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 11px;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        layout.addWidget(self.close_btn)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

    def show_message(self, text: str, msg_type: str = "success", timeout_ms: int = 5000) -> None:
        """Belirtilen türde ve mesajla bildirimi gösterir."""
        style = self.STYLES.get(msg_type, self.STYLES["info"])
        self.icon_label.setText(style["icon"])
        self.icon_label.setStyleSheet(f"color: {style['border']}; font-weight: bold; font-size: 14px; background: transparent;")
        self.message_label.setText(text)
        self.message_label.setStyleSheet(f"color: {style['text']}; font-size: 13px; font-weight: 500; background: transparent;")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {style['bg']};
                border: 1px solid {style['border']};
                border-radius: 6px;
            }}
        """)

        self.setVisible(True)
        if timeout_ms > 0:
            self.timer.start(timeout_ms)
