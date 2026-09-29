"""Artistic Presets (Sepia, Vintage/Film Grain, Cyanotype, Cyberpunk/Neon) Operasyonu."""

from __future__ import annotations

from typing import Any
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="artistic", aliases=["preset", "filter_preset"])
class ArtisticPresetsOperation(BaseOperation):
    """Sanatsal ve nostaljik hazır görsel filtreleri (Sepia, Vintage, Cyanotype, Cyberpunk)."""

    name = "artistic"
    description = "Artistic presets: Sepia, Vintage film grain, Cyanotype monochrome, and Cyberpunk neon"
    category = "artistic"

    PRESETS = ("sepia", "vintage", "cyanotype", "cyberpunk")

    def __init__(
        self,
        preset: str = "sepia",
        intensity: float = 1.0,
        grain_amount: float = 0.15,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            preset=preset.lower(),
            intensity=float(intensity),
            grain_amount=float(grain_amount),
            **kwargs,
        )

    def validate(self) -> None:
        preset = self.params.get("preset", "sepia")
        intensity = self.params.get("intensity", 1.0)

        if preset not in self.PRESETS:
            raise ValidationError(f"Geçersiz preset: '{preset}'. Geçerli olanlar: {self.PRESETS}")

        if not (0.0 <= intensity <= 1.0):
            raise ValidationError(f"Intensity 0.0 ile 1.0 arasında olmalıdır: {intensity}")

    def apply(self, context: ImageContext) -> ImageContext:
        preset = self.params.get("preset", "sepia")
        intensity = self.params.get("intensity", 1.0)
        grain = self.params.get("grain_amount", 0.15)

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

        orig_rgb = rgb.copy()
        h, w = rgb.shape[:2]

        if preset == "sepia":
            # Standart Sepia Matrisi
            # R' = 0.393R + 0.769G + 0.189B
            # G' = 0.349R + 0.686G + 0.168B
            # B' = 0.272R + 0.534G + 0.131B
            sepia_kernel = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131],
            ], dtype=np.float32).T
            filtered = cv2.transform(rgb, sepia_kernel)

        elif preset == "vintage":
            # Sıcak renk kayması + film greni
            sepia_kernel = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131],
            ], dtype=np.float32).T
            warm = cv2.transform(rgb, sepia_kernel)
            filtered = 0.7 * warm + 0.3 * rgb

            # Film Greni (Gaussian Noise)
            if grain > 0:
                noise = np.random.normal(0, grain * 50.0, (h, w, 3)).astype(np.float32)
                filtered += noise

        elif preset == "cyanotype":
            # Klasik Prusya mavisi monokrom baskı
            gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
            # Mavi tonlama: Düşük R, orta G, yüksek B
            filtered = np.zeros_like(rgb)
            filtered[:, :, 0] = gray * 0.15   # Kırmızı
            filtered[:, :, 1] = gray * 0.55   # Yeşil
            filtered[:, :, 2] = gray * 0.95   # Mavi

        elif preset == "cyberpunk":
            # Mavi/Camgöbeği gölgeler, Pembe/Macenta parlak alanlar
            gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]) / 255.0
            filtered = np.zeros_like(rgb)
            # Gölgeler için Neon Camgöbeği (0, 220, 255), Işıklar için Neon Pembe (255, 0, 180)
            shadow_color = np.array([0, 220, 255], dtype=np.float32)
            highlight_color = np.array([255, 20, 160], dtype=np.float32)

            factor = gray[:, :, np.newaxis]
            # Kontrastı artır
            factor = np.clip((factor - 0.5) * 1.5 + 0.5, 0.0, 1.0)
            filtered = shadow_color * (1.0 - factor) + highlight_color * factor
        else:
            raise ValidationError(f"Bilinmeyen preset: {preset}")

        # Yoğunluk karıştırma
        output = orig_rgb * (1.0 - intensity) + filtered * intensity
        np.clip(output, 0, 255, out=output)
        out_uint8 = output.astype(np.uint8)

        if alpha is not None:
            out_arr = np.concatenate([out_uint8, alpha], axis=2)
        else:
            out_arr = out_uint8

        context.update_numpy(out_arr, operation_name=self.name)
        return context
