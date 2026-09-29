"""Rotation & Flip Operasyonu (EXIF Auto-Orient Dahil)."""

from __future__ import annotations

from typing import Any, Optional, Tuple
from PIL import Image, ImageOps

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="transform", aliases=["rotate", "flip"])
class TransformOperation(BaseOperation):
    """Görsel döndürme, yatay/dikey çevirme ve EXIF otomatik yön düzeltme operasyonu."""

    name = "transform"
    description = "Rotation, horizontal/vertical flip, and EXIF-based auto orientation"
    category = "geometry"

    def __init__(
        self,
        angle: float = 0.0,
        expand: bool = True,
        flip_h: bool = False,
        flip_v: bool = False,
        auto_orient: bool = False,
        fill_color: Optional[Tuple[int, ...]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            angle=float(angle),
            expand=expand,
            flip_h=flip_h,
            flip_v=flip_v,
            auto_orient=auto_orient,
            fill_color=fill_color,
            **kwargs,
        )

    def validate(self) -> None:
        angle = self.params.get("angle")
        if not isinstance(angle, (int, float)):
            raise ValidationError(f"Açı sayısal olmalıdır: {angle}")

    def apply(self, context: ImageContext) -> ImageContext:
        img = context.pil_image
        angle = self.params.get("angle", 0.0)
        expand = self.params.get("expand", True)
        flip_h = self.params.get("flip_h", False)
        flip_v = self.params.get("flip_v", False)
        auto_orient = self.params.get("auto_orient", False)
        fill_color = self.params.get("fill_color")

        # 1. EXIF Auto-Orient
        if auto_orient:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

        # 2. Döndürme
        if angle % 360 != 0:
            if angle == 90:
                img = img.transpose(Image.Transpose.ROTATE_270)
            elif angle == 180:
                img = img.transpose(Image.Transpose.ROTATE_180)
            elif angle == 270:
                img = img.transpose(Image.Transpose.ROTATE_90)
            else:
                img = img.rotate(
                    -angle,  # Saat yönünde dönüş için ters işaret
                    resample=Image.Resampling.BICUBIC,
                    expand=expand,
                    fillcolor=fill_color,
                )

        # 3. Aynalama / Çevirme
        if flip_h:
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if flip_v:
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        context.update_pil(img, operation_name=self.name)
        return context
