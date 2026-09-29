"""Test Armatürleri ve Sentetik Görsel Üreticileri (Synthetic Image Fixtures)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple
import numpy as np
from PIL import Image
import pytest

from image_toolbox.core.context import ImageContext


@pytest.fixture
def rgb_gradient_image() -> Image.Image:
    """Yatay renk geçişli 200x200 RGB sentetik test görseli."""
    w, h = 200, 200
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for x in range(w):
        r = int(x / w * 255)
        g = int((1.0 - x / w) * 255)
        b = 128
        arr[:, x] = [r, g, b]
    return Image.fromarray(arr, mode="RGB")


@pytest.fixture
def rgba_image() -> Image.Image:
    """Şeffaf dairesel pencereli 200x200 RGBA sentetik test görseli."""
    w, h = 200, 200
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = 200
    arr[:, :, 1] = 100
    arr[:, :, 2] = 50
    # Alfa kanalında radyal şeffaflık
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - 100) ** 2 + (y - 100) ** 2)
    alpha = np.clip(dist * 2.5, 0, 255).astype(np.uint8)
    arr[:, :, 3] = alpha
    return Image.fromarray(arr, mode="RGBA")


@pytest.fixture
def rgb_context(rgb_gradient_image: Image.Image) -> ImageContext:
    """RGB ImageContext armatürü."""
    return ImageContext(pil_image=rgb_gradient_image.copy(), source_format="PNG")


@pytest.fixture
def rgba_context(rgba_image: Image.Image) -> ImageContext:
    """RGBA ImageContext armatürü."""
    return ImageContext(pil_image=rgba_image.copy(), source_format="PNG")


@pytest.fixture
def temp_image_file(tmp_path: Path, rgb_gradient_image: Image.Image) -> Path:
    """Geçici diske yazılmış RGB JPEG dosyası."""
    p = tmp_path / "test_sample.jpg"
    rgb_gradient_image.save(p, format="JPEG", quality=95)
    return p
