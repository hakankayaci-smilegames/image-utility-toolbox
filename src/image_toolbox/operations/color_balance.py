"""Color Balance & Temperature Operasyonu (Kelvin / Tint)."""

from __future__ import annotations

import math
from typing import Any, Tuple
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


def kelvin_to_rgb_multipliers(kelvin: float) -> Tuple[float, float, float]:
    """Kelvin renk sıcaklığını Tanner Helland algoritmasıyla RGB çarpanlarına çevirir.
    
    6500K nötr beyaz kabul edilir (çarpan: 1.0, 1.0, 1.0).
    """
    temp = kelvin / 100.0

    # 1. Kırmızı (Red)
    if temp <= 66:
        r = 255.0
    else:
        r = 329.698727446 * math.pow(temp - 60, -0.1332047592)
        r = max(0.0, min(255.0, r))

    # 2. Yeşil (Green)
    if temp <= 66:
        g = 99.4708025861 * math.log(temp) - 161.1195681661
    else:
        g = 288.1221695283 * math.pow(temp - 60, -0.0755148492)
    g = max(0.0, min(255.0, g))

    # 3. Mavi (Blue)
    if temp >= 66:
        b = 255.0
    elif temp <= 19:
        b = 0.0
    else:
        b = 138.5177312231 * math.log(temp - 10) - 305.0447927307
        b = max(0.0, min(255.0, b))

    # 6500K nötr katsayıları
    # (6500K için Tanner Helland değerleri yaklaşık: r=255, g=254.9, b=255)
    r_factor = r / 255.0
    g_factor = g / 254.9
    b_factor = b / 255.0

    return (r_factor, g_factor, b_factor)


@register_operation(name="color_balance", aliases=["temperature", "tint"])
class ColorBalanceOperation(BaseOperation):
    """Kelvin sıcaklığı (1500K - 15000K) ve Tint (-100..+100) ayar operasyonu."""

    name = "color_balance"
    description = "Color balance, Kelvin temperature shift (warm/cold) and tint adjustment"
    category = "color"

    def __init__(
        self,
        kelvin: float = 6500.0,
        tint: float = 0.0,
        preserve_luminance: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            kelvin=float(kelvin),
            tint=float(tint),
            preserve_luminance=preserve_luminance,
            **kwargs,
        )

    def validate(self) -> None:
        kelvin = self.params.get("kelvin", 6500.0)
        tint = self.params.get("tint", 0.0)

        if not (1500.0 <= kelvin <= 20000.0):
            raise ValidationError(f"Kelvin değeri 1500 ile 20000 arasında olmalıdır: {kelvin}")

        if not (-100.0 <= tint <= 100.0):
            raise ValidationError(f"Tint değeri -100 ile +100 arasında olmalıdır: {tint}")

    def apply(self, context: ImageContext) -> ImageContext:
        kelvin = self.params.get("kelvin", 6500.0)
        tint = self.params.get("tint", 0.0)
        preserve_lum = self.params.get("preserve_luminance", True)

        arr = context.np_array.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        if has_alpha:
            rgb = arr[:, :, :3]
            alpha = arr[:, :, 3:4]
        elif arr.ndim == 3:
            rgb = arr
            alpha = None
        else:
            # Grayscale ise RGB'ye çevirip uygula
            rgb = np.repeat(arr[:, :, np.newaxis], 3, axis=2)
            alpha = None

        orig_lum = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]) if preserve_lum else None

        # 1. Kelvin çarpanları
        kr, kg, kb = kelvin_to_rgb_multipliers(kelvin)

        # 2. Tint çarpanları (Yeşil <-> Magenta)
        # Pozitif: Magenta (+R, -G, +B) | Negatif: Green (+G, -R, -B)
        tint_factor = tint / 200.0
        r_mult = kr * (1.0 + tint_factor)
        g_mult = kg * (1.0 - tint_factor)
        b_mult = kb * (1.0 + tint_factor)

        rgb[:, :, 0] *= r_mult
        rgb[:, :, 1] *= g_mult
        rgb[:, :, 2] *= b_mult

        if preserve_lum and orig_lum is not None:
            new_lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
            mask = new_lum > 1e-4
            factor = np.ones_like(new_lum)
            factor[mask] = orig_lum[mask] / new_lum[mask]
            rgb *= factor[:, :, np.newaxis]

        np.clip(rgb, 0, 255, out=rgb)

        if alpha is not None:
            out_arr = np.concatenate([rgb, alpha], axis=2).astype(np.uint8)
        else:
            out_arr = rgb.astype(np.uint8)

        context.update_numpy(out_arr, operation_name=self.name)
        return context
