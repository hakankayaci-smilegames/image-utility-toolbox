"""GUI doğrudan çalıştırma modülü (python -m image_toolbox.gui)."""

from __future__ import annotations

import sys
from image_toolbox.gui import launch_gui


if __name__ == "__main__":
    init_file = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(launch_gui(init_file))
