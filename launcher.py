#!/usr/bin/env python3
"""PyInstaller ve bağımsız çalıştırma giriş noktası (Entrypoint)."""
import sys
from pathlib import Path

# src dizinini pythonpath'e ekle
sys.path.insert(0, str(Path(__file__).parent / "src"))

from image_toolbox.gui import launch_gui

if __name__ == "__main__":
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(launch_gui(initial_file))
