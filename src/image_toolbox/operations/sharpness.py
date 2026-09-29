"""Sharpness & Clarity (Unsharp Masking ve High-Pass) Operasyonu."""

from __future__ import annotations

from typing import Any
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="sharpness", aliases=["clarity", "unsharp_mask"])
class SharpnessOperation(BaseOperation):
    """Unsharp masking ve high-pass clarity ile görsel keskinleştirme operasyonu."""

    name = "sharpness"
    description = "Unsharp masking, clarity, and high-pass edge sharpening"
    category = "enhancement"

    def __init__(
        self,
        amount: float = 1.0,
        radius: float = 1.5,
        threshold: float = 0.0,
        clarity: float = 0.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            amount=float(amount),
            radius=float(radius),
            threshold=float(threshold),
            clarity=float(clarity),
            **kwargs,
        )

    def validate(self) -> None:
        amt = self.params.get("amount", 1.0)
        r = self.params.get("radius", 1.5)
        t = self.params.get("threshold", 0.0)
        c = self.params.get("clarity", 0.0)

        if not (0.0 <= amt <= 10.0):
            raise ValidationError(f"Amount 0.0 ile 10.0 arasında olmalıdır: {amt}")

        if not (0.1 <= r <= 20.0):
            raise ValidationError(f"Radius 0.1 ile 20.0 arasında olmalıdır: {r}")

        if not (0.0 <= t <= 50.0):
            raise ValidationError(f"Threshold 0.0 ile 50.0 arasında olmalıdır: {t}")

        if not (-2.0 <= c <= 2.0):
            raise ValidationError(f"Clarity -2.0 ile 2.0 arasında olmalıdır: {c}")

    def apply(self, context: ImageContext) -> ImageContext:
        amt = self.params.get("amount", 1.0)
        r = self.params.get("radius", 1.5)
        t = self.params.get("threshold", 0.0)
        c = self.params.get("clarity", 0.0)

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            img_data = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        else:
            img_data = arr
            alpha = None

        float_data = img_data.astype(np.float32)

        # 1. Unsharp Masking
        if amt > 0.0:
            blurred = cv2.GaussianBlur(float_data, (0, 0), sigmaX=r, sigmaY=r)
            diff = float_data - blurred
            if t > 0.0:
                mask = np.abs(diff) >= t
                diff = diff * mask
            float_data += amt * diff

        # 2. Clarity (Orta ton geniş yarıçaplı yerel kontrast)
        if c != 0.0:
            clarity_blurred = cv2.GaussianBlur(float_data, (0, 0), sigmaX=15.0, sigmaY=15.0)
            float_data += c * (float_data - clarity_blurred)

        np.clip(float_data, 0, 255, out=float_data)
        out_uint8 = float_data.astype(np.uint8)

        if alpha is not None:
            out_arr = np.concatenate([out_uint8, alpha], axis=2)
        else:
            out_arr = out_uint8

        context.update_numpy(out_arr, operation_name=self.name)
        return context
