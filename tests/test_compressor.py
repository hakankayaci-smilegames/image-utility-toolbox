"""TargetSizeCompressorService ve Operasyon Birim Testleri."""

from __future__ import annotations

import pytest
from PIL import Image

from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import TargetSizeUnreachableError
from image_toolbox.services.compressor_service import (
    TargetSizeCompressorService,
    parse_size_string,
)


def test_parse_size_string() -> None:
    assert parse_size_string("500kb") == 500 * 1024
    assert parse_size_string("2mb") == 2 * 1024 * 1024
    assert parse_size_string("1024b") == 1024
    assert parse_size_string(2048) == 2048


def test_compressor_webp_success(rgb_context: ImageContext) -> None:
    service = TargetSizeCompressorService(max_iterations=8, strip_metadata=True)
    target = "10kb"  # 10240 bytes
    res_ctx = service.compress(rgb_context, target_size=target, format="WEBP")

    final_bytes = res_ctx.to_bytes(format="WEBP")
    assert len(final_bytes) <= 10 * 1024
    meta = res_ctx.metadata["compression"]
    assert meta["iterations"] <= 8
    assert meta["final_quality"] >= 40
    # Aspect ratio korunmalı: 200x200 -> Kare kalmalı
    w, h = res_ctx.size
    assert w == h


def test_compressor_jpeg_success(rgb_context: ImageContext) -> None:
    service = TargetSizeCompressorService(max_iterations=8, strip_metadata=True)
    target = "12kb"
    res_ctx = service.compress(rgb_context, target_size=target, format="JPEG")

    final_bytes = res_ctx.to_bytes(format="JPEG")
    assert len(final_bytes) <= 12 * 1024
    assert res_ctx.width == res_ctx.height


def test_compressor_fallback_downscaling(rgb_context: ImageContext) -> None:
    # 800 bayt hedefi için min_quality=40'ta bile sığmaz ve kademeli çözünürlük düşüşü devreye girer
    service = TargetSizeCompressorService(
        min_quality=40,
        fallback_scale_step=0.10,
        strip_metadata=True,
    )
    target = "800b"
    res_ctx = service.compress(rgb_context, target_size=target, format="JPEG")

    final_bytes = res_ctx.to_bytes(format="JPEG")
    assert len(final_bytes) <= 800
    meta = res_ctx.metadata["compression"]
    assert meta["fallback_scales"] > 0
    # Orijinal 200x200'den küçülmüş olmalı
    assert res_ctx.width < 200
    assert res_ctx.height < 200
    # Oran yine de korunmalı
    assert res_ctx.width == res_ctx.height


def test_compressor_unreachable_target_raises(rgb_context: ImageContext) -> None:
    # İmkansız hedef (50 bytes)
    service = TargetSizeCompressorService(min_dimension=64)
    with pytest.raises(TargetSizeUnreachableError):
        service.compress(rgb_context, target_size=50, format="WEBP")
