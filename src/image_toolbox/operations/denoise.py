"""Denoise Operasyonu (Fast Non-Local Means & Bilateral)."""

from __future__ import annotations

from typing import Any
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="denoise", aliases=["nlmeans", "bilateral"])
class DenoiseOperation(BaseOperation):
    """Görseldeki parazit ve kumlanmayı gideren filtreleme operasyonu."""

    name = "denoise"
    description = "Noise reduction using Fast Non-Local Means or edge-preserving Bilateral filter"
    category = "enhancement"

    def __init__(
        self,
        mode: str = "bilateral",
        strength: float = 10.0,
        diameter: int = 9,
        sigma_color: float = 75.0,
        sigma_space: float = 75.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            mode=mode.lower(),
            strength=float(strength),
            diameter=int(diameter),
            sigma_color=float(sigma_color),
            sigma_space=float(sigma_space),
            **kwargs,
        )

    def validate(self) -> None:
        mode = self.params.get("mode", "bilateral")
        valid_modes = ("bilateral", "nlmeans")
        if mode not in valid_modes:
            raise ValidationError(f"Geçersiz denoise modu: '{mode}'. Geçerli modlar: {valid_modes}")

    def apply(self, context: ImageContext) -> ImageContext:
        mode = self.params.get("mode", "bilateral")
        strength = self.params.get("strength", 10.0)
        d = self.params.get("diameter", 9)
        sc = self.params.get("sigma_color", 75.0)
        ss = self.params.get("sigma_space", 75.0)

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            data = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        else:
            data = arr
            alpha = None

        if mode == "bilateral":
            # Bilateral filtre: kenarları koruyarak yumuşatır
            denoised = cv2.bilateralFilter(data, d=d, sigmaColor=sc, sigmaSpace=ss)
        elif mode == "nlmeans":
            if data.ndim == 3 and data.shape[2] == 3:
                denoised = cv2.fastNlMeansDenoisingColored(
                    data,
                    None,
                    h=strength,
                    hColor=strength,
                    templateWindowSize=7,
                    searchWindowSize=21,
                )
            else:
                denoised = cv2.fastNlMeansDenoising(
                    data,
                    None,
                    h=strength,
                    templateWindowSize=7,
                    searchWindowSize=21,
                )
        else:
            raise ValidationError(f"Bilinmeyen mod: {mode}")

        if alpha is not None:
            out_arr = np.concatenate([denoised, alpha], axis=2)
        else:
            out_arr = denoised

        context.update_numpy(out_arr, operation_name=self.name)
        return context
