"""Threshold & Binarization (Otsu ve Adaptif Eşikleme) Operasyonu."""

from __future__ import annotations

from typing import Any
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="threshold", aliases=["binarize", "otsu"])
class ThresholdOperation(BaseOperation):
    """Otsu algoritması, adaptif Gauss veya sabit eşik ile siyah-beyaz binarizasyon operasyonu."""

    name = "threshold"
    description = "Binarization using Otsu's thresholding, adaptive Gaussian, or fixed thresholding"
    category = "enhancement"

    MODES = ("otsu", "adaptive", "fixed")

    def __init__(
        self,
        mode: str = "otsu",
        threshold_value: int = 128,
        block_size: int = 11,
        c_constant: int = 2,
        invert: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            mode=mode.lower(),
            threshold_value=int(threshold_value),
            block_size=int(block_size),
            c_constant=int(c_constant),
            invert=invert,
            **kwargs,
        )

    def validate(self) -> None:
        mode = self.params.get("mode", "otsu")
        t_val = self.params.get("threshold_value", 128)
        bs = self.params.get("block_size", 11)

        if mode not in self.MODES:
            raise ValidationError(f"Geçersiz threshold modu: '{mode}'. Geçerli modlar: {self.MODES}")

        if not (0 <= t_val <= 255):
            raise ValidationError(f"Eşik değeri 0 ile 255 arasında olmalıdır: {t_val}")

        if bs % 2 == 0 or bs < 3:
            raise ValidationError(f"Block size 3'ten büyük tek sayı olmalıdır: {bs}")

    def apply(self, context: ImageContext) -> ImageContext:
        mode = self.params.get("mode", "otsu")
        t_val = self.params.get("threshold_value", 128)
        bs = self.params.get("block_size", 11)
        c_const = self.params.get("c_constant", 2)
        invert = self.params.get("invert", False)

        arr = context.np_array
        if arr.ndim == 3:
            gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
        else:
            gray = arr

        thresh_type = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY

        if mode == "otsu":
            _, bin_img = cv2.threshold(gray, 0, 255, thresh_type + cv2.THRESH_OTSU)
        elif mode == "adaptive":
            bin_img = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                thresh_type,
                bs,
                c_const,
            )
        elif mode == "fixed":
            _, bin_img = cv2.threshold(gray, t_val, 255, thresh_type)
        else:
            raise ValidationError(f"Bilinmeyen mod: {mode}")

        # RGB formatında 3 kanallı olarak döndür
        result_rgb = cv2.cvtColor(bin_img, cv2.COLOR_GRAY2RGB)
        context.update_numpy(result_rgb, operation_name=self.name)
        return context
