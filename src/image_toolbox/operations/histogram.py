"""Histogram Equalization & CLAHE Operasyonu."""

from __future__ import annotations

from typing import Any, Tuple
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="histogram", aliases=["clahe", "equalize"])
class HistogramOperation(BaseOperation):
    """Luminance kanalına uygulanan CLAHE ve global histogram eşitleme operasyonu."""

    name = "histogram"
    description = "Adaptive CLAHE and global histogram equalization on luminance channel to prevent color shift"
    category = "enhancement"

    def __init__(
        self,
        mode: str = "clahe",
        clip_limit: float = 2.5,
        tile_grid_size: Tuple[int, int] = (8, 8),
        **kwargs: Any,
    ) -> None:
        super().__init__(
            mode=mode.lower(),
            clip_limit=float(clip_limit),
            tile_grid_size=tile_grid_size,
            **kwargs,
        )

    def validate(self) -> None:
        mode = self.params.get("mode", "clahe")
        clip = self.params.get("clip_limit", 2.5)

        if mode not in ("clahe", "global"):
            raise ValidationError(f"Geçersiz mod: '{mode}'. Geçerli modlar: 'clahe', 'global'")

        if clip <= 0:
            raise ValidationError(f"Clip limit 0'dan büyük olmalıdır: {clip}")

    def apply(self, context: ImageContext) -> ImageContext:
        mode = self.params.get("mode", "clahe")
        clip = self.params.get("clip_limit", 2.5)
        tile = self.params.get("tile_grid_size", (8, 8))

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            rgb = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        elif arr.ndim == 3:
            rgb = arr
            alpha = None
        else:
            # Grayscale görsel
            if mode == "clahe":
                clahe_engine = cv2.createCLAHE(clipLimit=clip, tileGridSize=tile)
                out_gray = clahe_engine.apply(arr)
            else:
                out_gray = cv2.equalizeHist(arr)
            context.update_numpy(out_gray, operation_name=self.name)
            return context

        # Renk bozulmasını engellemek için LAB uzayına geç ve sadece L (Aydınlık) kanalını işle
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        if mode == "clahe":
            clahe_engine = cv2.createCLAHE(clipLimit=clip, tileGridSize=tile)
            eq_l = clahe_engine.apply(l_channel)
        else:
            eq_l = cv2.equalizeHist(l_channel)

        merged_lab = cv2.merge([eq_l, a_channel, b_channel])
        result_rgb = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2RGB)

        if alpha is not None:
            out_arr = np.concatenate([result_rgb, alpha], axis=2)
        else:
            out_arr = result_rgb

        context.update_numpy(out_arr, operation_name=self.name)
        return context
