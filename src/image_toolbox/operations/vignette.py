"""Vignette Effect Operasyonu."""

from __future__ import annotations

import math
from typing import Any, Tuple
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="vignette")
class VignetteOperation(BaseOperation):
    """Köşe karartma / aydınlatma vinyet efekti operasyonu."""

    name = "vignette"
    description = "Vignette effect with customizable radius, feather, opacity, and color"
    category = "effects"

    def __init__(
        self,
        radius: float = 0.8,
        feather: float = 0.5,
        opacity: float = 0.7,
        color: Tuple[int, int, int] = (0, 0, 0),
        **kwargs: Any,
    ) -> None:
        super().__init__(
            radius=float(radius),
            feather=float(feather),
            opacity=float(opacity),
            color=color,
            **kwargs,
        )

    def validate(self) -> None:
        radius = self.params.get("radius", 0.8)
        feather = self.params.get("feather", 0.5)
        opacity = self.params.get("opacity", 0.7)

        if not (0.1 <= radius <= 3.0):
            raise ValidationError(f"Radius 0.1 ile 3.0 arasında olmalıdır: {radius}")

        if not (0.01 <= feather <= 1.0):
            raise ValidationError(f"Feather 0.01 ile 1.0 arasında olmalıdır: {feather}")

        if not (0.0 <= opacity <= 1.0):
            raise ValidationError(f"Opacity 0.0 ile 1.0 arasında olmalıdır: {opacity}")

    def apply(self, context: ImageContext) -> ImageContext:
        radius = self.params.get("radius", 0.8)
        feather = self.params.get("feather", 0.5)
        opacity = self.params.get("opacity", 0.7)
        vignette_color = np.array(self.params.get("color", (0, 0, 0)), dtype=np.float32)

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            rgb = arr[:, :, :3].astype(np.float32)
            alpha = arr[:, :, 3:4]
        elif arr.ndim == 3:
            rgb = arr.astype(np.float32)
            alpha = None
        else:
            rgb = np.repeat(arr[:, :, np.newaxis], 3, axis=2).astype(np.float32)
            alpha = None

        h, w = rgb.shape[:2]
        center_y, center_x = h / 2.0, w / 2.0
        max_dist = math.hypot(center_x, center_y) * radius

        y, x = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

        # İç yarıçap ve dış yarıçap
        inner_r = max_dist * (1.0 - feather)
        outer_r = max_dist

        # Mesafe faktörü (0: merkez/iç alan, 1: dış köşe)
        factor = np.clip((dist_from_center - inner_r) / (outer_r - inner_r + 1e-6), 0.0, 1.0)
        # Cosine veya smoothstep eğrisi
        factor = factor * factor * (3.0 - 2.0 * factor)
        factor = factor * opacity  # Vinyet yoğunluğu

        factor_3d = factor[:, :, np.newaxis]
        result_rgb = rgb * (1.0 - factor_3d) + vignette_color * factor_3d
        np.clip(result_rgb, 0, 255, out=result_rgb)
        result_uint8 = result_rgb.astype(np.uint8)

        if alpha is not None:
            out_arr = np.concatenate([result_uint8, alpha], axis=2)
        else:
            out_arr = result_uint8

        context.update_numpy(out_arr, operation_name=self.name)
        return context
