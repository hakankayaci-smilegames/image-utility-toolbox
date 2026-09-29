"""ImageContext Birim Testleri."""

from __future__ import annotations

import io
from pathlib import Path
import numpy as np
from PIL import Image
import pytest

from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import CorruptImageError


def test_context_creation_and_dimensions(rgb_context: ImageContext) -> None:
    assert rgb_context.width == 200
    assert rgb_context.height == 200
    assert rgb_context.size == (200, 200)
    assert not rgb_context.has_alpha
    assert rgb_context.source_format == "PNG"


def test_context_lazy_sync_pil_to_numpy(rgb_context: ImageContext) -> None:
    # Başlangıçta NumPy dizisi oluşturulmamış olmalı (lazy)
    assert rgb_context._np_array is None
    np_arr = rgb_context.np_array
    assert isinstance(np_arr, np.ndarray)
    assert np_arr.shape == (200, 200, 3)
    assert np_arr.dtype == np.uint8


def test_context_lazy_sync_numpy_to_pil(rgb_context: ImageContext) -> None:
    # NumPy manipülasyonu yap ve update_numpy çağır
    arr = rgb_context.np_array.copy()
    arr[:, :, 0] = 42  # Kırmızı kanalını sabitle
    rgb_context.update_numpy(arr, operation_name="custom_op")

    assert rgb_context._pil_dirty is True
    assert "custom_op" in rgb_context.history

    # PIL erişildiğinde senkronize olmalı
    pil_img = rgb_context.pil_image
    assert pil_img.size == (200, 200)
    r_sample, _, _ = pil_img.getpixel((10, 10))
    assert r_sample == 42
    assert rgb_context._pil_dirty is False


def test_context_clone_isolation(rgb_context: ImageContext) -> None:
    cloned = rgb_context.clone()
    assert cloned.size == rgb_context.size

    # Cloned görseli değiştir
    new_img = Image.new("RGB", (50, 50), (255, 0, 0))
    cloned.update_pil(new_img)

    assert cloned.size == (50, 50)
    assert rgb_context.size == (200, 200)


def test_context_to_bytes_and_save(rgb_context: ImageContext, tmp_path: Path) -> None:
    raw_webp = rgb_context.to_bytes(format="WEBP", quality=80)
    assert isinstance(raw_webp, bytes)
    assert len(raw_webp) > 0
    assert raw_webp.startswith(b"RIFF")

    out_file = tmp_path / "out.webp"
    rgb_context.save(out_file, format="WEBP")
    assert out_file.exists()
    assert out_file.stat().st_size == len(raw_webp)


def test_context_corrupt_file_raises(tmp_path: Path) -> None:
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"NOT_A_REAL_IMAGE_DATA_12345")

    with pytest.raises(CorruptImageError):
        ImageContext.from_file(corrupt_file)


def test_context_ensure_rgb_and_rgba(rgba_context: ImageContext) -> None:
    assert rgba_context.has_alpha
    rgba_context.ensure_rgb()
    assert not rgba_context.has_alpha
    assert rgba_context.pil_image.mode == "RGB"

    rgba_context.ensure_rgba()
    assert rgba_context.has_alpha
    assert rgba_context.pil_image.mode == "RGBA"
