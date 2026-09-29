"""Saturation & Vibrance (Ten Rengini Koruyan Akıllı Doygunluk) Operasyonu."""

from __future__ import annotations

from typing import Any
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="vibrance", aliases=["saturation"])
class VibranceOperation(BaseOperation):
    """Klasik satürasyon ve ten tonlarını koruyan akıllı vibrance operasyonu."""

    name = "vibrance"
    description = "Skin-tone aware vibrance and classic saturation adjustment"
    category = "color"

    def __init__(
        self,
        vibrance: float = 0.0,
        saturation: float = 1.0,
        protect_skin_tones: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            vibrance=float(vibrance),
            saturation=float(saturation),
            protect_skin_tones=protect_skin_tones,
            **kwargs,
        )

    def validate(self) -> None:
        v = self.params.get("vibrance", 0.0)
        s = self.params.get("saturation", 1.0)

        if not (-1.0 <= v <= 2.0):
            raise ValidationError(f"Vibrance -1.0 ile 2.0 arasında olmalıdır: {v}")

        if not (0.0 <= s <= 4.0):
            raise ValidationError(f"Satürasyon 0.0 ile 4.0 arasında olmalıdır: {s}")

    def apply(self, context: ImageContext) -> ImageContext:
        v = self.params.get("vibrance", 0.0)
        s = self.params.get("saturation", 1.0)
        protect_skin = self.params.get("protect_skin_tones", True)

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            rgb = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        elif arr.ndim == 3:
            rgb = arr
            alpha = None
        else:
            # Grayscale satürasyondan etkilenmez
            return context

        # RGB -> HSV
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
        h = hsv[:, :, 0]  # 0..180
        sat = hsv[:, :, 1] / 255.0  # 0..1
        val = hsv[:, :, 2]

        # 1. Klasik Satürasyon Çarpanı
        if s != 1.0:
            sat *= s

        # 2. Akıllı Vibrance: Düşük doymuş pikselleri daha fazla artırır
        if v != 0.0:
            boost = v * (1.0 - sat)

            if protect_skin:
                # OpenCV Hue: 0-180 (Kırmızı-Turuncu: 0-25 ve 165-180)
                # Ten tonu koruma maskesi (1: ten değil, 0: tam ten tonu)
                skin_dist_low = np.clip(np.abs(h - 12.0) / 15.0, 0.0, 1.0)
                skin_mask = skin_dist_low
                boost *= skin_mask

            sat += boost

        sat = np.clip(sat * 255.0, 0, 255)
        hsv[:, :, 1] = sat

        # HSV -> RGB
        result_rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

        if alpha is not None:
            out_arr = np.concatenate([result_rgb, alpha], axis=2)
        else:
            out_arr = result_rgb

        context.update_numpy(out_arr, operation_name=self.name)
        return context
