"""Target Size Compressor Operasyonu (BaseOperation Uyarlaması)."""

from __future__ import annotations

from typing import Any, Optional, Union

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation
from image_toolbox.services.compressor_service import TargetSizeCompressorService


@register_operation(name="compress", aliases=["target_compress", "compress_to_size"])
class TargetSizeCompressorOperation(BaseOperation):
    """Görseli belirlenen maksimum dosya boyutuna akıllıca sıkıştıran boru hattı operasyonu."""

    name = "compress"
    description = "Smart binary search and fallback downscale compression targeting explicit file size"
    category = "compression"

    def __init__(
        self,
        target_size: Union[int, float, str] = "500kb",
        format: str = "WEBP",
        min_quality: int = 40,
        max_quality: int = 100,
        strip_metadata: bool = True,
        max_iterations: int = 8,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            target_size=target_size,
            format=format.upper(),
            min_quality=int(min_quality),
            max_quality=int(max_quality),
            strip_metadata=strip_metadata,
            max_iterations=int(max_iterations),
            **kwargs,
        )
        self.service = TargetSizeCompressorService(
            min_quality=int(min_quality),
            max_quality=int(max_quality),
            max_iterations=int(max_iterations),
            strip_metadata=strip_metadata,
        )

    def validate(self) -> None:
        fmt = self.params.get("format", "WEBP")
        if fmt not in ("WEBP", "JPEG", "JPG"):
            raise ValidationError(f"Format 'WEBP' veya 'JPEG' olmalıdır: {fmt}")

    def apply(self, context: ImageContext) -> ImageContext:
        target_size = self.params.get("target_size", "500kb")
        fmt = self.params.get("format", "WEBP")
        strip_meta = self.params.get("strip_metadata", True)
        min_q = self.params.get("min_quality", 40)
        max_iter = self.params.get("max_iterations", 8)

        result_ctx = self.service.compress(
            context,
            target_size=target_size,
            format=fmt,
            strip_metadata=strip_meta,
            min_quality=min_q,
            max_iterations=max_iter,
        )
        return result_ctx
