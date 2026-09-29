"""Merkezi Görsel Bağlamı (ImageContext).

Bellek verimliliği için PIL Image ve NumPy array arasında lazy senkronizasyon uygular.
Sıfır gereksiz disk I/O prensibiyle RAM üzerinde çalışır.
"""

from __future__ import annotations

import copy
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

from image_toolbox.core.exceptions import CorruptImageError


class ImageContext:
    """İşlem gören görseli ve ilişkili metaverileri taşıyan merkezi bağlam sınıfı."""

    def __init__(
        self,
        pil_image: Optional[Image.Image] = None,
        np_array: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None,
        exif_bytes: Optional[bytes] = None,
        icc_profile: Optional[bytes] = None,
        source_format: Optional[str] = None,
    ) -> None:
        self._pil_image: Optional[Image.Image] = pil_image
        self._np_array: Optional[np.ndarray] = np_array
        self._pil_dirty: bool = False
        self._np_dirty: bool = False

        if pil_image is None and np_array is None:
            raise ValueError("ImageContext requires at least a PIL Image or a NumPy array.")

        self.metadata: Dict[str, Any] = metadata or {}
        self.exif_bytes: Optional[bytes] = exif_bytes
        self.icc_profile: Optional[bytes] = icc_profile
        self.source_format: str = (source_format or "PNG").upper()
        self.history: List[str] = []

        # Eğer ilk oluşturmada exif veya icc PIL'de varsa ve parametre verilmemişse çıkar
        if pil_image is not None:
            if self.exif_bytes is None:
                self.exif_bytes = pil_image.info.get("exif")
            if self.icc_profile is None:
                self.icc_profile = pil_image.info.get("icc_profile")

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> ImageContext:
        """Görseli diskten okuyarak ImageContext örneği oluşturur."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Görsel dosyası bulunamadı: {file_path}")

        try:
            with open(file_path, "rb") as f:
                data = f.read()
            return cls.from_bytes(data, format_hint=file_path.suffix.lstrip(".").upper())
        except Exception as e:
            raise CorruptImageError(f"Dosya okunamadı ({file_path}): {e}") from e

    @classmethod
    def from_bytes(cls, data: bytes, format_hint: Optional[str] = None) -> ImageContext:
        """RAM'deki byte dizisinden ImageContext oluşturur."""
        try:
            bio = io.BytesIO(data)
            img = Image.open(bio)
            img.load()  # Görseli RAM'e tam olarak yükle
            source_fmt = img.format or format_hint or "PNG"
            exif_data = img.info.get("exif")
            icc = img.info.get("icc_profile")
            return cls(
                pil_image=img,
                exif_bytes=exif_data,
                icc_profile=icc,
                source_format=source_fmt,
            )
        except Exception as e:
            raise CorruptImageError(f"Byte dizisinden görsel çözümlenemedi: {e}") from e

    @classmethod
    def from_numpy(cls, array: np.ndarray, source_format: str = "PNG") -> ImageContext:
        """Doğrudan NumPy dizisinden (RGB/RGBA uint8) ImageContext oluşturur."""
        if not isinstance(array, np.ndarray):
            raise TypeError("array parametresi numpy.ndarray olmalıdır.")
        return cls(np_array=array.copy(), source_format=source_format)

    @property
    def pil_image(self) -> Image.Image:
        """Güncel PIL Image nesnesini döndürür; gerekirse NumPy dizisinden senkronize eder."""
        if self._pil_dirty and self._np_array is not None:
            arr = self._np_array
            if arr.dtype != np.uint8:
                arr = np.clip(arr, 0, 255).astype(np.uint8)

            if arr.ndim == 2:
                mode = "L"
            elif arr.ndim == 3:
                channels = arr.shape[2]
                if channels == 1:
                    mode = "L"
                    arr = arr.squeeze(axis=2)
                elif channels == 3:
                    mode = "RGB"
                elif channels == 4:
                    mode = "RGBA"
                else:
                    raise ValueError(f"Desteklenmeyen kanal sayısı: {channels}")
            else:
                raise ValueError(f"Geçersiz dizi boyutu: {arr.ndim}")

            self._pil_image = Image.fromarray(arr, mode=mode)
            self._pil_dirty = False

        if self._pil_image is None:
            raise RuntimeError("PIL Image mevcut değil.")
        return self._pil_image

    @property
    def np_array(self) -> np.ndarray:
        """Güncel NumPy dizisini (uint8) döndürür; gerekirse PIL Image'dan senkronize eder."""
        if self._np_dirty and self._pil_image is not None:
            img = self._pil_image
            if img.mode not in ("RGB", "RGBA", "L"):
                img = img.convert("RGBA" if "A" in img.mode else "RGB")
            self._np_array = np.array(img, dtype=np.uint8)
            self._np_dirty = False

        if self._np_array is None:
            if self._pil_image is not None:
                img = self._pil_image
                if img.mode not in ("RGB", "RGBA", "L"):
                    img = img.convert("RGBA" if "A" in img.mode else "RGB")
                self._np_array = np.array(img, dtype=np.uint8)
                self._np_dirty = False
            else:
                raise RuntimeError("NumPy dizisi mevcut değil.")
        return self._np_array

    def update_pil(self, image: Image.Image, operation_name: Optional[str] = None) -> None:
        """PIL görselini günceller ve NumPy önbelleğini dirty işaretler."""
        self._pil_image = image
        self._pil_dirty = False
        self._np_dirty = True
        if operation_name:
            self.history.append(operation_name)

    def update_numpy(self, array: np.ndarray, operation_name: Optional[str] = None) -> None:
        """NumPy dizisini günceller ve PIL önbelleğini dirty işaretler."""
        if array.dtype != np.uint8:
            array = np.clip(array, 0, 255).astype(np.uint8)
        self._np_array = array
        self._np_dirty = False
        self._pil_dirty = True
        if operation_name:
            self.history.append(operation_name)

    @property
    def width(self) -> int:
        """Görsel genişliği."""
        if not self._pil_dirty and self._pil_image is not None:
            return self._pil_image.width
        if self._np_array is not None:
            return int(self._np_array.shape[1])
        return self.pil_image.width

    @property
    def height(self) -> int:
        """Görsel yüksekliği."""
        if not self._pil_dirty and self._pil_image is not None:
            return self._pil_image.height
        if self._np_array is not None:
            return int(self._np_array.shape[0])
        return self.pil_image.height

    @property
    def size(self) -> Tuple[int, int]:
        """(Genişlik, Yükseklik) demeti."""
        return (self.width, self.height)

    @property
    def has_alpha(self) -> bool:
        """Alfa şeffaflık kanalının varlığını denetler."""
        if not self._pil_dirty and self._pil_image is not None:
            return self._pil_image.mode in ("RGBA", "LA", "PA")
        if self._np_array is not None:
            return self._np_array.ndim == 3 and self._np_array.shape[2] == 4
        return self.pil_image.mode in ("RGBA", "LA", "PA")

    def ensure_rgb(self) -> ImageContext:
        """Görselin RGB modunda olmasını garanti eder (Alfa varsa beyaz arka plana bindirilir)."""
        img = self.pil_image
        if img.mode == "RGB":
            return self
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img_rgba = img.convert("RGBA")
            bg = Image.new("RGB", img_rgba.size, (255, 255, 255))
            bg.paste(img_rgba, mask=img_rgba.split()[3])
            self.update_pil(bg)
        else:
            self.update_pil(img.convert("RGB"))
        return self

    def ensure_rgba(self) -> ImageContext:
        """Görselin RGBA modunda olmasını garanti eder."""
        img = self.pil_image
        if img.mode == "RGBA":
            return self
        self.update_pil(img.convert("RGBA"))
        return self

    def to_bytes(self, format: str = "PNG", **save_kwargs: Any) -> bytes:
        """Diske yazmadan doğrudan RAM üzerinde belirtilen formatta byte dizisi üretir."""
        bio = io.BytesIO()
        img = self.pil_image
        target_fmt = format.upper()
        if target_fmt == "JPG":
            target_fmt = "JPEG"

        # JPEG alfa kanalı desteklemez; RGB'ye dönüştür
        if target_fmt == "JPEG" and img.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img.convert("RGB"))
            img_to_save = bg
        else:
            img_to_save = img

        kwargs = dict(save_kwargs)
        if "quality" not in kwargs:
            comp_q = self.metadata.get("compression", {}).get("final_quality")
            save_q = self.metadata.get("save_options", {}).get("quality")
            if comp_q is not None:
                kwargs["quality"] = comp_q
            elif save_q is not None:
                kwargs["quality"] = save_q

        if "optimize" not in kwargs and target_fmt in ("JPEG", "WEBP"):
            kwargs["optimize"] = True

        if self.exif_bytes and "exif" not in kwargs and target_fmt in ("JPEG", "WEBP", "TIFF"):
            kwargs["exif"] = self.exif_bytes
        if self.icc_profile and "icc_profile" not in kwargs:
            kwargs["icc_profile"] = self.icc_profile

        img_to_save.save(bio, format=target_fmt, **kwargs)
        return bio.getvalue()

    def save(
        self,
        path: Union[str, Path],
        format: Optional[str] = None,
        **save_kwargs: Any
    ) -> None:
        """Görseli diske kaydeder."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fmt = format or output_path.suffix.lstrip(".").upper() or "PNG"
        data = self.to_bytes(format=fmt, **save_kwargs)
        output_path.write_bytes(data)

    def clone(self) -> ImageContext:
        """Mevcut bağlamın derin bir kopyasını oluşturur."""
        cloned_pil = self.pil_image.copy() if self._pil_image is not None else None
        cloned_np = self.np_array.copy() if self._np_array is not None else None
        new_ctx = ImageContext(
            pil_image=cloned_pil,
            np_array=cloned_np,
            metadata=copy.deepcopy(self.metadata),
            exif_bytes=self.exif_bytes,
            icc_profile=self.icc_profile,
            source_format=self.source_format,
        )
        new_ctx._pil_dirty = self._pil_dirty
        new_ctx._np_dirty = self._np_dirty
        new_ctx.history = list(self.history)
        return new_ctx
