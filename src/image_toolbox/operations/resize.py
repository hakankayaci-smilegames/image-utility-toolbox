"""Aspect-Ratio Preserved Resizing Operasyonu (Fit, Fill, Pad)."""

from __future__ import annotations

from typing import Any, Optional, Tuple
from PIL import Image

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="resize", aliases=["scale"])
class ResizeOperation(BaseOperation):
    """En-boy oranını koruyarak veya serbest boyutlandırma operasyonu."""

    name = "resize"
    description = "Aspect-ratio preserved or custom resizing with fit, fill, pad modes"
    category = "geometry"

    def __init__(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        scale: Optional[float] = None,
        mode: str = "fit",
        pad_color: Tuple[int, ...] = (255, 255, 255),
        resample: Image.Resampling = Image.Resampling.LANCZOS,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            width=width,
            height=height,
            scale=scale,
            mode=mode.lower(),
            pad_color=pad_color,
            resample=resample,
            **kwargs,
        )

    def validate(self) -> None:
        scale = self.params.get("scale")
        width = self.params.get("width")
        height = self.params.get("height")
        mode = self.params.get("mode")

        if scale is None and width is None and height is None:
            raise ValidationError("ResizeOperation için 'width', 'height' veya 'scale' belirtilmelidir.")

        if scale is not None and scale <= 0:
            raise ValidationError(f"Scale değeri 0'dan büyük olmalıdır: {scale}")

        if width is not None and width <= 0:
            raise ValidationError(f"Genişlik pozitif tam sayı olmalıdır: {width}")

        if height is not None and height <= 0:
            raise ValidationError(f"Yükseklik pozitif tam sayı olmalıdır: {height}")

        valid_modes = ("fit", "fill", "pad", "exact")
        if mode not in valid_modes:
            raise ValidationError(f"Geçersiz resize modu: '{mode}'. Geçerli modlar: {valid_modes}")

    def apply(self, context: ImageContext) -> ImageContext:
        img = context.pil_image
        orig_w, orig_h = img.size
        mode = self.params["mode"]
        scale = self.params.get("scale")
        target_w = self.params.get("width")
        target_h = self.params.get("height")
        pad_color = self.params.get("pad_color", (255, 255, 255))
        resample = self.params.get("resample", Image.Resampling.LANCZOS)

        # 1. Yüzde bazlı ölçekleme
        if scale is not None:
            new_w = max(1, int(round(orig_w * scale)))
            new_h = max(1, int(round(orig_h * scale)))
            resized = img.resize((new_w, new_h), resample=resample)
            context.update_pil(resized, operation_name=self.name)
            return context

        # Sadece genişlik veya sadece yükseklik verildiyse en-boy oranını koru
        if target_w is not None and target_h is None:
            ratio = target_w / orig_w
            new_w = target_w
            new_h = max(1, int(round(orig_h * ratio)))
            resized = img.resize((new_w, new_h), resample=resample)
            context.update_pil(resized, operation_name=self.name)
            return context

        if target_h is not None and target_w is None:
            ratio = target_h / orig_h
            new_h = target_h
            new_w = max(1, int(round(orig_w * ratio)))
            resized = img.resize((new_w, new_h), resample=resample)
            context.update_pil(resized, operation_name=self.name)
            return context

        assert target_w is not None and target_h is not None

        if mode == "exact":
            resized = img.resize((target_w, target_h), resample=resample)
        elif mode == "fit":
            # En-boy oranını koruyarak hedef sınırlara sığdır
            ratio = min(target_w / orig_w, target_h / orig_h)
            new_w = max(1, int(round(orig_w * ratio)))
            new_h = max(1, int(round(orig_h * ratio)))
            resized = img.resize((new_w, new_h), resample=resample)
        elif mode == "fill":
            # Hedef kutuyu tamamen doldur ve taşan kısımları merkezden kırp
            ratio = max(target_w / orig_w, target_h / orig_h)
            new_w = max(1, int(round(orig_w * ratio)))
            new_h = max(1, int(round(orig_h * ratio)))
            scaled = img.resize((new_w, new_h), resample=resample)
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            resized = scaled.crop((left, top, left + target_w, top + target_h))
        elif mode == "pad":
            # Sığdırıp arkaplan tuvali üzerine merkezle
            ratio = min(target_w / orig_w, target_h / orig_h)
            new_w = max(1, int(round(orig_w * ratio)))
            new_h = max(1, int(round(orig_h * ratio)))
            scaled = img.resize((new_w, new_h), resample=resample)

            bg_mode = "RGBA" if context.has_alpha or len(pad_color) == 4 else "RGB"
            canvas = Image.new(bg_mode, (target_w, target_h), pad_color)
            offset_x = (target_w - new_w) // 2
            offset_y = (target_h - new_h) // 2
            if scaled.mode == "RGBA":
                canvas.paste(scaled, (offset_x, offset_y), mask=scaled.split()[3])
            else:
                canvas.paste(scaled, (offset_x, offset_y))
            resized = canvas
        else:
            raise ValidationError(f"Bilinmeyen mod: {mode}")

        context.update_pil(resized, operation_name=self.name)
        return context
