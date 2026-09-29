"""EXIF Inspector & Sanitizer Operasyonu."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from PIL import ExifTags, Image
import piexif

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import ValidationError
from image_toolbox.core.registry import register_operation


def extract_exif_dict(img: Image.Image) -> Dict[str, Any]:
    """PIL görselindeki EXIF etiketlerini insan tarafından okunabilir dict formatına çevirir."""
    result: Dict[str, Any] = {}
    exif = img.getexif()
    if not exif:
        return result

    for tag_id, val in exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        if isinstance(val, bytes):
            try:
                val = val.decode("utf-8", errors="replace")
            except Exception:
                val = str(val)
        result[tag_name] = str(val)

    # GPS info IFD'si
    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
    if gps_ifd:
        gps_dict = {}
        for gps_id, gps_val in gps_ifd.items():
            gps_name = ExifTags.GPSTAGS.get(gps_id, str(gps_id))
            gps_dict[gps_name] = str(gps_val)
        result["GPSInfo"] = gps_dict

    return result


@register_operation(name="exif", aliases=["exif_tool", "sanitize_exif", "strip_exif"])
class ExifToolOperation(BaseOperation):
    """EXIF metaverisini inceleme, GPS gizleme veya tamamen temizleme operasyonu."""

    name = "exif"
    description = "EXIF metadata inspector and sanitizer (strip GPS or strip all metadata)"
    category = "metadata"

    def __init__(
        self,
        action: str = "strip_all",
        json_output_path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            action=action.lower(),
            json_output_path=json_output_path,
            **kwargs,
        )

    def validate(self) -> None:
        action = self.params.get("action", "strip_all")
        valid_actions = ("strip_all", "strip_gps", "inspect")
        if action not in valid_actions:
            raise ValidationError(f"Geçersiz EXIF aksiyonu: '{action}'. Geçerli değerler: {valid_actions}")

    def apply(self, context: ImageContext) -> ImageContext:
        action = self.params.get("action", "strip_all")
        json_path = self.params.get("json_output_path")

        img = context.pil_image
        exif_dict = extract_exif_dict(img)
        context.metadata["exif_data"] = exif_dict

        if json_path:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(exif_dict, f, indent=2, ensure_ascii=False)

        if action == "inspect":
            # Yalnızca metaveriyi context.metadata içine yazar
            return context

        if action == "strip_all":
            # Tüm EXIF metaverilerini sıfırla
            context.exif_bytes = None
            if "exif" in context.pil_image.info:
                del context.pil_image.info["exif"]
            context.metadata["exif_stripped"] = True

        elif action == "strip_gps":
            # Yalnızca GPS ve kişisel etiketleri temizle
            if context.exif_bytes:
                try:
                    exif_data = piexif.load(context.exif_bytes)
                    exif_data["GPS"] = {}
                    context.exif_bytes = piexif.dump(exif_data)
                except Exception:
                    context.exif_bytes = None

        return context
