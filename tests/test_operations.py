"""22 Modüler Operasyonun Kapsamlı Birim Testleri."""

from __future__ import annotations

import numpy as np
from PIL import Image
import pytest

from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import registry
from image_toolbox.operations import (
    ArtisticPresetsOperation,
    BlurOperation,
    BordersOperation,
    ChannelsOperation,
    ColorBalanceOperation,
    CropOperation,
    DenoiseOperation,
    EdgeSketchOperation,
    ExifToolOperation,
    ExposureOperation,
    FormatConverterOperation,
    HistogramOperation,
    PaletteExtractorOperation,
    ResizeOperation,
    SharpnessOperation,
    SolarizeOperation,
    TargetSizeCompressorOperation,
    ThresholdOperation,
    TransformOperation,
    VibranceOperation,
    VignetteOperation,
    WatermarkOperation,
)


# 1. Resize
def test_op_resize_modes(rgb_context: ImageContext) -> None:
    # Fit
    op_fit = ResizeOperation(width=100, height=50, mode="fit")
    res = op_fit.apply(rgb_context.clone())
    assert res.size == (50, 50)

    # Fill
    op_fill = ResizeOperation(width=100, height=50, mode="fill")
    res = op_fill.apply(rgb_context.clone())
    assert res.size == (100, 50)

    # Pad
    op_pad = ResizeOperation(width=100, height=80, mode="pad", pad_color=(0, 0, 0))
    res = op_pad.apply(rgb_context.clone())
    assert res.size == (100, 80)

    # Scale
    op_scale = ResizeOperation(scale=0.5)
    res = op_scale.apply(rgb_context.clone())
    assert res.size == (100, 100)


# 2. Crop
def test_op_crop_ratios_and_box(rgb_context: ImageContext) -> None:
    op_ratio = CropOperation(ratio="16:9", gravity="center")
    res = op_ratio.apply(rgb_context.clone())
    w, h = res.size
    assert abs(w / h - 16 / 9) < 0.02

    op_box = CropOperation(box=(20, 30, 80, 90))
    res_box = op_box.apply(rgb_context.clone())
    assert res_box.size == (60, 60)


# 3. Transform
def test_op_transform(rgb_context: ImageContext) -> None:
    op_rot = TransformOperation(angle=90, flip_h=True)
    res = op_rot.apply(rgb_context.clone())
    assert res.size == (200, 200)


# 4. Color Balance
def test_op_color_balance(rgb_context: ImageContext) -> None:
    op_warm = ColorBalanceOperation(kelvin=3500.0, tint=10.0)
    res = op_warm.apply(rgb_context.clone())
    arr = res.np_array
    # Sıcak ayarda kırmızı oranı mavi oranına göre yükselmeli
    assert arr[:, :, 0].mean() >= arr[:, :, 2].mean()


# 5. Exposure
def test_op_exposure(rgb_context: ImageContext) -> None:
    op_exp = ExposureOperation(brightness=20.0, contrast=1.2, exposure=1.0, gamma=1.1)
    res = op_exp.apply(rgb_context.clone())
    assert res.size == (200, 200)
    assert res.np_array.mean() > rgb_context.np_array.mean()


# 6. Vibrance
def test_op_vibrance(rgb_context: ImageContext) -> None:
    op_vib = VibranceOperation(vibrance=0.5, saturation=1.2, protect_skin_tones=True)
    res = op_vib.apply(rgb_context.clone())
    assert res.size == (200, 200)


# 7. Sharpness
def test_op_sharpness(rgb_context: ImageContext) -> None:
    op_sharp = SharpnessOperation(amount=1.5, radius=1.2, clarity=0.5)
    res = op_sharp.apply(rgb_context.clone())
    assert res.size == (200, 200)


# 8. Blur Suite
def test_op_blur_suite(rgb_context: ImageContext) -> None:
    for mode in ("gaussian", "box", "motion", "tilt_shift"):
        op = BlurOperation(mode=mode, radius=2.0)
        res = op.apply(rgb_context.clone())
        assert res.size == (200, 200)


# 9. Denoise
def test_op_denoise(rgb_context: ImageContext) -> None:
    op_bilateral = DenoiseOperation(mode="bilateral", diameter=5)
    res = op_bilateral.apply(rgb_context.clone())
    assert res.size == (200, 200)


# 10. Vignette
def test_op_vignette(rgb_context: ImageContext) -> None:
    op_vig = VignetteOperation(radius=0.7, feather=0.4, opacity=0.8)
    res = op_vig.apply(rgb_context.clone())
    assert res.size == (200, 200)
    # Köşeler merkezden daha karanlık olmalı
    arr = res.np_array
    corner_val = arr[0, 0, :].mean()
    center_val = arr[100, 100, :].mean()
    assert corner_val <= center_val


