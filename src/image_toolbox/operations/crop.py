"""Smart / Ratio Cropping Operasyonu."""

from __future__ import annotations

from typing import Any, Optional, Tuple, Union
from PIL import Image

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


@register_operation(name="crop")
class CropOperation(BaseOperation):
    """En-boy oranına veya piksel koordinatlarına göre görsel kırpma operasyonu."""

    name = "crop"
    description = "Smart ratio cropping (1:1, 16:9, 4:3, 9:16) or pixel bounds cropping"
    category = "geometry"

    RATIO_PRESETS = {
        "1:1": 1.0,
        "16:9": 16.0 / 9.0,
        "9:16": 9.0 / 16.0,
        "4:3": 4.0 / 3.0,
        "3:4": 3.0 / 4.0,
        "2:3": 2.0 / 3.0,
        "3:2": 3.0 / 2.0,
    }

    def __init__(
        self,
        ratio: Optional[Union[str, float]] = None,
        box: Optional[Tuple[int, int, int, int]] = None,
        gravity: str = "center",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            ratio=ratio,
            box=box,
            gravity=gravity.lower(),
            **kwargs,
        )

    def validate(self) -> None:
        ratio = self.params.get("ratio")
        box = self.params.get("box")
        gravity = self.params.get("gravity", "center")

        if ratio is None and box is None:
            raise ValidationError("CropOperation için 'ratio' veya 'box' (x1, y1, x2, y2) belirtilmelidir.")

        if ratio is not None:
            if isinstance(ratio, str) and ratio not in self.RATIO_PRESETS:
                try:
                    parts = ratio.split(":")
                    if len(parts) == 2:
                        w_r, h_r = float(parts[0]), float(parts[1])
                        if w_r <= 0 or h_r <= 0:
                            raise ValueError()
                    else:
                        float(ratio)
                except ValueError:
                    raise ValidationError(
                        f"Geçersiz oran formatı: '{ratio}'. Örnek: '16:9', '1:1' veya sayısal oran (1.777)."
                    )
            elif isinstance(ratio, (int, float)) and ratio <= 0:
                raise ValidationError("Oran pozitif bir sayı olmalıdır.")

        if box is not None:
            if len(box) != 4:
                raise ValidationError("Kutu koordinatları 4 elemanlı olmalıdır: (x1, y1, x2, y2)")
            x1, y1, x2, y2 = box
            if x2 <= x1 or y2 <= y1:
                raise ValidationError(f"Geçersiz kırpma kutusu: ({x1}, {y1}, {x2}, y2) -> x2>x1 ve y2>y1 olmalıdır.")

        valid_gravities = ("center", "top", "bottom", "left", "right")
        if gravity not in valid_gravities:
            raise ValidationError(f"Geçersiz gravity: '{gravity}'. Geçerli değerler: {valid_gravities}")

    def apply(self, context: ImageContext) -> ImageContext:
        img = context.pil_image
        w, h = img.size
        box = self.params.get("box")
        ratio_val = self.params.get("ratio")
        gravity = self.params.get("gravity", "center")

        if box is not None:
            x1, y1, x2, y2 = box
            # Sınır güvenlik kırpması
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(x1 + 1, min(w, x2))
            y2 = max(y1 + 1, min(h, y2))
            cropped = img.crop((x1, y1, x2, y2))
        else:
            # Hedef oranı hesapla
            target_ratio: float
            if isinstance(ratio_val, str):
                if ratio_val in self.RATIO_PRESETS:
                    target_ratio = self.RATIO_PRESETS[ratio_val]
                else:
                    parts = ratio_val.split(":")
                    target_ratio = float(parts[0]) / float(parts[1])
            else:
                target_ratio = float(ratio_val)

            current_ratio = w / h

            if current_ratio > target_ratio:
                # Mevcut görsel çok geniş, kenarlardan kırpılacak
                crop_w = int(round(h * target_ratio))
                crop_h = h
                if gravity == "left":
                    x1 = 0
                elif gravity == "right":
                    x1 = w - crop_w
                else:  # center, top, bottom
                    x1 = (w - crop_w) // 2
                y1 = 0
            else:
                # Mevcut görsel çok uzun, üst/alttan kırpılacak
                crop_w = w
                crop_h = int(round(w / target_ratio))
                x1 = 0
                if gravity == "top":
                    y1 = 0
                elif gravity == "bottom":
                    y1 = h - crop_h
                else:  # center, left, right
                    y1 = (h - crop_h) // 2

            cropped = img.crop((x1, y1, x1 + crop_w, y1 + crop_h))

        context.update_pil(cropped, operation_name=self.name)
        return context
