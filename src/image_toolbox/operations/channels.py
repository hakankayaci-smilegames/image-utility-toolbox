"""Channel Split & Merge Operasyonu (RGB, RGBA, HSV)."""

from __future__ import annotations

from typing import Any, Optional
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="channels", aliases=["channel_swap", "split_merge"])
class ChannelsOperation(BaseOperation):
    """RGB, RGBA ve HSV kanallarını ayrıştırma, ölçekleme ve takas etme operasyonu."""

    name = "channels"
    description = "Split, manipulate, swap, and merge RGB, RGBA, and HSV channels"
    category = "color"

    def __init__(
        self,
        swap: Optional[str] = None,
        isolate: Optional[str] = None,
        r_scale: float = 1.0,
        g_scale: float = 1.0,
        b_scale: float = 1.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            swap=swap.upper() if swap else None,
            isolate=isolate.upper() if isolate else None,
            r_scale=float(r_scale),
            g_scale=float(g_scale),
            b_scale=float(b_scale),
            **kwargs,
        )

    def validate(self) -> None:
        swap = self.params.get("swap")
        isolate = self.params.get("isolate")

        if swap and sorted(swap) != sorted("RGB"):
            raise ValidationError(f"Geçersiz kanal takası: '{swap}'. 'RGB' permütasyonu olmalıdır (örn: 'BGR', 'GRB').")

        if isolate and isolate not in ("R", "G", "B", "A", "H", "S", "V"):
            raise ValidationError(f"Geçersiz izolasyon kanalı: '{isolate}'. Seçenekler: R, G, B, A, H, S, V.")

    def apply(self, context: ImageContext) -> ImageContext:
        swap = self.params.get("swap")
        isolate = self.params.get("isolate")
        r_s = self.params.get("r_scale", 1.0)
        g_s = self.params.get("g_scale", 1.0)
        b_s = self.params.get("b_scale", 1.0)

        arr = context.np_array
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            rgb = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        elif arr.ndim == 3:
            rgb = arr
            alpha = None
        else:
            rgb = np.repeat(arr[:, :, np.newaxis], 3, axis=2)
            alpha = None

        # 1. Tek Kanal İzolasyonu
        if isolate:
            if isolate == "R":
                ch = rgb[:, :, 0]
            elif isolate == "G":
                ch = rgb[:, :, 1]
            elif isolate == "B":
                ch = rgb[:, :, 2]
            elif isolate == "A":
                ch = alpha[:, :, 0] if alpha is not None else np.full(rgb.shape[:2], 255, dtype=np.uint8)
            elif isolate in ("H", "S", "V"):
                hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
                idx = {"H": 0, "S": 1, "V": 2}[isolate]
                ch = hsv[:, :, idx]
            else:
                raise ValidationError(f"Bilinmeyen kanal: {isolate}")

            res = cv2.cvtColor(ch, cv2.COLOR_GRAY2RGB)
            context.update_numpy(res, operation_name=self.name)
            return context

        # 2. Kanal Ölçekleme
        rgb_float = rgb.astype(np.float32)
        if r_s != 1.0:
            rgb_float[:, :, 0] *= r_s
        if g_s != 1.0:
            rgb_float[:, :, 1] *= g_s
        if b_s != 1.0:
            rgb_float[:, :, 2] *= b_s

        np.clip(rgb_float, 0, 255, out=rgb_float)
        rgb = rgb_float.astype(np.uint8)

        # 3. Kanal Takası (Swap)
        if swap:
            order = [{"R": 0, "G": 1, "B": 2}[c] for c in swap]
            rgb = rgb[:, :, order]

        if alpha is not None:
            out_arr = np.concatenate([rgb, alpha], axis=2)
        else:
            out_arr = rgb

        context.update_numpy(out_arr, operation_name=self.name)
        return context
