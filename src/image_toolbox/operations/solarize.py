"""Invert & Solarize Operasyonu."""

from __future__ import annotations

from typing import Any
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="solarize", aliases=["invert", "negative"])
class SolarizeOperation(BaseOperation):
    """Renkleri tersine çevirme (negatif) veya Sabattier eşikli solarizasyon operasyonu."""

    name = "solarize"
    description = "Color inversion and threshold-based solarization (Sabattier effect)"
    category = "effects"

    def __init__(
        self,
        mode: str = "invert",
        threshold: int = 128,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            mode=mode.lower(),
            threshold=int(threshold),
            **kwargs,
        )

    def validate(self) -> None:
        mode = self.params.get("mode", "invert")
        t = self.params.get("threshold", 128)

        if mode not in ("invert", "solarize"):
            raise ValidationError(f"Geçersiz mod: '{mode}'. Geçerli modlar: 'invert', 'solarize'")

        if not (0 <= t <= 255):
            raise ValidationError(f"Eşik 0 ile 255 arasında olmalıdır: {t}")

    def apply(self, context: ImageContext) -> ImageContext:
        mode = self.params.get("mode", "invert")
        threshold = self.params.get("threshold", 128)

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            data = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        else:
            data = arr
            alpha = None

        if mode == "invert":
            result = 255 - data
        elif mode == "solarize":
            result = data.copy()
            mask = result > threshold
            result[mask] = 255 - result[mask]
        else:
            raise ValidationError(f"Bilinmeyen mod: {mode}")

        if alpha is not None:
            out_arr = np.concatenate([result, alpha], axis=2)
        else:
            out_arr = result

        context.update_numpy(out_arr, operation_name=self.name)
        return context
