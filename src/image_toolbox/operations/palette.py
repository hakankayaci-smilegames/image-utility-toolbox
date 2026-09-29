"""Color Palette Extractor (K-Means Kümeleme) Operasyonu."""

from __future__ import annotations

from typing import Any, Dict, List
import cv2
import numpy as np

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB değerlerini #RRGGBB formatına çevirir."""
    return f"#{r:02X}{g:02X}{b:02X}"


@register_operation(name="palette", aliases=["color_palette", "extract_palette"])
class PaletteExtractorOperation(BaseOperation):
    """K-Means algoritması ile görseldeki en baskın K rengi çıkaran operasyon."""

    name = "palette"
    description = "Extracts top K dominant colors using K-Means clustering with HEX/RGB and percentages"
    category = "analysis"

    def __init__(
        self,
        k: int = 5,
        render_bar: bool = False,
        bar_height: int = 40,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            k=int(k),
            render_bar=render_bar,
            bar_height=int(bar_height),
            **kwargs,
        )

    def validate(self) -> None:
        k = self.params.get("k", 5)
        if not (1 <= k <= 32):
            raise ValidationError(f"Renk sayısı (k) 1 ile 32 arasında olmalıdır: {k}")

    def apply(self, context: ImageContext) -> ImageContext:
        k = self.params.get("k", 5)
        render_bar = self.params.get("render_bar", False)
        bar_height = self.params.get("bar_height", 40)

        arr = context.np_array
        if arr.ndim == 3 and arr.shape[2] == 4:
            rgb = arr[:, :, :3]
        elif arr.ndim == 3:
            rgb = arr
        else:
            rgb = np.repeat(arr[:, :, np.newaxis], 3, axis=2)

        # Hızlı K-Means için görseli makul bir boyuta küçült (örn: maks 150x150)
        h, w = rgb.shape[:2]
        sample_w = min(150, w)
        sample_h = min(150, h)
        small = cv2.resize(rgb, (sample_w, sample_h), interpolation=cv2.INTER_AREA)

        pixels = small.reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 0.2)
        _, labels, centers = cv2.kmeans(
            pixels,
            k,
            None,
            criteria,
            5,
            cv2.KMEANS_PP_CENTERS,
        )

        labels_flat = labels.flatten()
        counts = np.bincount(labels_flat, minlength=k)
        total_pixels = len(labels_flat)

        # Baskınlık oranına göre sırala
        sorted_indices = np.argsort(-counts)

        palette_list: List[Dict[str, Any]] = []
        for idx in sorted_indices:
            color = centers[idx].astype(int)
            r, g, b = int(color[0]), int(color[1]), int(color[2])
            pct = round(float(counts[idx]) / total_pixels * 100.0, 2)
            palette_list.append({
                "rgb": [r, g, b],
                "hex": rgb_to_hex(r, g, b),
                "percentage": pct,
            })

        context.metadata["palette"] = palette_list

        # Eğer talep edildiyse görselin altına renk paleti çubuğu çiz
        if render_bar:
            bar = np.zeros((bar_height, w, 3), dtype=np.uint8)
            curr_x = 0
            for item in palette_list:
                pct = item["percentage"] / 100.0
                seg_w = int(round(w * pct))
                if curr_x + seg_w > w or item == palette_list[-1]:
                    seg_w = w - curr_x
                r, g, b = item["rgb"]
                bar[:, curr_x : curr_x + seg_w] = (r, g, b)
                curr_x += seg_w

            if arr.ndim == 3 and arr.shape[2] == 4:
                alpha_bar = np.full((bar_height, w, 1), 255, dtype=np.uint8)
                bar_rgba = np.concatenate([bar, alpha_bar], axis=2)
                new_arr = np.concatenate([arr, bar_rgba], axis=0)
            else:
                new_arr = np.concatenate([arr, bar], axis=0)

            context.update_numpy(new_arr, operation_name=self.name)

        return context
