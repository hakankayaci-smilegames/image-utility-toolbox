"""Edge & Sketch (Sobel, Canny ve Kurşun Kalem Eskiz) Operasyonu."""

from __future__ import annotations

from typing import Any
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="edge_sketch", aliases=["edge", "sketch", "canny", "sobel"])
class EdgeSketchOperation(BaseOperation):
    """Sobel, Canny kenar bulma ve sanatsal kurşun kalem eskiz efekti operasyonu."""

    name = "edge_sketch"
    description = "Edge detection (Sobel, Canny) and artistic pencil sketch effect"
    category = "artistic"

    MODES = ("canny", "sobel", "sketch")

    def __init__(
        self,
        mode: str = "sketch",
        low_threshold: float = 50.0,
        high_threshold: float = 150.0,
        blur_radius: float = 21.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            mode=mode.lower(),
            low_threshold=float(low_threshold),
            high_threshold=float(high_threshold),
            blur_radius=float(blur_radius),
            **kwargs,
        )

    def validate(self) -> None:
        mode = self.params.get("mode", "sketch")
        if mode not in self.MODES:
            raise ValidationError(f"Geçersiz mod: '{mode}'. Geçerli modlar: {self.MODES}")

    def apply(self, context: ImageContext) -> ImageContext:
        mode = self.params.get("mode", "sketch")
        low_t = self.params.get("low_threshold", 50.0)
        high_t = self.params.get("high_threshold", 150.0)
        blur_r = self.params.get("blur_radius", 21.0)

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            rgb = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        elif arr.ndim == 3:
            rgb = arr
            alpha = None
        else:
            rgb = arr
            alpha = None

        # Gri tonlamaya çevir
        if rgb.ndim == 3:
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        else:
            gray = rgb

        if mode == "canny":
            edges = cv2.Canny(gray, int(low_t), int(high_t))
            result = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

        elif mode == "sobel":
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            mag = np.hypot(sobelx, sobely)
            mag = np.clip((mag / mag.max() * 255.0) if mag.max() > 0 else 0, 0, 255).astype(np.uint8)
            result = cv2.cvtColor(mag, cv2.COLOR_GRAY2RGB)

        elif mode == "sketch":
            # 1. Gri tonlamanın tersini al
            inverted = 255 - gray
            # 2. Ters görseli Gaussian ile kuvvetlice bulanıklaştır
            k = int(round(blur_r))
            if k % 2 == 0:
                k += 1
            blurred = cv2.GaussianBlur(inverted, (k, k), sigmaX=0, sigmaY=0)
            # 3. Color Dodge harmanlaması: (gray * 256) / (256 - blurred)
            dodge = cv2.divide(gray, 255 - blurred, scale=256)
            result = cv2.cvtColor(dodge, cv2.COLOR_GRAY2RGB)
        else:
            raise ValidationError(f"Bilinmeyen mod: {mode}")

        if alpha is not None:
            out_arr = np.concatenate([result, alpha], axis=2)
        else:
            out_arr = result

        context.update_numpy(out_arr, operation_name=self.name)
        return context
