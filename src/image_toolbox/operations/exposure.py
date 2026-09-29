"""Brightness, Contrast & Exposure (Gamma) Operasyonu."""

from __future__ import annotations

from typing import Any
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="exposure", aliases=["brightness", "contrast", "tone"])
class ExposureOperation(BaseOperation):
    """Parlaklık, kontrast, EV pozlama ve gamma eğrisi düzenleme operasyonu."""

    name = "exposure"
    description = "Brightness, contrast, EV exposure stops, and non-linear gamma adjustment"
    category = "tone"

    def __init__(
        self,
        brightness: float = 0.0,
        contrast: float = 1.0,
        exposure: float = 0.0,
        gamma: float = 1.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            brightness=float(brightness),
            contrast=float(contrast),
            exposure=float(exposure),
            gamma=float(gamma),
            **kwargs,
        )

    def validate(self) -> None:
        b = self.params.get("brightness", 0.0)
        c = self.params.get("contrast", 1.0)
        exp = self.params.get("exposure", 0.0)
        g = self.params.get("gamma", 1.0)

        if not (-100.0 <= b <= 100.0):
            raise ValidationError(f"Parlaklık -100 ile 100 arasında olmalıdır: {b}")

        if not (0.0 <= c <= 5.0):
            raise ValidationError(f"Kontrast 0.0 ile 5.0 arasında olmalıdır: {c}")

        if not (-5.0 <= exp <= 5.0):
            raise ValidationError(f"Pozlama (EV) -5.0 ile +5.0 durak arasında olmalıdır: {exp}")

        if not (0.1 <= g <= 5.0):
            raise ValidationError(f"Gamma 0.1 ile 5.0 arasında olmalıdır: {g}")

    def apply(self, context: ImageContext) -> ImageContext:
        b = self.params.get("brightness", 0.0)
        c = self.params.get("contrast", 1.0)
        exp = self.params.get("exposure", 0.0)
        g = self.params.get("gamma", 1.0)

        arr = context.np_array.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            data = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        else:
            data = arr
            alpha = None

        # 1. EV Pozlama Durakları (Exposure Stops: 2^EV)
        if exp != 0.0:
            exp_mult = float(2.0 ** exp)
            data *= exp_mult

        # 2. Parlaklık (-100..100) -> 255 ölçeğinde kaydırma
        if b != 0.0:
            data += b * 2.55

        # 3. Kontrast (Merkez 128 etrafında ölçekleme)
        if c != 1.0:
            data = 128.0 + c * (data - 128.0)

        # 4. Gamma Düzeltmesi (V_out = 255 * (V_in / 255)^gamma)
        if g != 1.0:
            np.clip(data, 0, 255, out=data)
            norm = data / 255.0
            data = 255.0 * np.power(norm, 1.0 / g)

        np.clip(data, 0, 255, out=data)

        if alpha is not None:
            out_arr = np.concatenate([data, alpha], axis=2).astype(np.uint8)
        else:
            out_arr = data.astype(np.uint8)

        context.update_numpy(out_arr, operation_name=self.name)
        return context
