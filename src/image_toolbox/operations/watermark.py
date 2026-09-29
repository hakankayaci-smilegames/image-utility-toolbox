"""Watermark Engine Operasyonu (Metin ve PNG Logo, 9 Çapa Noktası)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


ANCHORS = (
    "top-left", "top-center", "top-right",
    "center-left", "center", "center-right",
    "bottom-left", "bottom-center", "bottom-right",
)


def calculate_position(
    bg_w: int,
    bg_h: int,
    fg_w: int,
    fg_h: int,
    anchor: str,
    margin_x: int = 20,
    margin_y: int = 20,
) -> Tuple[int, int]:
    """9 çapa noktasına ve kenar boşluklarına göre konum koordinatlarını hesaplar."""
    if anchor == "top-left":
        return (margin_x, margin_y)
    elif anchor == "top-center":
        return ((bg_w - fg_w) // 2, margin_y)
    elif anchor == "top-right":
        return (bg_w - fg_w - margin_x, margin_y)
    elif anchor == "center-left":
        return (margin_x, (bg_h - fg_h) // 2)
    elif anchor == "center":
        return ((bg_w - fg_w) // 2, (bg_h - fg_h) // 2)
    elif anchor == "center-right":
        return (bg_w - fg_w - margin_x, (bg_h - fg_h) // 2)
    elif anchor == "bottom-left":
        return (margin_x, bg_h - fg_h - margin_y)
    elif anchor == "bottom-center":
        return ((bg_w - fg_w) // 2, bg_h - fg_h - margin_y)
    elif anchor == "bottom-right":
        return (bg_w - fg_w - margin_x, bg_h - fg_h - margin_y)
    return (margin_x, margin_y)


@register_operation(name="watermark")
class WatermarkOperation(BaseOperation):
    """Görsel üzerine metin veya logo filigranı yerleştirme operasyonu."""

    name = "watermark"
    description = "Text watermark with customizable font/opacity and PNG logo overlay on 9 anchor points"
    category = "overlay"

    def __init__(
        self,
        text: Optional[str] = None,
        logo_path: Optional[Union[str, Path]] = None,
        anchor: str = "bottom-right",
        opacity: float = 0.7,
        font_size: Optional[int] = None,
        color: Tuple[int, int, int] = (255, 255, 255),
        margin: int = 25,
        scale: float = 0.2,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            text=text,
            logo_path=str(logo_path) if logo_path else None,
            anchor=anchor.lower(),
            opacity=float(opacity),
            font_size=font_size,
            color=color,
            margin=int(margin),
            scale=float(scale),
            **kwargs,
        )

    def validate(self) -> None:
        text = self.params.get("text")
        logo_path = self.params.get("logo_path")
        anchor = self.params.get("anchor", "bottom-right")
        opacity = self.params.get("opacity", 0.7)

        if text is None and logo_path is None:
            raise ValidationError("WatermarkOperation için 'text' veya 'logo_path' belirtilmelidir.")

        if anchor not in ANCHORS:
            raise ValidationError(f"Geçersiz anchor: '{anchor}'. Geçerli değerler: {ANCHORS}")

        if not (0.0 <= opacity <= 1.0):
            raise ValidationError(f"Opacity 0.0 ile 1.0 arasında olmalıdır: {opacity}")

        if logo_path is not None and not Path(logo_path).exists():
            raise ValidationError(f"Logo dosyası bulunamadı: {logo_path}")

    def apply(self, context: ImageContext) -> ImageContext:
        text = self.params.get("text")
        logo_path = self.params.get("logo_path")
        anchor = self.params.get("anchor", "bottom-right")
        opacity = self.params.get("opacity", 0.7)
        color = self.params.get("color", (255, 255, 255))
        margin = self.params.get("margin", 25)
        scale = self.params.get("scale", 0.2)
        font_size = self.params.get("font_size")

        base_img = context.pil_image.convert("RGBA")
        bg_w, bg_h = base_img.size

        # Şeffaf katman oluştur
        overlay = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))

        if logo_path:
            # Logo görselini aç ve ölçekle
            logo_img = Image.open(logo_path).convert("RGBA")
            lw, lh = logo_img.size
            target_lw = max(16, int(bg_w * scale))
            target_lh = max(16, int(round(lh * (target_lw / lw))))
            logo_resized = logo_img.resize((target_lw, target_lh), Image.Resampling.LANCZOS)

            # Opaklık ayarla
            if opacity < 1.0:
                r, g, b, a = logo_resized.split()
                a = a.point(lambda p: int(p * opacity))
                logo_resized = Image.merge("RGBA", (r, g, b, a))

            pos = calculate_position(bg_w, bg_h, target_lw, target_lh, anchor, margin, margin)
            overlay.paste(logo_resized, pos, mask=logo_resized)

        elif text:
            draw = ImageDraw.Draw(overlay)
            fsize = font_size or max(14, int(bg_h * 0.04))
            try:
                # Varsayılan sistem fontu veya yüklenen font
                font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()

            # Metin sınır kutusu
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            pos = calculate_position(bg_w, bg_h, tw, th, anchor, margin, margin)

            # Opaklık kanalı ile metin çiz
            text_alpha = int(opacity * 255)
            text_color = (color[0], color[1], color[2], text_alpha)
            draw.text(pos, text, font=font, fill=text_color)

        # Alpha composite ile birleştir
        result = Image.alpha_composite(base_img, overlay)

        # Eğer orijinal görselde alfa yoksa RGB'ye geri çevir
        if not context.has_alpha:
            result = result.convert("RGB")

        context.update_pil(result, operation_name=self.name)
        return context
