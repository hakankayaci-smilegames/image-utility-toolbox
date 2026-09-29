"""Format Converter Operasyonu (PNG, JPEG, WebP, BMP, TIFF, ICO)."""

from __future__ import annotations

from typing import Any
from PIL import Image

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


SUPPORTED_FORMATS = ("PNG", "JPEG", "JPG", "WEBP", "BMP", "TIFF", "ICO")


@register_operation(name="converter", aliases=["convert_format", "format"])
class FormatConverterOperation(BaseOperation):
    """Görsel dosya formatı ve renk profili dönüştürme operasyonu."""

    name = "converter"
    description = "Lossy/lossless format converter supporting PNG, JPEG, WebP, BMP, TIFF, and ICO"
    category = "format"

    def __init__(
        self,
        format: str = "WEBP",
        quality: int = 85,
        lossless: bool = False,
        optimize: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            format=format.upper(),
            quality=int(quality),
            lossless=lossless,
            optimize=optimize,
            **kwargs,
        )

    def validate(self) -> None:
        fmt = self.params.get("format", "WEBP")
        q = self.params.get("quality", 85)

        if fmt not in SUPPORTED_FORMATS:
            raise ValidationError(f"Desteklenmeyen format: '{fmt}'. Desteklenenler: {SUPPORTED_FORMATS}")

        if not (1 <= q <= 100):
            raise ValidationError(f"Kalite 1 ile 100 arasında olmalıdır: {q}")

    def apply(self, context: ImageContext) -> ImageContext:
        target_fmt = self.params.get("format", "WEBP")
        if target_fmt == "JPG":
            target_fmt = "JPEG"

        q = self.params.get("quality", 85)
        lossless = self.params.get("lossless", False)
        optimize = self.params.get("optimize", True)

        img = context.pil_image

        # ICO için boyut kısıtlaması (genelde maks 256x256)
        if target_fmt == "ICO":
            if img.width > 256 or img.height > 256:
                img = img.resize((256, 256), Image.Resampling.LANCZOS)

        # JPEG formatında alfa kanalı olmadığı için RGB'ye dönüştür
        if target_fmt == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img.convert("RGB"))
            img = bg

        context.source_format = target_fmt
        context.metadata["save_options"] = {
            "format": target_fmt,
            "quality": q,
            "lossless": lossless,
            "optimize": optimize,
        }

        context.update_pil(img, operation_name=self.name)
        return context
