"""Borders & Framing (Çerçeve ve Yuvarlak Köşeler) Operasyonu."""

from __future__ import annotations

from typing import Any, Tuple, Union
from PIL import Image, ImageChops, ImageDraw, ImageOps

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="borders", aliases=["border", "frame", "rounded_corners"])
class BordersOperation(BaseOperation):
    """Düz çerçeve, Polaroid çerçevesi ve şeffaf yuvarlatılmış köşeler operasyonu."""

    name = "borders"
    description = "Solid borders, Polaroid-style extended bottom frames, and anti-aliased rounded corners"
    category = "decorations"

    def __init__(
        self,
        mode: str = "solid",
        width: int = 20,
        color: Tuple[int, ...] = (255, 255, 255),
        radius: int = 30,
        bottom_extra: int = 60,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            mode=mode.lower(),
            width=int(width),
            color=color,
            radius=int(radius),
            bottom_extra=int(bottom_extra),
            **kwargs,
        )

    def validate(self) -> None:
        mode = self.params.get("mode", "solid")
        w = self.params.get("width", 20)
        radius = self.params.get("radius", 30)

        valid_modes = ("solid", "polaroid", "rounded_corners")
        if mode not in valid_modes:
            raise ValidationError(f"Geçersiz çerçeve modu: '{mode}'. Geçerli modlar: {valid_modes}")

        if w < 0:
            raise ValidationError("Çerçeve kalınlığı negatif olamaz.")

        if radius < 0:
            raise ValidationError("Köşe yarıçapı negatif olamaz.")

    def apply(self, context: ImageContext) -> ImageContext:
        mode = self.params.get("mode", "solid")
        width = self.params.get("width", 20)
        color = self.params.get("color", (255, 255, 255))
        radius = self.params.get("radius", 30)
        bottom_extra = self.params.get("bottom_extra", 60)

        img = context.pil_image

        if mode == "solid":
            framed = ImageOps.expand(img, border=width, fill=color)

        elif mode == "polaroid":
            # Üst, sol, sağ eşit; alt taraf Polaroid için genişletilmiş
            framed = ImageOps.expand(
                img,
                border=(width, width, width, width + bottom_extra),
                fill=color,
            )

        elif mode == "rounded_corners":
            # Şeffaf alfa kanalı ile pürüzsüz yuvarlatılmış köşe maskesi (2x supersampling anti-aliasing)
            w, h = img.size
            img_rgba = img.convert("RGBA")

            scale = 2
            mask = Image.new("L", (w * scale, h * scale), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, w * scale, h * scale), radius=radius * scale, fill=255)
            mask = mask.resize((w, h), Image.Resampling.LANCZOS)

            # Mevcut alfa ile birleştir
            orig_alpha = img_rgba.split()[3]
            combined_alpha = ImageChops.multiply(orig_alpha, mask)

            r, g, b, _ = img_rgba.split()
            framed = Image.merge("RGBA", (r, g, b, combined_alpha))
        else:
            raise ValidationError(f"Bilinmeyen mod: {mode}")

        context.update_pil(framed, operation_name=self.name)
        return context
