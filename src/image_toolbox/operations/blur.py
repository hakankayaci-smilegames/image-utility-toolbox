"""Blur Suite (Gaussian, Box, Motion, Tilt-Shift) Operasyonu."""

from __future__ import annotations

import math
from typing import Any
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="blur", aliases=["gaussian_blur", "motion_blur", "tilt_shift"])
class BlurOperation(BaseOperation):
    """Gaussian, Box, Motion ve Tilt-Shift bulanıklaştırma operasyon takımı."""

    name = "blur"
    description = "Blur suite: Gaussian, Box, Motion, and Tilt-Shift miniature blur"
    category = "filters"

    def __init__(
        self,
        mode: str = "gaussian",
        radius: float = 3.0,
        angle: float = 0.0,
        focus_position: float = 0.5,
        focus_width: float = 0.25,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            mode=mode.lower(),
            radius=float(radius),
            angle=float(angle),
            focus_position=float(focus_position),
            focus_width=float(focus_width),
            **kwargs,
        )

    def validate(self) -> None:
        mode = self.params.get("mode", "gaussian")
        radius = self.params.get("radius", 3.0)
        valid_modes = ("gaussian", "box", "motion", "tilt_shift")

        if mode not in valid_modes:
            raise ValidationError(f"Geçersiz bulanıklık modu: '{mode}'. Geçerli modlar: {valid_modes}")

        if radius <= 0:
            raise ValidationError(f"Radius değeri 0'dan büyük olmalıdır: {radius}")

    def apply(self, context: ImageContext) -> ImageContext:
        mode = self.params.get("mode", "gaussian")
        radius = self.params.get("radius", 3.0)
        angle = self.params.get("angle", 0.0)
        focus_pos = self.params.get("focus_position", 0.5)
        focus_w = self.params.get("focus_width", 0.25)

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            data = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        else:
            data = arr
            alpha = None

        h, w = data.shape[:2]

        if mode == "gaussian":
            # ksize 0 olunca sigmaX'ten otomatik hesaplanır
            blurred = cv2.GaussianBlur(data, (0, 0), sigmaX=radius, sigmaY=radius)

        elif mode == "box":
            k = max(1, int(round(radius * 2 + 1)))
            if k % 2 == 0:
                k += 1
            blurred = cv2.boxFilter(data, -1, (k, k))

        elif mode == "motion":
            k = max(3, int(round(radius * 2 + 1)))
            kernel = np.zeros((k, k), dtype=np.float32)
            rad = math.radians(angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            center = (k - 1) / 2.0

            for i in range(k):
                offset = i - center
                x = int(round(center + offset * cos_a))
                y = int(round(center + offset * sin_a))
                if 0 <= x < k and 0 <= y < k:
                    kernel[y, x] = 1.0

            k_sum = kernel.sum()
            if k_sum > 0:
                kernel /= k_sum
            else:
                kernel[k // 2, k // 2] = 1.0
            blurred = cv2.filter2D(data, -1, kernel)

        elif mode == "tilt_shift":
            # Tilt-Shift: Odak bandı net kalırken yukarı ve aşağı kademeli bulanıklaşır
            base_blurred = cv2.GaussianBlur(data, (0, 0), sigmaX=radius * 2.5, sigmaY=radius * 2.5)
            y_indices = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, np.newaxis]
            # Odak noktasına olan mesafe
            dist = np.abs(y_indices - focus_pos)
            half_w = focus_w / 2.0
            mask = np.clip((dist - half_w) / (half_w + 1e-5), 0.0, 1.0)
            # Düzgün geçiş (Smoothstep: 3x^2 - 2x^3)
            mask = mask * mask * (3.0 - 2.0 * mask)

            if data.ndim == 3:
                mask_3d = mask[:, :, np.newaxis]
            else:
                mask_3d = mask

            blurred = (data * (1.0 - mask_3d) + base_blurred * mask_3d).astype(np.uint8)
        else:
            raise ValidationError(f"Bilinmeyen mod: {mode}")

        if alpha is not None:
            out_arr = np.concatenate([blurred, alpha], axis=2)
        else:
            out_arr = blurred

        context.update_numpy(out_arr, operation_name=self.name)
        return context
