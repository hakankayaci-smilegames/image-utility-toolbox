"""Tüm operasyonlar için temel soyut sınıf (Command / Strategy Deseni)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from image_toolbox.core.context import ImageContext


class BaseOperation(ABC):
    """Görüntü işleme operasyonlarının soyut temel sınıfı."""

    name: str = "base_operation"
    description: str = "Base image operation"
    category: str = "general"

    def __init__(self, **params: Any) -> None:
        self.params: Dict[str, Any] = params
        self.validate()

    @abstractmethod
    def validate(self) -> None:
        """Operasyon parametrelerinin geçerliliğini denetler.
        
        Raises:
            ValidationError: Parametreler sınırların dışındaysa veya geçersiz türdeyse.
        """
        pass

    @abstractmethod
    def apply(self, context: ImageContext) -> ImageContext:
        """Operasyonu ImageContext üzerinde çalıştırır.
        
        Args:
            context: İşlenecek görsel bağlamı.
            
        Returns:
            Güncellenmiş ImageContext nesnesi.
            
        Raises:
            OperationError: İşlem sırasında çalışma zamanı hatası oluşursa.
        """
        pass

    def __repr__(self) -> str:
        param_str = ", ".join(f"{k}={v!r}" for k, v in self.params.items())
        return f"{self.__class__.__name__}({param_str})"