# 11. Watermark
def test_op_watermark_text(rgb_context: ImageContext) -> None:
    op_wm = WatermarkOperation(text="Antigravity Test", anchor="bottom-right", opacity=0.8)
    res = op_wm.apply(rgb_context.clone())
    assert res.size == (200, 200)


# 12. Borders
def test_op_borders(rgb_context: ImageContext) -> None:
    # Solid
    op_solid = BordersOperation(mode="solid", width=10, color=(0, 255, 0))
    res_solid = op_solid.apply(rgb_context.clone())
    assert res_solid.size == (220, 220)

    # Polaroid
    op_polaroid = BordersOperation(mode="polaroid", width=10, bottom_extra=30)
    res_pol = op_polaroid.apply(rgb_context.clone())
    assert res_pol.size == (220, 250)

    # Rounded Corners
    op_rc = BordersOperation(mode="rounded_corners", radius=20)
    res_rc = op_rc.apply(rgb_context.clone())
    assert res_rc.has_alpha


# 13. Format Converter
def test_op_converter(rgb_context: ImageContext) -> None:
    op_conv = FormatConverterOperation(format="WEBP", quality=90)
    res = op_conv.apply(rgb_context.clone())
    assert res.source_format == "WEBP"


# 14. EXIF Tool
def test_op_exif_sanitizer(rgb_context: ImageContext) -> None:
    op_exif = ExifToolOperation(action="strip_all")
    res = op_exif.apply(rgb_context.clone())
    assert res.metadata.get("exif_stripped") is True


# 15. Artistic Presets
def test_op_artistic_presets(rgb_context: ImageContext) -> None:
    for preset in ("sepia", "vintage", "cyanotype", "cyberpunk"):
        op = ArtisticPresetsOperation(preset=preset, intensity=1.0)
        res = op.apply(rgb_context.clone())
        assert res.size == (200, 200)


# 16. Edge & Sketch
def test_op_edge_sketch(rgb_context: ImageContext) -> None:
    for mode in ("canny", "sobel", "sketch"):
        op = EdgeSketchOperation(mode=mode)
        res = op.apply(rgb_context.clone())
        assert res.size == (200, 200)


# 17. Solarize & Invert
def test_op_solarize(rgb_context: ImageContext) -> None:
    op_inv = SolarizeOperation(mode="invert")
    res_inv = op_inv.apply(rgb_context.clone())
    assert res_inv.size == (200, 200)

    op_sol = SolarizeOperation(mode="solarize", threshold=100)
    res_sol = op_sol.apply(rgb_context.clone())
    assert res_sol.size == (200, 200)


# 18. Histogram / CLAHE
def test_op_histogram(rgb_context: ImageContext) -> None:
    op_clahe = HistogramOperation(mode="clahe", clip_limit=3.0)
    res = op_clahe.apply(rgb_context.clone())
    assert res.size == (200, 200)


# 19. Color Palette Extractor
def test_op_palette_extractor(rgb_context: ImageContext) -> None:
    op_pal = PaletteExtractorOperation(k=5, render_bar=True, bar_height=20)
    res = op_pal.apply(rgb_context.clone())
    assert "palette" in res.metadata
    palette = res.metadata["palette"]
    assert len(palette) == 5
    assert "hex" in palette[0]
    assert "percentage" in palette[0]
    assert res.height == 220  # 200 + 20 bar


# 20. Threshold / Binarize
def test_op_threshold(rgb_context: ImageContext) -> None:
    for mode in ("otsu", "adaptive", "fixed"):
        op = ThresholdOperation(mode=mode)
        res = op.apply(rgb_context.clone())
        assert res.size == (200, 200)


# 21. Channels
def test_op_channels(rgb_context: ImageContext) -> None:
    op_swap = ChannelsOperation(swap="BGR")
    res_swap = op_swap.apply(rgb_context.clone())
    assert res_swap.size == (200, 200)

    op_iso = ChannelsOperation(isolate="R")
    res_iso = op_iso.apply(rgb_context.clone())
    assert res_iso.size == (200, 200)


# 22. Target Size Compressor Operation
def test_op_target_compressor(rgb_context: ImageContext) -> None:
    op_comp = TargetSizeCompressorOperation(target_size="15kb", format="WEBP")
    res = op_comp.apply(rgb_context.clone())
    assert len(res.to_bytes("WEBP")) <= 15 * 1024
