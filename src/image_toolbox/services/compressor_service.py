"""Hedef Boyutlu Akıllı Sıkıştırma Servisi (Target Size Compressor Service).

İkili Arama (Binary Search) ve Kademeli Çözünürlük Düşüşü (Fallback Downscaling)
ile belirlenen maksimum dosya boyutuna (KB/MB) ulaşır.
"""

from __future__ import annotations

import io
from typing import Any, Dict, Optional, Tuple, Union
from PIL import Image

from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import TargetSizeUnreachableError, ValidationError


def parse_size_string(size_val: Union[int, float, str]) -> int:
    """'500kb', '2mb', '1024b' veya tamsayı boyut değerlerini bayt cinsine çevirir."""
    if isinstance(size_val, (int, float)):
        return int(size_val)

    s = str(size_val).strip().lower()
    if s.endswith("mb") or s.endswith("m"):
        num = float(s.rstrip("mb"))
        return int(num * 1024 * 1024)
    elif s.endswith("kb") or s.endswith("k"):
        num = float(s.rstrip("kb"))
        return int(num * 1024)
    elif s.endswith("b"):
        num = float(s.rstrip("b"))
        return int(num)
    else:
        return int(float(s))


class TargetSizeCompressorService:
    """Maksimum dosya boyutunu hedefleyen akıllı sıkıştırma motoru."""

    def __init__(
        self,
        min_quality: int = 40,
        max_quality: int = 100,
        max_iterations: int = 8,
        fallback_scale_step: float = 0.08,
        min_dimension: int = 48,
        strip_metadata: bool = True,
    ) -> None:
        self.min_quality = min_quality
        self.max_quality = max_quality
        self.max_iterations = max_iterations
        self.fallback_scale_step = fallback_scale_step
        self.min_dimension = min_dimension
        self.strip_metadata = strip_metadata

    def _test_compress(
        self,
        img: Image.Image,
        fmt: str,
        quality: int,
        strip_meta: bool,
        exif_bytes: Optional[bytes],
        icc_profile: Optional[bytes],
    ) -> bytes:
        """PIL görselini RAM içinde sıkıştırıp byte boyutunu döndürür."""
        bio = io.BytesIO()
        target_fmt = fmt.upper()
        if target_fmt == "JPG":
            target_fmt = "JPEG"

        # JPEG için alfa kanalını beyaz arka plana dök
        if target_fmt == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img.convert("RGB"))
            img_to_save = bg
        else:
            img_to_save = img

        save_kwargs: Dict[str, Any] = {
            "format": target_fmt,
            "quality": quality,
            "optimize": True,
        }

        if not strip_meta:
            if exif_bytes and target_fmt in ("JPEG", "WEBP"):
                save_kwargs["exif"] = exif_bytes
            if icc_profile:
                save_kwargs["icc_profile"] = icc_profile

        img_to_save.save(bio, **save_kwargs)
        return bio.getvalue()

    def compress(
        self,
        context: ImageContext,
        target_size: Union[int, float, str],
        format: str = "WEBP",
        strip_metadata: Optional[bool] = None,
        min_quality: Optional[int] = None,
        max_iterations: Optional[int] = None,
    ) -> ImageContext:
        """Görseli hedef dosya boyutuna ikili arama ve çözünürlük düşüşü ile sıkıştırır.
        
        Args:
            context: Girdi ImageContext nesnesi.
            target_size: Hedef maksimum boyut (örn: '400kb', '1.5mb', 500000).
            format: Çıktı formatı ('WEBP', 'JPEG').
            strip_metadata: Metaverilerin silinip silinmeyeceği bayrağı.
            min_quality: Çözünürlük düşüşünden önceki en düşük kalite eşiği.
            max_iterations: İkili arama için en fazla adım sayısı.
            
        Returns:
            Sıkıştırılmış görseli içeren yeni ImageContext.
            
        Raises:
            TargetSizeUnreachableError: Hedef boyuta ulaşılamadığında.
        """
        target_bytes = parse_size_string(target_size)
        if target_bytes <= 0:
            raise ValidationError(f"Hedef dosya boyutu pozitif olmalıdır: {target_bytes}")

        fmt = format.upper()
        if fmt not in ("WEBP", "JPEG", "JPG"):
            raise ValidationError(f"Sıkıştırma formatı WEBP veya JPEG olmalıdır: {fmt}")

        strip_meta = self.strip_metadata if strip_metadata is None else strip_metadata
        min_q = self.min_quality if min_quality is None else min_quality
        max_iter = self.max_iterations if max_iterations is None else max_iterations

        current_img = context.pil_image.copy()
        exif = None if strip_meta else context.exif_bytes
        icc = None if strip_meta else context.icc_profile

        total_binary_steps = 0
        fallback_scale_count = 0
        lowest_reached_bytes = float("inf")

        # 1. Fallback & Scaling Döngüsü
        while True:
            cur_w, cur_h = current_img.size

            # İkili Arama (Binary Search for Quality)
            low = min_q
            high = self.max_quality
            best_bytes: Optional[bytes] = None
            best_quality: Optional[int] = None

            for _ in range(max_iter):
                if low > high:
                    break
                total_binary_steps += 1
                mid = (low + high) // 2

                compressed_data = self._test_compress(
                    current_img,
                    fmt,
                    mid,
                    strip_meta,
                    exif,
                    icc,
                )
                c_size = len(compressed_data)
                if c_size < lowest_reached_bytes:
                    lowest_reached_bytes = c_size

                if c_size <= target_bytes:
                    # Hedef boyut sınırları içinde, daha yüksek kalite arayabiliriz
                    best_bytes = compressed_data
                    best_quality = mid
                    low = mid + 1
                else:
                    # Dosya çok büyük, kaliteyi düşürmemiz gerek
                    high = mid - 1

            # Eğer mevcut çözünürlükte hedef boyuta ulaşıldıysa
            if best_bytes is not None and best_quality is not None:
                result_ctx = ImageContext.from_bytes(best_bytes, format_hint=fmt)
                result_ctx.metadata["compression"] = {
                    "target_bytes": target_bytes,
                    "final_bytes": len(best_bytes),
                    "final_quality": best_quality,
                    "format": fmt,
                    "iterations": total_binary_steps,
                    "fallback_scales": fallback_scale_count,
                    "final_dimensions": result_ctx.size,
                    "original_dimensions": context.size,
                }
                return result_ctx

            # 2. Fallback Stratejisi: min_quality ile bile sığmadı, çözünürlüğü kademeli düşür
            new_w = int(cur_w * (1.0 - self.fallback_scale_step))
            new_h = int(cur_h * (1.0 - self.fallback_scale_step))

            if new_w < self.min_dimension or new_h < self.min_dimension:
                raise TargetSizeUnreachableError(
                    f"Görsel boyutu {cur_w}x{cur_h} piksele inmesine rağmen {target_bytes} byte hedefine ulaşılamadı. "
                    f"En düşük ulaşılan: {lowest_reached_bytes} byte."
                )

            current_img = current_img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
            fallback_scale_count += 1
