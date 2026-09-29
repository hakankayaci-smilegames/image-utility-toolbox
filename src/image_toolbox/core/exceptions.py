"""Özelleştirilmiş Hata Sınıfları (Custom Exceptions)."""

from __future__ import annotations


class ToolboxError(Exception):
    """Image Utility Toolbox ana istisna taban sınıfı."""
    pass


class ValidationError(ToolboxError):
    """Operasyon veya servis parametreleri geçersiz olduğunda fırlatılır."""
    pass


class OperationError(ToolboxError):
    """Bir operasyon uygulanırken çalışma zamanında hata meydana geldiğinde fırlatılır."""
    pass


class TargetSizeUnreachableError(ToolboxError):
    """Hedef boyut sıkıştırmasında minimum çözünürlüğe inilmesine rağmen boyuta ulaşılamadığında fırlatılır."""
    pass


class CorruptImageError(ToolboxError):
    """Görsel verisi bozuk veya okunamadığında fırlatılır."""
    pass
