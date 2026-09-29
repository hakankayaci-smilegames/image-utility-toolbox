"""Image Utility Toolbox - Masaüstü Grafik Arayüzü (GUI)."""

from __future__ import annotations

import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication

from image_toolbox.gui.main_window import MainWindow
from image_toolbox.gui.theme import apply_theme


def launch_gui(initial_file: Optional[str] = None) -> int:
    """GUI uygulamasını başlatır."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    apply_theme(app)

    window = MainWindow()
    if initial_file:
        window.load_image(initial_file)

    window.show()
    return app.exec()


__all__ = ["launch_gui", "MainWindow"]
