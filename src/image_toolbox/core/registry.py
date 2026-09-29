"""Operasyon Kayıt ve Keşif Defteri (Operation Registry)."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Type
from image_toolbox.core.base import BaseOperation
from image_toolbox.core.exceptions import ValidationError


class OperationRegistry:
    """Sistemdeki tüm operasyonların merkezi kayıt defteri."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[BaseOperation]] = {}
        self._aliases: Dict[str, str] = {}

    def register(
        self,
        name: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> Callable[[Type[BaseOperation]], Type[BaseOperation]]:
        """Bir operasyon sınıfını deftere kaydetmek için dekoratör."""

        def decorator(cls: Type[BaseOperation]) -> Type[BaseOperation]:
            op_name = (name or cls.name).lower()
            self._registry[op_name] = cls

            if aliases:
                for alias in aliases:
                    self._aliases[alias.lower()] = op_name
            return cls

        return decorator

    def get(self, name: str) -> Type[BaseOperation]:
        """İsim veya takma ad (alias) ile operasyon sınıfını döndürür."""
        norm_name = name.lower()
        if norm_name in self._aliases:
            norm_name = self._aliases[norm_name]

        if norm_name not in self._registry:
            valid_ops = ", ".join(sorted(self._registry.keys()))
            raise ValidationError(f"Bilinmeyen operasyon: '{name}'. Geçerli operasyonlar: {valid_ops}")

        return self._registry[norm_name]

    def create(self, name: str, **params: object) -> BaseOperation:
        """Operasyon sınıfını bulup verilen parametrelerle örnekler."""
        cls = self.get(name)
        return cls(**params)

    def list_operations(self) -> Dict[str, Dict[str, str]]:
        """Kayıtlı tüm operasyonların özet listesini döndürür."""
        return {
            name: {
                "class": cls.__name__,
                "category": cls.category,
                "description": cls.description,
            }
            for name, cls in sorted(self._registry.items())
        }


# Tekil global defter
registry = OperationRegistry()
register_operation = registry.register
